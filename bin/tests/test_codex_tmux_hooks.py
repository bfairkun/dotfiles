import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('hook', ROOT/'agents/.codex/hooks/tmux-state.py')
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class Hooks(unittest.TestCase):
    def test_lifecycle(self):
        for event, action in [('Stop','done'), ('PermissionRequest','attn'),
                              ('UserPromptSubmit','clear'), ('Interrupt','clear'),
                              ('PostToolUse','clear'), ('SessionEnd','clear'),
                              ('SubagentStop',None)]:
            self.assertEqual(hook.action_for({'hook_event_name':event}), action)
        for tool in ('request_user_input','functions.request_user_input_async'):
            self.assertEqual(hook.action_for({'hook_event_name':'PreToolUse','tool_name':tool}), 'attn')

    def test_install_preserves_other_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'hooks.json'
            original = {'hooks':{'Stop':[{'hooks':[{'type':'command','command':'existing-hook'}]}]}}
            path.write_text(json.dumps(original))
            env = dict(os.environ, CODEX_HOME=temp)
            script = str(ROOT/'bin/bin/install-codex-tmux-hooks')
            subprocess.run([script], env=env, check=True, capture_output=True)
            first = path.read_text()
            subprocess.run([script], env=env, check=True, capture_output=True)
            self.assertEqual(path.read_text(), first)
            self.assertEqual(json.loads(first)['hooks']['Stop'][0], original['hooks']['Stop'][0])

    def test_markers_on_isolated_tmux_server(self):
        import shutil
        tmux = shutil.which('tmux')
        if not tmux:
            self.skipTest('tmux unavailable')
        with tempfile.TemporaryDirectory() as temp:
            socket = str(Path(temp)/'socket')
            def tm(*args):
                return subprocess.check_output([tmux, '-S', socket, *args], text=True).strip()
            agent = Path(temp)/'codex'
            agent.symlink_to(shutil.which('sleep'))
            command = str(agent)+' 60'
            try:
                pane = tm('-f','/dev/null','new-session','-d','-s','test','-P','-F','#{pane_id}',command)
                other = tm('split-window','-d','-t',pane,'-P','-F','#{pane_id}',command)
                wrapper = Path(temp)/'tmux'
                wrapper.write_text('#!/bin/sh\nexec '+tmux+' -S '+socket+' "$@"\n')
                wrapper.chmod(0o755)
                env = dict(os.environ, PATH=temp+os.pathsep+os.environ['PATH'])
                def run(action, target):
                    subprocess.run([str(ROOT/'bin/bin/tmux-agent-state'),action],
                                   env=dict(env, TMUX_PANE=target), input='', text=True,
                                   capture_output=True, timeout=5, check=True)
                run('done', pane)
                run('attn', other)
                self.assertEqual(tm('show-options','-wqv','-t',pane,'@agent_win_state'), 'attn')
                self.assertEqual(tm('show-options','-wqv','-t',pane,'@agent_attn_count'), '1')
                self.assertEqual(tm('show-options','-wqv','-t',pane,'@agent_done_count'), '1')
                run('clear', other)
                self.assertEqual(tm('show-options','-wqv','-t',pane,'@agent_win_state'), 'done')
                run('done', other)
                subprocess.run([str(ROOT/'bin/bin/tmux-agent-state'),'clear-done',other], env=env, check=True, capture_output=True)
                self.assertEqual(tm('show-options','-pqv','-t',pane,'@agent_state'), 'done')
                self.assertEqual(tm('show-options','-pqv','-t',other,'@agent_state'), '')
                self.assertEqual(tm('show-options','-wqv','-t',pane,'@agent_done_count'), '1')
                run('attn', other)
                run('jump', pane)
                self.assertEqual(tm('display-message','-p','-t',other,'#{pane_active}'), '1')
                self.assertEqual(tm('show-options','-pqv','-t',other,'@agent_state'), 'attn')
                run('clear', other)
                # Validate rendering and hook names on the installed tmux version.
                config = ROOT/'tmux/.tmux.conf'
                formats = [line for line in config.read_text().splitlines()
                           if line.startswith('set -g window-status-format ')]
                fragment = Path(temp)/'markers.conf'
                fragment.write_text('\n'.join(formats)+'\n')
                tm('source-file',str(fragment))
                rendered = tm('display-message','-p','-t',pane,
                              tm('show-options','-gv','window-status-format'))
                self.assertIn('✔1', rendered)
                tm('set-hook','-g','window-pane-changed','display-message test-hook')
                run('clear', pane)
                self.assertEqual(tm('show-options','-wqv','-t',pane,'@agent_win_state'), '')
            finally:
                subprocess.run([tmux,'-S',socket,'kill-server'], capture_output=True)
