<div align="center">

# Mango Performance Mode

**Eco / Balanced / Max for Ryzen + Radeon on MangoWM — right in your Waybar.**

<br />

[![Star this repo](https://img.shields.io/github/stars/qwerpik/mango-performance-mode?style=for-the-badge&logo=github&label=%E2%AD%90%20Star%20this%20repo&color=yellow)](https://github.com/qwerpik/mango-performance-mode/stargazers)

<br />

[![CI Status](https://img.shields.io/github/actions/workflow/status/qwerpik/mango-performance-mode/test.yml?branch=main&label=CI&style=for-the-badge&logo=githubactions&logoColor=white&color=a6e3a1)](https://github.com/qwerpik/mango-performance-mode/actions/workflows/test.yml)
&nbsp;
[![Release](https://img.shields.io/github/v/release/qwerpik/mango-performance-mode?style=for-the-badge&logo=github&color=89b4fa)](https://github.com/qwerpik/mango-performance-mode/releases)
&nbsp;
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-89b4fa?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
&nbsp;
[![Dependencies: 0](https://img.shields.io/badge/Dependencies-0-a6e3a1?style=for-the-badge)](pyproject.toml)
&nbsp;
[![License: MIT](https://img.shields.io/badge/License-MIT-f38ba8?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
&nbsp;
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)

---

Zero-dependency Waybar power controller • 3 locked-down modes • Sober auto-switching • Repaired wlogout menu.

[Quickstart](#quickstart) • [How It Works](#how-it-works) • [Features](#features) • [Installation](#installation) • [Waybar](docs/WAYBAR.md) • [Architecture](docs/ARCHITECTURE.md) • [Power Notes](docs/POWER-AUDIT.md) • [Original Report](docs/REPORT.md) • [Contributing](#contributing)

</div>

<br />

> [!TIP]
> **Try in 60 seconds**
> ```bash
> git clone https://github.com/qwerpik/mango-performance-mode.git
> cd mango-performance-mode
> ./install.sh && sudo ./install-system.sh
> mango-performance-mode status
> ```

<table>
<tr>
<td width="33%" valign="top">

**⚡ Three honest modes**
Eco, Balanced, Max — governor + EPP + boost + Radeon perf level, verified by readback.

</td>
<td width="33%" valign="top">

**🔒 Least privilege**
Root helper does one thing (3 exact sudo args), verifies, and rolls back on failure.

</td>
<td width="33%" valign="top">

**🎯 Feels native**
Left-click menu in the bar, right-click power menu, auto-Balanced while Sober runs.

</td>
</tr>
</table>

## How it works

Left-click the far-right module → pick **Eco**, **Balanced**, or **Max**. The daemon starts in Eco every Mango login, switches to Balanced while the Sober Flatpak runs, and returns to Eco when it closes. A manual pick wins until you choose Eco again. Max is never auto-selected.

| Mode | Ryzen CPU | Radeon GPU |
| :--- | :--- | :--- |
| Eco | `powersave`, EPP `balance_power`, boost on | Dynamic `auto` |
| Balanced | `powersave`, EPP `balance_performance`, boost on | Dynamic `auto` |
| Max Performance | `performance`, EPP `performance`, boost on | Forced `high` |

No clock caps or undervolts. Verified on Ryzen 5 5600X + RX 7600 XT (`0x7480`); other Radeons fall back to the first AMD GPU exposing `power_dpm_force_performance_level` (override with `MANGO_GPU_DEVICE`).

> [!NOTE]
> Short Vulkan benchmark on the reference machine: **15,517 Eco / 15,725 Balanced / 15,674 Max** — noise-level difference for that workload. Max raised sampled GPU power (37 W); game FPS and wall power were not measured. Pick modes for responsiveness and heat, not this one number.

> [!CAUTION]
> **😱 Without it**
> The machine sat in `powersave` at ~558 MHz, EEE/USB/audio power-saving added jitter, and the old power menu was dead (`wlogout` missing).

## ✨ Features

| | Capability | What you get |
| :--- | :--- | :--- |
| ⚡ | **Three verified modes** | Governor + EPP + boost + GPU level, with kernel readback before reporting success |
| 🔌 | **Waybar-native UX** | `custom/performance-mode` module, click menu, right-click `wlogout` power menu |
| 🎮 | **Sober auto-switch** | Balanced while Sober runs, Eco on close, manual choice always wins |
| 🛡️ | **Race-free & atomic** | `fcntl.flock` locks, atomic `state.json` writes, single-instance daemon |
| 🔒 | **Restricted helper** | `NOPASSWD` for exactly 3 commands, non-interactive `sudo -n`, rollback on mismatch |
| 🖥️ | **Portable install** | `PREFIX`/`XDG`-aware `install.sh` with backups + `uninstall.sh`; distro-aware system install |

## Installation

<a id="installation"></a>
<a id="quickstart"></a>

Requires Linux with `amd-pstate`/`cpufreq`, an AMD GPU (best on RX 7600-class), Waybar, `flatpak` (only for Sober detection), and `sudo`.

```bash
git clone https://github.com/qwerpik/mango-performance-mode.git
cd mango-performance-mode
./install.sh            # user files: ~/.local/bin + ~/.config/mango
sudo ./install-system.sh  # helper + sudoers + wlogout
```

Then wire the module and CSS into Waybar — see [docs/WAYBAR.md](docs/WAYBAR.md) (2-minute merge). Start the daemon at Mango login:

```bash
mango-performance-mode daemon >>/tmp/mango-performance-mode.log 2>&1 &
```

Uninstall: `./uninstall.sh [--purge]` and `sudo ./uninstall-system.sh`.

## Status & verification

```bash
mango-performance-mode status          # Waybar JSON for the current mode
PYTHONPATH=src python3 -m unittest discover -s tests -v
make check                             # ruff + mypy + tests
```

All three modes were verified by kernel readback on the reference machine; Sober open/close and manual-Max priority were exercised end to end.

## Contributing

<a id="contributing"></a>

See [CONTRIBUTING.md](CONTRIBUTING.md) — fork, branch, `make check`, PR. Stdlib only, locks + atomic writes, sudoers stays minimal.

## Origin

Built from a full system-optimization session (disk cleanup, Steam/BBR tuning, power audit). The unedited session log lives in [docs/REPORT.md](docs/REPORT.md); the reusable tuning notes in [docs/POWER-AUDIT.md](docs/POWER-AUDIT.md).
