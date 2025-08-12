import platform
import subprocess
import sys
import time
from typing import Optional


def run_shell_command(command: str, timeout: Optional[float] = None) -> int:
    try:
        print(f"[CMD] {command}")
        res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if res.stdout:
            try:
                print(res.stdout.decode(errors="ignore"))
            except Exception:
                pass
        if res.returncode != 0 and res.stderr:
            try:
                print(res.stderr.decode(errors="ignore"), file=sys.stderr)
            except Exception:
                pass
        return res.returncode
    except subprocess.TimeoutExpired:
        print(f"[ERR] Command timed out: {command}", file=sys.stderr)
        return 124


def macos_vpn_status(service_name: str) -> str:
    try:
        res = subprocess.run(["scutil", "--nc", "status", service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            return "Unknown"
        out = (res.stdout or b"").decode(errors="ignore").strip()
        first = out.splitlines()[0] if out else ""
        return (first.split() or ["Unknown"])[0]
    except Exception:
        return "Unknown"


def macos_vpn_connect(service_name: str, timeout_seconds: float = 60.0) -> bool:
    if platform.system() != "Darwin":
        print("[WARN] --vpn-service is only supported on macOS (Darwin).", file=sys.stderr)
        return False
    print(f"[VPN] Connecting '{service_name}'…")
    subprocess.run(["scutil", "--nc", "start", service_name])
    deadline = time.time() + max(1.0, float(timeout_seconds))
    last_status = ""
    while time.time() < deadline:
        status = macos_vpn_status(service_name)
        if status != last_status and status:
            print(f"[VPN] Status: {status}")
            last_status = status
        if status.lower().startswith("connected"):
            print("[VPN] Connected.")
            return True
        time.sleep(1.0)
    print(f"[ERR] VPN did not reach Connected within {timeout_seconds:.0f}s.", file=sys.stderr)
    return False


def macos_vpn_disconnect(service_name: str, timeout_seconds: float = 15.0) -> None:
    if platform.system() != "Darwin":
        return
    print(f"[VPN] Disconnecting '{service_name}'…")
    subprocess.run(["scutil", "--nc", "stop", service_name])
    deadline = time.time() + max(1.0, float(timeout_seconds))
    while time.time() < deadline:
        status = macos_vpn_status(service_name)
        if status.lower().startswith("disconnected") or status == "Unknown":
            print("[VPN] Disconnected.")
            return
        time.sleep(0.5)


