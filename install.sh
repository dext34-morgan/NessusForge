#!/usr/bin/env bash

set -e

TOOL_NAME="nessusforge"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
INSTALL_DIR="$HOME/.local/bin"
LAUNCHER="$INSTALL_DIR/$TOOL_NAME"

echo "[*] Installing $TOOL_NAME..."

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "[!] main.py not found."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "[!] requirements.txt not found."
    exit 1
fi

# --------------------------------------------------
# Find Python
# --------------------------------------------------

if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "[!] Python was not found."
    exit 1
fi

echo "[+] Using Python: $("$PYTHON" --version)"

# --------------------------------------------------
# Create ~/.local/bin
# --------------------------------------------------

mkdir -p "$INSTALL_DIR"

# --------------------------------------------------
# Remove old launcher/symlink
# --------------------------------------------------

if [ -L "$LAUNCHER" ] || [ -f "$LAUNCHER" ]; then
    echo "[*] Removing existing launcher..."
    rm -f "$LAUNCHER"
fi

# --------------------------------------------------
# Create launcher
# --------------------------------------------------

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
exec "$PYTHON" "$MAIN_SCRIPT" "\$@"
EOF

chmod +x "$LAUNCHER"

echo "[+] Launcher created:"
echo "    $LAUNCHER"

# --------------------------------------------------
# Install dependencies
# --------------------------------------------------

echo "[*] Installing Python dependencies..."

"$PYTHON" -m pip install \
    -r "$SCRIPT_DIR/requirements.txt" \
    --break-system-packages

# --------------------------------------------------
# PATH check
# --------------------------------------------------

case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        ;;
    *)
        echo
        echo "[!] $INSTALL_DIR is not currently in PATH."
        echo
        echo "Add this to ~/.zshrc:"
        echo
        echo 'export PATH="$HOME/.local/bin:$PATH"'
        echo
        ;;
esac

# --------------------------------------------------
# Test installation
# --------------------------------------------------

echo
echo "[*] Testing NessusForge..."

"$LAUNCHER" --version

echo
echo "[+] Installation completed."
echo
echo "Usage:"
echo "    nessusforge"
echo "    nessusforge report.html"
echo "    nessusforge report.html -pdf report.pdf"
echo "    nessusforge report.html -pdf report.pdf -o results"
echo
echo "Check version:"
echo "    nessusforge --version"
