#!/bin/bash
# Installs the Glacier Night terminal setup on macOS: Ghostty, nushell, tmux,
# starship, atuin, zoxide and the Claude Code theme. Safe to re-run.
# See SETUP.md for what each step does and the manual IntelliJ step.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
PLUGINS="$HOME/.config/tmux/plugins"

# name|repo|commit. Each commit was read for network calls before pinning.
TMUX_PLUGINS=(
  "tmux-sensible|https://github.com/tmux-plugins/tmux-sensible|25cb91f42d020f675bb0a2ce3fbd3a5d96119efa"
  "tmux-yank|https://github.com/tmux-plugins/tmux-yank|acfd36e4fcba99f8310a7dfb432111c242fe7392"
  "tmux-resurrect|https://github.com/tmux-plugins/tmux-resurrect|cff343cf9e81983d3da0c8562b01616f12e8d548"
  "tmux-continuum|https://github.com/tmux-plugins/tmux-continuum|0698e8f4b17d6454c71bf5212895ec055c578da0"
  "tmux-fzf|https://github.com/sainnhe/tmux-fzf|2839d6bd0e13b7c5e385e131e4c217917fa73555"
  "catppuccin-tmux|https://github.com/omerxx/catppuccin-tmux|e30336b79986e87b1f99e6bd9ec83cffd1da2017"
  "tmux-sessionx|https://github.com/omerxx/tmux-sessionx|8df6df56639acedb5343a6db02cf58120ff09ef7"
  "tmux-floax|https://github.com/omerxx/tmux-floax|133f526793d90d2caa323c47687dd5544a2c704b"
)

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

backup() {
  if [ -e "$1" ] || [ -L "$1" ]; then
    mv "$1" "$1.bak-$STAMP"
    log "backed up $1 -> $1.bak-$STAMP"
  fi
}

install_file() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ] && cmp -s "$src" "$dest"; then return 0; fi
  backup "$dest"
  cp "$src" "$dest"
  log "installed $dest"
}

install_brew_packages() {
  command -v brew >/dev/null || { echo "Homebrew is required: https://brew.sh" >&2; exit 1; }
  log "installing Homebrew packages"
  brew install tmux fzf zoxide nushell starship atuin
  brew install --cask ghostty font-jetbrains-mono-nerd-font
}

install_ghostty() {
  install_file "$REPO/ghostty/dot-config/ghostty/config" "$HOME/.config/ghostty/config"
  install_file "$REPO/ghostty/dot-config/ghostty/themes/Glacier Night Vivid" "$HOME/.config/ghostty/themes/Glacier Night Vivid"

  local app_support="$HOME/Library/Application Support/com.mitchellh.ghostty/config.ghostty"
  if [ -s "$app_support" ]; then
    echo "WARNING: $app_support exists and overrides ~/.config/ghostty/config. Empty or remove it." >&2
  fi
}

install_nushell() {
  local dir="$HOME/Library/Application Support/nushell"
  install_file "$REPO/nushell/dot-config/nushell/config.nu" "$dir/config.nu"
  install_file "$REPO/nushell/dot-config/nushell/env.nu" "$dir/env.nu"
}

install_tmux_plugin() {
  local name="$1" url="$2" commit="$3" dir="$PLUGINS/$1"
  if [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$commit" ]; then return 0; fi
  backup "$dir"
  git clone --quiet "$url" "$dir"
  git -C "$dir" -c advice.detachedHead=false checkout --quiet "$commit"
  log "pinned $name at ${commit:0:7}"
}

install_tmux() {
  install_file "$REPO/tmux/dot-config/tmux/tmux.conf" "$HOME/.config/tmux/tmux.conf"
  install_file "$REPO/tmux/dot-config/tmux/tmux.reset.conf" "$HOME/.config/tmux/tmux.reset.conf"

  local entry
  for entry in "${TMUX_PLUGINS[@]}"; do
    IFS='|' read -r name url commit <<<"$entry"
    install_tmux_plugin "$name" "$url" "$commit"
  done

  install_file "$REPO/tmux/catppuccin-glacier-night-vivid.tmuxtheme" "$PLUGINS/catppuccin-tmux/catppuccin-glacier-night-vivid.tmuxtheme"
}

install_shell_tools() {
  install_file "$REPO/starship/dot-config/starship/starship.toml" "$HOME/.config/starship/starship.toml"
  install_file "$REPO/atuin/dot-config/atuin/config.toml" "$HOME/.config/atuin/config.toml"
  install_file "$REPO/zsh/dot-config/zsh/tools.zsh" "$HOME/.config/zsh/tools.zsh"

  local line='source ~/.config/zsh/tools.zsh'
  touch "$HOME/.zshrc"
  if ! grep -qxF "$line" "$HOME/.zshrc"; then
    printf '\n%s\n' "$line" >>"$HOME/.zshrc"
    log "added '$line' to ~/.zshrc"
  fi
}

install_claude_theme() {
  install_file "$REPO/claude/dot-claude/themes/glacier-night-vivid.json" "$HOME/.claude/themes/glacier-night-vivid.json"

  local settings="$HOME/.claude/settings.json"
  [ -f "$settings" ] || echo '{}' >"$settings"
  cp "$settings" "$settings.bak-$STAMP"
  python3 -I - "$settings" <<'EOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    settings = json.load(f)
settings["theme"] = "custom:glacier-night-vivid"
with open(path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
EOF
  log "set Claude Code theme in $settings (backup: $settings.bak-$STAMP)"
}

main() {
  install_brew_packages
  install_ghostty
  install_nushell
  install_tmux
  install_shell_tools
  install_claude_theme

  log "done. Manual step left: install the IntelliJ theme (see SETUP.md)."
}

main "$@"
