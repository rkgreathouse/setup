# Glacier Night setup

A terminal and editor setup in one palette, Glacier Night Vivid: Ghostty
running nushell, tmux (where panes run zsh with starship, zoxide and atuin),
Claude Code, and IntelliJ. Everything runs locally; nothing in it sends data
anywhere or downloads code after install.

## Quick start

macOS with [Homebrew](https://brew.sh) installed. From the repo root:

```sh
./setup.sh
```

Then do the one manual step, [IntelliJ](#intellij), and open a new Ghostty
window. Run `tmux` to start a session.

`setup.sh` is safe to re-run. It moves any file it would replace to
`<file>.bak-<timestamp>` first, and skips files that already match.

## What setup.sh does

Each step below is one function in `setup.sh`, run in this order.

| Step | Installs | To |
| --- | --- | --- |
| `install_brew_packages` | `tmux fzf zoxide nushell starship atuin`, casks `ghostty font-jetbrains-mono-nerd-font` | Homebrew |
| `install_ghostty` | `ghostty/dot-config/ghostty/config` and `themes/Glacier Night Vivid` | `~/.config/ghostty/` |
| `install_nushell` | `nushell/dot-config/nushell/{config,env}.nu` | `~/Library/Application Support/nushell/` |
| `install_tmux` | `tmux/dot-config/tmux/{tmux,tmux.reset}.conf`, 8 plugins at pinned commits, `tmux/catppuccin-glacier-night-vivid.tmuxtheme` | `~/.config/tmux/`, `~/.config/tmux/plugins/` |
| `install_shell_tools` | `starship.toml`, atuin `config.toml`, `zsh/dot-config/zsh/tools.zsh`, and appends `source ~/.config/zsh/tools.zsh` to `~/.zshrc` | `~/.config/` |
| `install_claude_theme` | `claude/dot-claude/themes/glacier-night-vivid.json`, and sets only the `theme` key in `settings.json` | `~/.claude/` |

Ghostty also reads
`~/Library/Application Support/com.mitchellh.ghostty/config.ghostty`, and that
file wins over `~/.config/ghostty/config`. `setup.sh` warns if it is non-empty.

## IntelliJ

Manual, because the plugins folder depends on the IDE version.

1. **Settings → Plugins → ⚙ → Install Plugin from Disk**, pick
   `themes/glacier-night-vivid-intellij/build/GlacierNightVivid.jar`.
2. **Appearance → Theme**: Glacier Night Vivid. The editor color scheme of the
   same name comes with it.

The jar holds only `plugin.xml` and theme JSON/XML, no code. Rebuild it from
`src/` with `themes/glacier-night-vivid-intellij/build.sh` (needs `jar` from a
JDK). Needs IntelliJ 2025.3 or later.

## Security notes

These were checked before the setup was brought to a work machine.

- **No tpm.** tmux plugins are cloned once by `setup.sh` at the commits in its
  `TMUX_PLUGINS` list, and `tmux.conf` loads each one with `run-shell`.
  `prefix + I` does nothing, so no plugin updates itself. To update one, read
  its diff, then change the commit in `setup.sh`.
- **Left out on purpose:** `tmux-fzf-url` (runs `curl | bash` on first use),
  `tmux-thumbs` (downloads a binary on first use), and all Claude Code plugins
  (Impeccable has telemetry and an update check; Firecrawl is a remote MCP
  server).
- **atuin** has `auto_sync = false` and `update_check = false`. It never logs
  in to a sync server. `tools.zsh` starts it with `--disable-ai`, because by
  default `?` at an empty prompt opens Atuin AI, a hosted service.
- **catppuccin-tmux** is omerxx's fork: upstream plus a meetings module that
  reads the macOS calendar with `icalBuddy`. The module is off in `tmux.conf`.
- The only network access is at install time: Homebrew, and `git clone` from
  GitHub for the pinned plugins.

## For an LLM running this

- Run `./setup.sh` from the repo root and report its output. Don't run steps
  by hand unless one fails.
- Never add tpm, `@plugin` lines, `tmux-fzf-url`, `tmux-thumbs`, or any Claude
  Code plugin or marketplace; see Security notes.
- Don't overwrite `~/.claude/settings.json` or `~/.zshrc`; the script edits one
  key and appends one line on purpose, since a work machine may manage the rest.
- If `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty` is
  non-empty, ask the user before emptying it.
- The IntelliJ step needs the user to click through the IDE; tell them the
  steps in [IntelliJ](#intellij).
