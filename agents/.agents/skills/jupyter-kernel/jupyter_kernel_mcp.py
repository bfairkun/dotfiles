#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["jupyter_client"]
# ///
"""Persistent Jupyter kernel MCP server (JSON-RPC 2.0 over stdio).

Usage:
  python3 jupyter_kernel_mcp.py                        # start a fresh default kernel
  python3 jupyter_kernel_mcp.py --existing <cf.json>   # attach to a running kernel
  python3 jupyter_kernel_mcp.py --latest               # attach to newest kernel, or start fresh
  python3 jupyter_kernel_mcp.py --timeout 600          # iopub poll timeout in seconds (default: 300)
"""

import atexit
import glob
import json
import os
import sys
import traceback
from datetime import datetime
from jupyter_client import KernelManager, BlockingKernelClient
from jupyter_client.connect import jupyter_runtime_dir

MAX_OUTPUT = 8000
IOPUB_TIMEOUT = 300  # seconds; overridden by --timeout arg

km = None   # None when attached to an existing kernel
kc = None
_pending_start = None  # ("fresh"|"existing"|"latest", arg_or_None) — resolved on first tool call


def _kernel_search_dirs() -> list:
    dirs = [jupyter_runtime_dir()]
    xdg = os.path.expanduser("~/.local/share/jupyter/runtime")
    if xdg not in dirs:
        dirs.append(xdg)
    run_user = f"/run/user/{os.getuid()}/jupyter/runtime"
    if os.path.isdir(run_user) and run_user not in dirs:
        dirs.append(run_user)
    return dirs


def find_latest_kernel() -> "str | None":
    files = []
    for d in _kernel_search_dirs():
        files.extend(glob.glob(os.path.join(d, "kernel-*.json")))
    return max(files, key=os.path.getmtime) if files else None


def _stop_current_client():
    global km, kc
    if kc is not None:
        try:
            kc.stop_channels()
        except Exception:
            pass
        kc = None
    if km is not None:
        try:
            km.shutdown_kernel(now=True)
        except Exception:
            pass
        km = None


def _shutdown_owned_kernel():
    """atexit handler: shut down any kernel we own."""
    global km, kc
    if kc is not None:
        try:
            kc.stop_channels()
        except Exception:
            pass
    if km is not None:
        try:
            km.shutdown_kernel(now=True)
        except Exception:
            pass


atexit.register(_shutdown_owned_kernel)


def start_kernel(kernel_name: str = ""):
    global km, kc
    _stop_current_client()
    km = KernelManager(kernel_name=kernel_name) if kernel_name else KernelManager()
    km.start_kernel()
    kc = km.blocking_client()
    kc.start_channels()
    kc.wait_for_ready(timeout=30)


def attach_kernel(connection_file: str):
    global km, kc
    _stop_current_client()
    km = None  # externally managed
    kc = BlockingKernelClient()
    kc.load_connection_file(connection_file)
    kc.start_channels()
    kc.wait_for_ready(timeout=30)


def _ensure_kernel():
    """Lazily start or attach the kernel on first use."""
    global _pending_start
    if kc is not None:
        return
    mode, arg = _pending_start if _pending_start is not None else ("fresh", None)
    _pending_start = None
    if mode == "existing":
        attach_kernel(arg)
    elif mode == "latest":
        cf = find_latest_kernel()
        if cf:
            print(f"[jupyter-kernel] attaching to existing kernel: {cf}", file=sys.stderr)
            attach_kernel(cf)
        else:
            print("[jupyter-kernel] no existing kernel found, starting fresh py_general kernel", file=sys.stderr)
            start_kernel()
    else:
        start_kernel()


def run_python(code: str) -> str:
    _ensure_kernel()
    msg_id = kc.execute(code)
    parts = []
    # TODO: better fix — catch TimeoutError and `continue` instead of breaking, so
    # long-running cells (MCMC, large pickle saves) aren't abandoned mid-execution.
    # Only break on non-timeout exceptions (kernel crash, connection error).
    # Risk: if the kernel job is killed by SLURM, get_iopub_msg may hang; add a
    # wall-clock deadline or liveness check as a safety valve.
    while True:
        try:
            msg = kc.get_iopub_msg(timeout=IOPUB_TIMEOUT)
        except Exception as e:
            parts.append(f"[timeout waiting for kernel: {e}]")
            break
        if msg["parent_header"].get("msg_id") != msg_id:
            continue
        msg_type = msg["msg_type"]
        content = msg["content"]
        if msg_type == "stream":
            parts.append(content["text"])
        elif msg_type == "execute_result":
            parts.append(content["data"].get("text/plain", ""))
        elif msg_type == "error":
            parts.append("\n".join(content["traceback"]))
        elif msg_type == "display_data":
            text = content["data"].get("text/plain")
            parts.append(text if text else "[rich output — no text repr]")
        elif msg_type == "status" and content.get("execution_state") == "idle":
            break
    result = "".join(parts)
    if len(result) > MAX_OUTPUT:
        result = result[:MAX_OUTPUT] + f"\n... [truncated — {len(result)} total chars]"
    return result or "[no output]"


def tool_restart_kernel() -> str:
    _ensure_kernel()
    if km is None:
        return "Cannot restart: attached to an external kernel (not managed by this server)."
    km.restart_kernel(now=True)
    global kc
    kc = km.blocking_client()
    kc.start_channels()
    kc.wait_for_ready(timeout=30)
    return "Kernel restarted."


def _find_all_kernel_files() -> list[str]:
    """Find all kernel connection files, including MCP-started ones in /tmp/."""
    files = []
    for d in _kernel_search_dirs():
        files.extend(glob.glob(os.path.join(d, "kernel-*.json")))
    # MCP-started kernels land in /tmp/tmp*.json
    if km is not None and km.connection_file and os.path.exists(km.connection_file):
        if km.connection_file not in files:
            files.append(km.connection_file)
    return files


def tool_list_kernels() -> str:
    files = _find_all_kernel_files()
    if not files:
        return "No running kernels found."
    files.sort(key=os.path.getmtime, reverse=True)
    lines = []
    for f in files:
        mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(f) as fp:
                data = json.load(fp)
            kernel_name = data.get("kernel_name", "unknown")
        except Exception:
            kernel_name = "unknown"
        lines.append(f"{f}  [{kernel_name}]  last modified {mtime}")
    return "\n".join(lines)


def tool_connect_to_kernel(connection_file: str = "") -> str:
    cf = connection_file.strip() or find_latest_kernel()
    if not cf:
        return "No kernel connection files found. Start a kernel first."
    if not os.path.exists(cf):
        return f"Connection file not found: {cf}"
    attach_kernel(cf)
    return f"Connected to kernel: {cf}"


def tool_start_kernel(kernel_name: str = "") -> str:
    start_kernel(kernel_name)
    cf = km.connection_file
    label = kernel_name or km.kernel_name
    return f"Started new {label} kernel.\nConnection file: {cf}"


TOOLS = [
    {
        "name": "run_python",
        "description": "Execute Python code in a persistent kernel and return stdout/stderr/result as text.",
        "inputSchema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code to execute"}},
            "required": ["code"],
        },
    },
    {
        "name": "restart_kernel",
        "description": "Restart the Jupyter kernel, clearing all variables. No-op when attached to an external kernel.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_kernels",
        "description": "List all running Jupyter kernel connection files, sorted newest first.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "connect_to_kernel",
        "description": (
            "Attach to a running Jupyter kernel by connection file path. "
            "If connection_file is omitted, attaches to the most recently modified kernel "
            "(useful for connecting to the kernel VS Code is currently using)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "connection_file": {
                    "type": "string",
                    "description": "Path to kernel-*.json connection file. Leave empty to attach to newest.",
                }
            },
        },
    },
    {
        "name": "start_kernel",
        "description": "Start a new Jupyter kernel and attach to it. Returns the connection file path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kernel_name": {
                    "type": "string",
                    "description": "Conda env / kernel name to start (default: system default kernel).",
                }
            },
        },
    },
]


def handle(request: dict) -> dict | None:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jupyter-kernel", "version": "1.1.0"},
            },
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            if tool_name == "run_python":
                text = run_python(args["code"])
            elif tool_name == "restart_kernel":
                text = tool_restart_kernel()
            elif tool_name == "list_kernels":
                text = tool_list_kernels()
            elif tool_name == "connect_to_kernel":
                text = tool_connect_to_kernel(args.get("connection_file", ""))
            elif tool_name == "start_kernel":
                text = tool_start_kernel(args.get("kernel_name", "py_general"))
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception:
            tb = traceback.format_exc()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"[server error]\n{tb}"}],
                    "isError": True,
                },
            }
    else:
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return None


def main():
    global _pending_start, IOPUB_TIMEOUT
    args = sys.argv[1:]
    if "--timeout" in args:
        IOPUB_TIMEOUT = int(args[args.index("--timeout") + 1])
    if "--existing" in args:
        _pending_start = ("existing", args[args.index("--existing") + 1])
    elif "--latest" in args:
        _pending_start = ("latest", None)
    else:
        _pending_start = ("fresh", None)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
