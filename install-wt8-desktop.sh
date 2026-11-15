#!/usr/bin/env bash
# Install a user-local desktop launcher for this checkout of WT8.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
applications="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$applications"
desktop="$applications/wt8.desktop"
# Escape desktop-entry Exec arguments (spaces and shell-special characters).
quote_exec() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//\$/\\$}"
    value="${value//\`/\\\`}"
    printf '"%s"' "$value"
}
launcher="$root/run-wt8.sh"
cat > "$launcher" <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -x .venv/bin/python ]]; then
    exec .venv/bin/python wt8_ubuntu_gui.py "$@"
fi
exec python3 wt8_ubuntu_gui.py "$@"
RUN
chmod +x "$launcher"
{
    printf '[Desktop Entry]\nType=Application\nName=WT8\nGenericName=Antenna Control and Tracking\nComment=WT8 radio telescope antenna control\n'
    printf 'Exec=%s\n' "$(quote_exec "$launcher")"
    printf 'Path=%s\n' "$root"
    printf 'Terminal=false\nCategories=Science;Education;\nStartupNotify=true\nStartupWMClass=WT8\n'
} > "$desktop"
chmod 644 "$desktop"
echo "Installed $desktop"
echo "Close existing WT8 windows, then launch WT8 from the Ubuntu applications menu."
