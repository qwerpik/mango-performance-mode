#!/usr/bin/env bash
set -euo pipefail
# Usage: sudo ./uninstall-system.sh
if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo ./uninstall-system.sh" >&2
  exit 1
fi
rm -f /usr/local/libexec/performance-mode-apply /etc/sudoers.d/mango-performance-mode
echo "Privileged helper and sudoers rule removed."
echo "Note: wlogout package is left installed."
