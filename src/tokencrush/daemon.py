"""Background proxy daemon management."""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

DAEMON_PORT = 8765
PID_FILE = Path.home() / ".tokencrush" / "daemon.pid"
LOG_FILE = Path.home() / ".tokencrush" / "daemon.log"


def get_pid() -> int | None:
    """Get running daemon PID."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)
    return None


def is_running() -> bool:
    """Check if daemon is running."""
    return get_pid() is not None


def start() -> bool:
    """Start the proxy daemon."""
    if is_running():
        return True

    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "tokencrush.proxy:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(DAEMON_PORT),
        "--log-level",
        "warning",
    ]

    with open(LOG_FILE, "a") as log:
        proc = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    PID_FILE.write_text(str(proc.pid))
    time.sleep(0.5)
    return is_running()


def stop() -> bool:
    """Stop the proxy daemon."""
    pid = get_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            PID_FILE.unlink(missing_ok=True)
            return True
        except OSError:
            pass
    return False


def status() -> dict:
    """Get daemon status."""
    pid = get_pid()
    return {
        "running": pid is not None,
        "pid": pid,
        "port": DAEMON_PORT,
        "url": f"http://127.0.0.1:{DAEMON_PORT}/v1",
    }
