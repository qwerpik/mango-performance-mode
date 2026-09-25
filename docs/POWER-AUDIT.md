# Power Audit & Network Tuning Notes

Distilled from the original session log (`docs/REPORT.md`). The report's persistent system-tuning recommendations, separated from the installable project:

## CPU

The Ryzen 5 5600X shipped in `powersave` (down to ~558 MHz), which starved Steam's decompressor threads. The mode controller now owns this: Eco/Balanced use `powersave` + EPP `balance_power`/`balance_performance`, Max uses `performance` + EPP `performance`, boost always on. Do not also persist a manual `scaling_governor` override — it fights the daemon.

## Network (Steam 95 → 260 Mbps in-session)

What helped during the 57 GB CS2 download without interrupting it:

```ini
# /etc/sysctl.d/99-network-tuning.conf
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

Plus in-flight: `performance` governor, `/` remounted `noatime,commit=60`, Steam niced to `-10`, and a region switch (Warsaw → Berlin) when the local CDN capped per-connection throughput. Ethernet EEE (`ethtool --set-eee eth0 eee off`) is worth trying if you see latency dips.

## Audit Snapshot

| Component | Finding |
|---|---|
| CPU `amd-pstate-epp` | throttled (now managed by modes) |
| Ethernet EEE 802.3az | active (Low Power Idle jitter) |
| SATA `med_power_with_dipm` | active |
| NVMe APST 100 ms | active (standard) |
| GPU | dynamic `auto` is fine; `high` only in Max |
| USB autosuspend 2s / audio 10s | active |
| PCIe ASPM | BIOS default |

See `docs/REPORT.md` for the full original log including the disk-cleanup walkthrough (~81 GB reclaimed).
