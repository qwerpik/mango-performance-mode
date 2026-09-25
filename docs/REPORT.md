# Complete System Optimization & Cleanup Report

**Date**: 2026-09-25  
**System**: Artix Linux (x86_64) | AMD Ryzen 5 5600X (6C/12T) | AMD Radeon RX 7600 (NAVI33) | 32 GB RAM  
**Network**: Gigabit Ethernet (`eth0` Realtek RTL8168/8111) | Play / CommScope DOCSIS 3.0/3.1 (300 Mbps Cable)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Task 1: Disk Space Audit & Cleanup (100 GB Target)](#task-1-disk-space-audit--cleanup-100-gb-target)
3. [Task 2: Steam Download & Network Throughput Optimization](#task-2-steam-download--network-throughput-optimization)
4. [Task 3: Full System Power Management Audit](#task-3-full-system-power-management-audit)
5. [Task 4: Waybar Power Modes](#task-4-waybar-power-modes)
6. [Summary of Applied System Settings & Recommendations](#summary-of-applied-system-settings--recommendations)

---

## Executive Summary

During this pair-programming session, two primary operational goals and one hardware audit were executed:

1. **Disk Cleanup (100 GB Free Space Goal)**: Reclaimed **~81+ GB** of physical storage on the root encrypted partition (`/dev/mapper/cryptroot`), increasing free space from **24 GB (98% full) to 104 GB (89% full)** without touching active projects or personal documents.
2. **Steam Speed Optimization (300 Mbps Cable Goal)**: Diagnosed why Steam was hovering at ~95 Mbps during a 57 GB Counter-Strike 2 download. Resolved CPU throttling, TCP window collapsing, and ext4 metadata latency in-flight. Following a region adjustment to Germany, download speed surged to **260.25 Mbps (31.02 MB/s)**, achieving the target without losing download progress.
3. **Hardware Power State Audit**: Conducted an exhaustive audit of all system subsystems (CPU, GPU, Network, SATA, PCIe, USB, Audio) to determine which components were throttled by power-saving modes.

---

## Task 1: Disk Space Audit & Cleanup (100 GB Target)

### 1. Initial State
- **Root Partition (`/dev/mapper/cryptroot`)**: 937 GB Total | 867 GB Used | **24 GB Free (98% Full)**.
- **Strict Rule**: Read-only diagnostics first; nothing deleted until reviewed.

### 2. High-Impact Culprits Identified
- **Package & Build Caches (`~/.cache`)**:
  - `uv` Python wheel/archive cache: **51.5 GB** (`~/.cache/uv/archive-v0`)
  - `yay` AUR compilation build artifacts: **6.8 GB** (`~/.cache/yay`)
  - `pip` cache: **3.1 GB** (`~/.cache/pip`)
  - `tracker3` GNOME index cache: **2.0 GB** (`~/.cache/tracker3`)
  - Hugging Face incomplete/detached downloads: **5.8 GB**
- **Downloads Folder (`~/Pobrane`)**:
  - Google Takeout zip archive (`takeout-...-001.zip`): **39 GB** (an exact duplicate of the already extracted directory right beside it).
  - Forza Horizon 6 DODI repack installer: **~80 GB** (partially pre-allocated).
  - Redundant game zip files with extracted folders present: `Slime-Rancher-2` (3.2 GB), `Poly-Bridge-3` (1.2 GB), `Deltarune` (844 MB), `larp` (718 MB).
  - Duplicate movie versions: Multiple lower-resolution rips of *Interstellar* (2.3 GB, 1.1 GB, 985 MB) and *Moonfall* (926 MB).
  - Duplicate Hugging Face model repository: `models--jayn7--Z-Image-Turbo-GGUF` (4.7 GB duplicate of unsloth's repo).

### 3. Cleanup Actions Executed
- Executed `uv cache clean` (freed 51.5 GB).
- Executed `pip cache purge` (freed 3.1 GB).
- Cleared `yay` and `tracker3` caches (freed ~8.8 GB).
- Pruned broken Hugging Face downloads via `hf cache prune --yes` (freed 5.8 GB).
- Deleted redundant Google Takeout `.zip` (preserving the unzipped files, freeing 39 GB).
- Removed redundant game archive duplicates and lower-res movie rips (retaining the 4K IMAX release).
- Removed the Forza Horizon 6 repack directory.

### 4. Result
- **Free Space**: Jumped from **24 GB to 104 GB Available**.
- **Goal Status**: **Fulfilled**.

---

## Task 2: Steam Download & Network Throughput Optimization

### 1. Problem Statement
The user was downloading Counter-Strike 2 (57 GB) on a 300 Mbps cable connection. Steam was hovering around **94.9 Mbps** (peaking at 212.4 Mbps) with a jagged download/disk graph. Constraint: **Do not interrupt or abort the active Steam download**.

### 2. Diagnosis & Root Causes
1. **Physical Line Verification**:
   - `eth0` was negotiated at **1000 Mb/s Full Duplex** to the CommScope DOCSIS 3.0/3.1 modem.
   - Direct CDN test confirmed **244.35 Mbps** (30.5 MB/s) raw line capacity.
   - Concurrent test: A background speedtest pulled **120.13 Mbit/s download / 14.33 Mbit/s upload** while Steam simultaneously pulled ~100 Mbps (totaling **~220–245 Mbps** aggregate link throughput).
2. **CPU Throttling**:
   - AMD Ryzen 5 5600X had its scaling governor set to **`powersave`** on all 12 threads.
   - Cores frequently downclocked to **558 MHz**.
   - CS2 downloads heavily decompress Zstandard `.vpk` archives on-the-fly; low CPU frequency starved Steam's decompressor threads, creating recurring "Write Gaps" and slowing down network socket reads.
3. **TCP Buffers & Window Collapse**:
   - Congestion control was default `cubic` with small default buffer sizes (`rmem_default = 212 KB`).
   - `tcp_slow_start_after_idle = 1` caused the TCP congestion window to drop back to minimum whenever Steam paused between file chunks.
4. **Steam Warsaw CDN Limits**:
   - Steam connected to Valve's Warsaw cluster (CellID 38: `cacheX-waw1.steamcontent.com`) across 10 connections.
   - Each Warsaw server connection was delivering ~8.5 to 10 Mbps per stream (`10 connections × ~9.5 Mbps ≈ 95 Mbps`).

### 3. Optimizations Applied In-Flight (Zero Interruption)
- **CPU Governor**: Switched all 12 cores to **`performance`** (clocks raised to 3.9 GHz – 4.77 GHz).
- **TCP Stack**:
  - Loaded and activated Google **BBR** (`net.ipv4.tcp_congestion_control = bbr`).
  - Expanded max socket buffers to **64 MB** (`rmem_max = 67108864`, `wmem_max = 67108864`, `tcp_rmem` default to 1 MB).
  - Disabled slow start after idle (`net.ipv4.tcp_slow_start_after_idle = 0`).
  - Set `net.ipv4.tcp_adv_win_scale = 2` and `net.ipv4.tcp_no_metrics_save = 1`.
- **Filesystem**: Remounted `/` with `noatime,commit=60` to eliminate frequent ext4 journal commit stalls during multi-gigabyte chunk writes.
- **Process Scheduling**: Elevated Steam process and worker threads to nice priority **`-10`** and `ionice` priority 0.

### 4. Region Switch & Speed Results
- When the user updated their Steam Download Region to **Germany - Berlin**:
  - All existing download progress (22+ GB) was 100% preserved.
  - Upon reconnection, Steam opened connections to German infrastructure (`fra1` / `fra2`).
  - Instant live throughput surged to **260.25 Mbps (31.02 MB/s)**, hitting near the 300 Mbps cable ceiling.
  - The download progressed smoothly past 26+ GB.

---

## Task 3: Full System Power Management Audit

The user asked whether the rest of the PC was also configured in power-saving mode. A hardware audit revealed:

| Component | Setting Found | Power Saving Status | Description |
|---|---|---|---|
| **CPU** | `amd-pstate-epp` = `powersave` | **YES (Heavily throttled)** | Cores throttled down to 558 MHz. *(Switched to `performance` @ 3.9–4.7 GHz).* |
| **Network (`eth0`)** | EEE (Energy Efficient Ethernet / 802.3az) | **YES (Active)** | Realtek PHY entered Low Power Idle (`Tx LPI: 12 us`) between packet bursts, introducing wake latency and jitter. |
| **Storage (SATA)** | `med_power_with_dipm` | **YES (Active)** | SATA controller aggressively powered down links when idle. |
| **Storage (NVMe)** | APST enabled (`100 ms` latency) | **YES (Standard)** | Autonomous Power State Transitions active. |
| **GPU** | `BOOTUP_DEFAULT` (`auto`) | **NO (Balanced dynamic)** | AMD Radeon RX 7600 was in normal mode: clocks down on desktop, scales to full clock in 3D workloads. |
| **USB** | `usbcore.autosuspend = 2` | **YES (Active)** | Suspended idle USB ports after 2 seconds. |
| **Audio** | `snd_hda_intel.power_save = 10` | **YES (Active)** | Powered down DAC after 10 seconds of silence. |
| **PCIe Bus** | `pcie_aspm` = `[default]` | **Neutral** | Managed by motherboard BIOS defaults. |

---

## Task 4: Waybar Power Modes

The active Mango Waybar now has a mode control at the far right, in place of the Arch icon. Left-click it to choose **Eco**, **Balanced**, or **Max Performance**. Right-click it for the repaired power menu. The controller starts with Eco at each Mango login, automatically uses Balanced while the Sober Flatpak is running, and returns to Eco when Sober closes. A manual selection wins while active; Max is never selected automatically. A manual Balanced or Max choice made outside Sober lasts until Eco is selected or the session ends.

| Mode | Ryzen CPU | Radeon GPU |
|---|---|---|
| Eco | `powersave`, EPP `balance_power`, boost on | Dynamic `auto` |
| Balanced | `powersave`, EPP `balance_performance`, boost on | Dynamic `auto` |
| Max Performance | `performance`, EPP `performance`, boost on | Forced `high` |

No clock cap or undervolt is applied. The GPU detected during this work identifies itself as **RX 7600 XT** (`0x7480`), refining the earlier report's RX 7600 label. The privileged helper is restricted to these three modes; the Sober watcher runs independently of Waybar. The existing power menu did not work because `wlogout` was missing. It is now installed, with lock, logout, shutdown, reboot, and suspend actions repaired. Hibernate was removed because this machine has only zram swap.

**Verification:** Opening Sober switched Eco to Balanced; manual Max took priority; closing Sober returned the system to Eco. All three modes read back correctly from CPU and GPU kernel settings. During a CPU workload in Eco, one core reached **4.77 GHz**, so the earlier 558 MHz reading was not a fixed underclock. A short, identical Vulkan benchmark scored **15,517 Eco**, **15,725 Balanced**, and **15,674 Max**. That difference is too small to claim a speed improvement for this workload. Max showed higher GPU power during the check (37 W at the sampled point); game frame rates and whole-system wall power were not measured.

The project source and configuration snapshot now live together in this directory. `mango/` contains the Waybar, controller, startup, and wlogout files; `power-modes/` contains the restricted root helper, installer, sudoers rule, and controller tests. Run `./install-user-config.sh` to copy the project configuration into `~/.config/mango/`. The currently active files remain there so Mango and Waybar can load them.

---

## Summary of Applied System Settings & Recommendations

**Current power configuration:** The fixed-performance CPU recommendation below records the earlier Steam-download session. It is superseded by the Waybar modes above; do not make that old performance-governor command persistent alongside the mode controller.

### Persistent Commands (If You Wish to Keep These After Rebooting)

#### 1. Keep CPU on Performance
To ensure your CPU does not revert to 558 MHz on reboot:
```bash
# Add to /etc/sysfs.conf or your startup script:
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > "$g"
done
```

#### 2. Keep BBR and High-Throughput Network Settings
Add to `/etc/sysctl.d/99-network-tuning.conf`:
```ini
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 2097152
net.core.wmem_default = 2097152
net.ipv4.tcp_rmem = 8192 1048576 67108864
net.ipv4.tcp_wmem = 8192 1048576 67108864
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_adv_win_scale = 2
net.core.netdev_max_backlog = 10000
```

#### 3. Disable Realtek EEE (If Experiencing Ethernet Latency Dips)
```bash
sudo ethtool --set-eee eth0 eee off
```
