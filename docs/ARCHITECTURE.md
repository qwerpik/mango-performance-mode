# Architecture

`mango-performance-mode` is a small two-process Waybar power controller for MangoWM on Ryzen + Radeon systems. Zero runtime dependencies (stdlib only).

## Components

- `src/mango_performance_modes/controller.py` (user space, runs as you):
  - `daemon` — single-instance loop (3s poll, `fcntl` daemon lock). Resets to automatic `eco` on each Mango login, then reconciles Sober state.
  - `status` — Waybar JSON output (`text`, `tooltip`, `class`: eco/balanced/max/error).
  - `set {eco|balanced|max}` — manual selection via Waybar menu actions.
  - State machine (`transition()`): Sober start → `balanced` (unless manual), Sober close → `eco` + clear manual, manual pick wins until Eco or session end, Max is never auto-selected.
  - State file: `$XDG_RUNTIME_DIR/mango-performance-mode/state.json`, written atomically (`tmp` + `os.replace`, `0600`) under an `flock`ed lock.
  - Privilege boundary: applies modes via `sudo -n /usr/local/libexec/performance-mode-apply <mode>`, then re-reads sysfs (`hardware_matches()`) before marking `applied`.
- `libexec/performance-mode-apply` (root, via sudoers allowlist):
  - Fixed purpose: exactly one of `eco|balanced|max`. Writes `scaling_governor` + `energy_performance_preference` + `boost=1` for every `policy*`, plus Radeon `power_dpm_force_performance_level` (`auto` vs `high`).
  - Verifies kernel readback; rolls back CPU + GPU to previous values on any failure.
  - GPU lookup: preferred device (`MANGO_GPU_DEVICE`, default `0x7480`) first, then first AMD GPU exposing the control file.

## Privilege & Safety

- Sudoers template renders the installing username (`install-system.sh --user`), allowlisting only the three exact helper invocations (`NOPASSWD`, no shell).
- `sudo -n` (non-interactive) so a missing rule surfaces as an error in the Waybar tooltip instead of hanging on a password prompt.
- Sysfs writes are the only privileged operations; everything else (Sober detection, Waybar output, state) runs unprivileged.

## Waybar Wiring

`custom/performance-mode` (`exec: mango-performance-mode status`, `interval: 2`) → `menu-file: performance_menu.xml` → `menu-actions: set eco|balanced|max`. Right-click opens `wlogout` (repaired layout, hibernate removed — zram-only machines). See `docs/WAYBAR.md`.
