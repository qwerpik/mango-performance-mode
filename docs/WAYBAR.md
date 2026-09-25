# Waybar Setup

## 1. Install

```bash
git clone https://github.com/qwerpik/mango-performance-mode.git
cd mango-performance-mode
./install.sh
sudo ./install-system.sh
```

`install.sh` puts `mango-performance-mode` on `PATH` (`~/.local/bin` by default), installs `performance_menu.xml` and the `wlogout` layout/style under `~/.config/mango/`, and backs up anything it overwrites (`*.bak.TIMESTAMP`).

## 2. Add the module

Merge `config/waybar/performance-module.jsonc` into your Waybar config:

```jsonc
"modules-right": ["tray", "cpu", "memory", "clock", "custom/performance-mode"],
"custom/performance-mode": {
    "format": "{}",
    "return-type": "json",
    "exec": "mango-performance-mode status",
    "interval": 2,
    "menu": "on-click",
    "menu-file": "~/.config/mango/waybar/performance_menu.xml",
    "menu-actions": {
        "eco": "mango-performance-mode set eco",
        "balanced": "mango-performance-mode set balanced",
        "max": "mango-performance-mode set max"
    },
    "on-click-right": "wlogout -C ~/.config/mango/wlogout/style.css -l ~/.config/mango/wlogout/layout -b 5 --protocol layer-shell"
}
```

## 3. Style it

Append `config/waybar/performance-mode.css` to your `style.css` for eco/balanced/max/error colors.

## 4. Start the daemon

Run at Mango login (replace your autostart's bar section):

```bash
mango-performance-mode daemon >>/tmp/mango-performance-mode.log 2>&1 &
waybar -c ~/.config/mango/waybar/config.jsonc -s ~/.config/mango/waybar/style.css &
```

Left-click the module to switch Eco/Balanced/Max. Right-click opens the power menu. While the Sober Flatpak runs, the controller auto-selects Balanced; closing Sober returns to Eco unless you picked manually.
