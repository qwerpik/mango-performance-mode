#!/usr/bin/env bash
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/mango-performance-mode"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mango"
REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

echo "Installing mango-performance-mode to $PREFIX..."

mkdir -p "$BIN_DIR" "$LIB_DIR"

# Clean previous library for idempotent installs
rm -rf "$LIB_DIR/src"
mkdir -p "$LIB_DIR"
cp -r "$REPO_DIR/src/mango_performance_modes" "$LIB_DIR/"
chmod -R u=rwX,go=rX "$LIB_DIR"

# Executable runner on PATH (portable: no /home/user hardcodes)
cat > "$BIN_DIR/mango-performance-mode" <<EOF
#!/usr/bin/env python3
import sys
sys.path.insert(0, "$LIB_DIR")
from mango_performance_modes.controller import main
if __name__ == "__main__":
    raise SystemExit(main())
EOF
chmod +x "$BIN_DIR/mango-performance-mode"

install_config() {
  local src="$1" dest="$2" mode="$3"
  mkdir -p "$(dirname "$dest")"
  if [ -f "$dest" ] && ! cmp -s "$src" "$dest"; then
    cp -a "$dest" "$dest.bak.$(date +%Y%m%d%H%M%S)"
    echo "Backed up existing $(basename "$dest")"
  fi
  install -m "$mode" "$src" "$dest"
}

install_config "$REPO_DIR/config/waybar/performance_menu.xml" "$CONFIG_DIR/waybar/performance_menu.xml" 0644
install_config "$REPO_DIR/config/wlogout/layout" "$CONFIG_DIR/wlogout/layout" 0644
install_config "$REPO_DIR/config/wlogout/style.css" "$CONFIG_DIR/wlogout/style.css" 0644

echo "=========================================================="
echo "User install complete!"
echo "Binary: $BIN_DIR/mango-performance-mode"
echo "Waybar menu: $CONFIG_DIR/waybar/performance_menu.xml"
echo ""
echo "Next:"
echo "  1. sudo ./install-system.sh   # privileged helper + sudoers + wlogout"
echo "  2. Add config/waybar/performance-module.jsonc to your Waybar config"
echo "     (see docs/WAYBAR.md)"
echo "  3. Merge config/waybar/performance-mode.css into your Waybar style.css"
echo "=========================================================="

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "WARNING: '$BIN_DIR' is not in your PATH."
    echo "  Bash/Zsh: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  Fish:     fish_add_path \$HOME/.local/bin"
    ;;
esac
