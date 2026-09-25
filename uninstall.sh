#!/usr/bin/env bash
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/mango-performance-mode"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mango"

echo "Uninstalling mango-performance-mode from $PREFIX..."

rm -f "$BIN_DIR/mango-performance-mode"
if [ -n "$LIB_DIR" ] && [ -d "$LIB_DIR" ]; then
  rm -rf "$LIB_DIR"
fi

if [ "${1:-}" = "--purge" ]; then
  echo "Purging Waybar/wlogout snippets installed by install.sh..."
  rm -f "$CONFIG_DIR/waybar/performance_menu.xml"
  rm -f "$CONFIG_DIR/wlogout/layout" "$CONFIG_DIR/wlogout/style.css"
  echo "Note: sudo ./uninstall-system.sh removes the privileged helper."
fi

echo "User files removed."
