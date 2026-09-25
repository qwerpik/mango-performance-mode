"""Mango Waybar power modes and Sober auto switching."""

import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

APP_ID = os.environ.get("MANGO_SOBER_APP_ID", "org.vinegarhq.Sober")
HELPER = os.environ.get("MANGO_PERFORMANCE_HELPER", "/usr/local/libexec/performance-mode-apply")
# Preferred GPU first, then any AMD GPU exposing the perf-level file.
# Override with MANGO_GPU_DEVICE (e.g. "0x7480") for other Radeons.
PREFERRED_GPU_DEVICE = os.environ.get("MANGO_GPU_DEVICE", "0x7480")
AMD_VENDOR = "0x1002"
MODES = {"eco", "balanced", "max"}
LABELS = {"eco": " Eco", "balanced": " Balanced", "max": " Max"}
RUNTIME = (
    Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "mango-performance-mode"
)
STATE = RUNTIME / "state.json"
LOCK = RUNTIME / "state.lock"
DAEMON_LOCK = RUNTIME / "daemon.lock"


def initial_state():
    return {"sober": False, "manual": False, "mode": "eco", "applied": None, "error": None}


def transition(state, sober, selected=None):
    """Return the desired state after a Sober observation or manual choice."""
    state = state.copy()
    was_sober = state["sober"]
    state["sober"] = sober
    if was_sober and not sober:
        state["manual"] = False
        state["mode"] = "eco"
    elif not was_sober and sober and not state["manual"]:
        state["mode"] = "balanced"

    if selected is not None:
        if selected not in MODES:
            raise ValueError("Unknown mode")
        state["mode"] = selected
        state["manual"] = selected != "eco" or sober
    return state


def prepare_runtime():
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    os.chmod(RUNTIME, 0o700)


def load_state():
    try:
        state = json.loads(STATE.read_text())
        if state.get("mode") in MODES and isinstance(state.get("manual"), bool):
            return state
    except (OSError, ValueError, TypeError):
        pass
    return initial_state()


def save_state(state):
    temp = RUNTIME / f"state.{os.getpid()}.tmp"
    temp.write_text(json.dumps(state, ensure_ascii=False))
    os.chmod(temp, 0o600)
    os.replace(temp, STATE)


def sober_running():
    result = subprocess.run(
        ["flatpak", "ps", "--columns=application"],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    return APP_ID in (line.strip() for line in result.stdout.splitlines())


def find_gpu():
    """Preferred Radeon device first, then any AMD GPU with the control file."""
    candidates = []
    for card in Path("/sys/class/drm").iterdir():
        if not card.name.startswith("card") or not card.name[4:].isdigit():
            continue
        device = card / "device"
        if not (device / "vendor").exists() or not (device / "device").exists():
            continue
        try:
            if (device / "vendor").read_text().strip() != AMD_VENDOR:
                continue
            level = device / "power_dpm_force_performance_level"
            if not level.exists():
                continue
            dev_id = (device / "device").read_text().strip()
            candidates.append((dev_id, level))
        except OSError:
            continue
    if not candidates:
        raise StopIteration("No AMD GPU with power_dpm_force_performance_level found")
    for dev_id, level in candidates:
        if dev_id == PREFERRED_GPU_DEVICE:
            return level
    return candidates[0][1]


def hardware_matches(mode):
    policies = sorted(Path("/sys/devices/system/cpu/cpufreq").glob("policy*"))
    if not policies:
        return False
    governor = "performance" if mode == "max" else "powersave"
    epp = {"eco": "balance_power", "balanced": "balance_performance", "max": "performance"}[mode]
    try:
        if any(
            (p / "scaling_governor").read_text().strip() != governor
            or (p / "energy_performance_preference").read_text().strip() != epp
            or (p / "boost").read_text().strip() != "1"
            for p in policies
        ):
            return False
        gpu = find_gpu()
        return gpu.read_text().strip() == ("high" if mode == "max" else "auto")
    except (OSError, StopIteration):
        return False


def reconcile(selected=None):
    prepare_runtime()
    with LOCK.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state()
        detection_error = None
        try:
            sober = sober_running()
        except (OSError, subprocess.SubprocessError) as exc:
            sober = state["sober"]
            detection_error = f"Sober detection failed: {exc}"
        state = transition(state, sober, selected)
        if state["mode"] != state.get("applied") or not hardware_matches(state["mode"]):
            try:
                result = subprocess.run(
                    ["sudo", "-n", HELPER, state["mode"]],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                if result.returncode:
                    err = (result.stderr or result.stdout).strip()
                    state["error"] = err or "Mode change failed"
                elif hardware_matches(state["mode"]):
                    state["applied"] = state["mode"]
                    state["error"] = None
                else:
                    state["error"] = "Hardware did not accept the selected mode"
            except (OSError, subprocess.SubprocessError) as exc:
                state["error"] = f"Mode change failed: {exc}"
        else:
            state["error"] = None
        if detection_error:
            if state["error"]:
                state["error"] = f"{state['error']}; {detection_error}"
            else:
                state["error"] = detection_error
        save_state(state)


def status():
    state = load_state()
    mode = state["mode"]
    source = "Manual" if state["manual"] else "Automatic"
    tooltip = f"{source}: {mode.title()}"
    if state["sober"]:
        tooltip += "\nSober is running"
    if state.get("error"):
        tooltip += f"\nError: {state['error']}"
    elif not hardware_matches(mode):
        tooltip += "\nHardware settings are not active"
    print(
        json.dumps(
            {
                "text": LABELS[mode],
                "tooltip": tooltip,
                "class": "error" if state.get("error") or not hardware_matches(mode) else mode,
            },
            ensure_ascii=False,
        )
    )


def daemon():
    prepare_runtime()
    with DAEMON_LOCK.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        # A new Mango login starts in automatic mode, regardless of a stale runtime file.
        with LOCK.open("a+") as state_lock:
            fcntl.flock(state_lock, fcntl.LOCK_EX)
            save_state(initial_state())
        while True:
            try:
                reconcile()
            except Exception as exc:
                print(f"Performance mode controller: {exc}", file=sys.stderr, flush=True)
            time.sleep(3)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) == 1 and args[0] == "status":
        status()
    elif len(args) == 1 and args[0] == "daemon":
        daemon()
    elif len(args) == 2 and args[0] == "set" and args[1] in MODES:
        reconcile(args[1])
    else:
        print("Usage: mango-performance-mode daemon|status|set {eco|balanced|max}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
