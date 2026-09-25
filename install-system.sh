#!/usr/bin/env bash
set -euo pipefail
# System install: privileged helper + sudoers + wlogout dependency.
# Usage: sudo ./install-system.sh [--user <name>]

TARGET_USER="${SUDO_USER:-${USER:-}}"
while [ $# -gt 0 ]; do
  case "$1" in
    --user) TARGET_USER="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$TARGET_USER" ]; then
  echo "Cannot determine target user (use --user <name>)." >&2
  exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo ./install-system.sh" >&2
  exit 1
fi

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

install -d -o root -g root -m 0755 /usr/local/libexec
install -o root -g root -m 0755 "$REPO_DIR/libexec/performance-mode-apply" /usr/local/libexec/performance-mode-apply

# Render sudoers template with the real username (no hardcoded 'user').
sed "s/%INSTALL_USER%/$TARGET_USER/" "$REPO_DIR/libexec/mango-performance-mode.sudoers.template" \
  > /etc/sudoers.d/mango-performance-mode
chmod 0440 /etc/sudoers.d/mango-performance-mode
visudo -cf /etc/sudoers.d/mango-performance-mode

# wlogout dependency (distro-aware; original was pacman-only).
if ! command -v wlogout >/dev/null 2>&1; then
  if command -v pacman >/dev/null 2>&1; then
    pacman -S --noconfirm --needed wlogout
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y wlogout
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y wlogout
  else
    echo "Please install 'wlogout' manually for the right-click power menu." >&2
  fi
fi

echo "System install complete for user '$TARGET_USER'."
echo "Verify: sudo -n /usr/local/libexec/performance-mode-apply eco"
