#!/usr/bin/env bash

set -e

TOOL_NAME="nessusforge"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
INSTALL_DIR="$HOME/.local/bin"
LINK_PATH="$INSTALL_DIR/$TOOL_NAME"

echo "[*] Installing $TOOL_NAME..."

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "[!] main.py not found."
    exit 1
fi

mkdir -p "$INSTALL_DIR"

# Make Python script executable
chmod +x "$MAIN_SCRIPT"

# Remove existing link/file
if [ -L "$LINK_PATH" ] || [ -e "$LINK_PATH" ]; then
    rm -f "$LINK_PATH"
fi

# Create symbolic link
ln -s "$MAIN_SCRIPT" "$LINK_PATH"

echo "[+] Symbolic link created:"
echo "    $LINK_PATH -> $MAIN_SCRIPT"

# Install Python dependencies
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "[!] Python was not found."
    exit 1
fi

echo "[*] Installing Python dependencies..."
"$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt --break-system-packages"

# Add ~/.local/bin to PATH if necessary
case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        ;;
    *)
        echo
        echo "[!] $INSTALL_DIR is not currently in PATH."
        echo "[*] Add this to your shell configuration:"
        echo
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo
        ;;
esac

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
