"""
Portable wall-time autosave for HPC Jupyter kernels.

Saves the current Python namespace to a dill file periodically and/or before
a Slurm job runs out of wall time, so the session can be restored in a new
kernel. Filename is keyed by notebook name (if provided) so it's easy to
find when restoring — no need to remember the job ID.

dill is OPTIONAL — if not installed, save/load are no-ops with a warning.

Usage (paste at top of any compute-kernel session):
    import sys, os; sys.path.insert(0, os.path.expanduser("~/bin"))
    import walltime_autosave
    SESSION_FILE = walltime_autosave.start(notebook="my_analysis")
    # periodic saves every 30 min + emergency save when <10 min remain:
    SESSION_FILE = walltime_autosave.start(notebook="my_analysis", save_interval=30)

To restore in a new kernel:
    import sys, os; sys.path.insert(0, os.path.expanduser("~/bin"))
    import walltime_autosave
    walltime_autosave.load(notebook="my_analysis")
"""

import os
import subprocess
import threading
import time
import types

try:
    import dill as _dill
    _DILL_AVAILABLE = True
except ImportError:
    _dill = None
    _DILL_AVAILABLE = False


def _default_session_file(notebook=None):
    user = os.environ.get("USER", "user")
    scratch = os.environ.get("SCRATCH")
    base = os.path.join(scratch, user) if (scratch and os.path.isdir(scratch)) else "/tmp"
    if notebook:
        name = f"autosave_{notebook}.pkl"
    else:
        job_id = os.environ.get("SLURM_JOB_ID", "local")
        name = f"kernel_{job_id}_autosave.pkl"
    return os.path.join(base, name)


def get_slurm_remaining_seconds():
    """Return remaining Slurm wall time in seconds, or None if not in a job."""
    job_id = os.environ.get("SLURM_JOB_ID")
    if not job_id:
        return None
    try:
        result = subprocess.run(
            ["squeue", "--job", job_id, "--noheader", "--format=%L"],
            capture_output=True, text=True, timeout=10,
        )
        time_str = result.stdout.strip()
        if not time_str or time_str in ("INVALID", ""):
            return None
        parts = [int(p) for p in time_str.replace("-", ":").split(":")]
        if len(parts) == 4:    # D-HH:MM:SS
            return parts[0] * 86400 + parts[1] * 3600 + parts[2] * 60 + parts[3]
        if len(parts) == 3:    # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:    # MM:SS
            return parts[0] * 60 + parts[1]
    except Exception as e:
        print(f"[walltime_autosave] squeue error: {e}")
    return None


_SKIP = {"In", "Out", "exit", "quit", "get_ipython", "open"}
_SKIP_PREFIXES = ("_",)


def save(notebook=None, session_file=None):
    """
    Serialize the current namespace to a dill file.
    Skips modules, unserializable objects, and IPython internals.
    Overwrites the file if it exists — always the most recent snapshot.

    Parameters
    ----------
    notebook     : notebook name used to derive filename (e.g. "my_analysis")
    session_file : explicit path; overrides notebook-derived path if given

    Returns the path written to, or None if dill is unavailable.
    """
    if not _DILL_AVAILABLE:
        print("[walltime_autosave] WARNING: dill not installed — cannot save. Run: pip install dill")
        return None

    session_file = session_file or _default_session_file(notebook)

    import __main__
    saved, skipped = {}, []
    for k, v in vars(__main__).items():
        if k in _SKIP or any(k.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if isinstance(v, types.ModuleType):
            continue
        try:
            _dill.dumps(v)
            saved[k] = v
        except Exception:
            skipped.append(k)

    dirpath = os.path.dirname(session_file)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(session_file, "wb") as f:
        _dill.dump(saved, f)

    size_mb = os.path.getsize(session_file) / 1e6
    print(f"[walltime_autosave] Saved {len(saved)} objects → {session_file} ({size_mb:.1f} MB)")
    if skipped:
        print(f"[walltime_autosave] Skipped (not serializable): {skipped}")
    return session_file


def load(notebook=None, session_file=None):
    """
    Restore variables saved by save() into the caller's __main__ namespace.

    Parameters
    ----------
    notebook     : notebook name used to derive filename (e.g. "my_analysis")
    session_file : explicit path; overrides notebook-derived path if given

    Returns the list of restored variable names, or None if dill is unavailable.
    """
    if not _DILL_AVAILABLE:
        print("[walltime_autosave] WARNING: dill not installed — cannot load. Run: pip install dill")
        return None

    session_file = session_file or _default_session_file(notebook)

    if not os.path.exists(session_file):
        print(f"[walltime_autosave] No session file at {session_file}")
        return None

    import __main__
    with open(session_file, "rb") as f:
        data = _dill.load(f)
    vars(__main__).update(data)
    print(f"[walltime_autosave] Loaded {len(data)} objects from {session_file}: {list(data.keys())}")
    return list(data.keys())


def start(notebook=None, session_file=None, warn_minutes=10, check_interval=60, save_interval=30):
    """
    Start a background monitor thread that checkpoints the session automatically.

    Saves when:
      - Every save_interval minutes (if save_interval is set)
      - Slurm remaining time drops below warn_minutes (emergency save)

    Each save overwrites the same file — always the most recent snapshot.

    Parameters
    ----------
    notebook      : notebook name for the session file (e.g. "my_analysis")
    session_file  : explicit path; overrides notebook-derived path if given
    warn_minutes  : save when this many minutes remain (default 10)
    check_interval: seconds between wall-time checks (default 60)
    save_interval : save every N minutes regardless of wall time (default 30)

    Returns the session file path.
    """
    session_file = session_file or _default_session_file(notebook)

    if not _DILL_AVAILABLE:
        print("[walltime_autosave] WARNING: dill not installed — autosave disabled. Run: pip install dill")
        print(f"[walltime_autosave] Session file would be: {session_file}")
        return session_file

    in_slurm = bool(os.environ.get("SLURM_JOB_ID"))
    if not in_slurm and not save_interval:
        print(f"[walltime_autosave] Not in a Slurm job and save_interval=None — monitor inactive.")
        print(f"[walltime_autosave] Call walltime_autosave.save(notebook={notebook!r}) manually to checkpoint.")
        print(f"[walltime_autosave] Session file: {session_file}")
        return session_file

    emergency_saved = [False]
    last_periodic = [time.time()]
    save_interval_sec = save_interval * 60 if save_interval else None

    def _monitor():
        while True:
            now = time.time()

            if save_interval_sec and (now - last_periodic[0]) >= save_interval_sec:
                print(f"\n[walltime_autosave] Periodic checkpoint...")
                save(session_file=session_file)
                last_periodic[0] = now

            if not emergency_saved[0]:
                remaining = get_slurm_remaining_seconds()
                if remaining is not None and remaining < warn_minutes * 60:
                    print(f"\n[walltime_autosave] WARNING: {remaining/60:.1f} min remaining — emergency save...")
                    save(session_file=session_file)
                    emergency_saved[0] = True
                    print(f"[walltime_autosave] Restore with: walltime_autosave.load(notebook={notebook!r})")

            time.sleep(check_interval)

    t = threading.Thread(target=_monitor, daemon=True, name="walltime-autosave")
    t.start()

    parts = []
    if save_interval:
        parts.append(f"every {save_interval} min")
    if in_slurm:
        parts.append(f"emergency save when <{warn_minutes} min remain")
    print(f"[walltime_autosave] Monitor started ({', '.join(parts)}).")
    print(f"[walltime_autosave] Session file: {session_file}")
    return session_file
