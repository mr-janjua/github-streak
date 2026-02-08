#!/bin/bash

echo "🔥 GitHub Streak Tracker Installation 🔥"
echo ""

INSTALL_DIR="$HOME/.local/bin/github-streak"
mkdir -p "$INSTALL_DIR"

echo "Installing Python dependencies..."
pip3 install --break-system-packages -r requirements_streak.txt

echo "Copying files..."
cp streak.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/streak.py"

echo "Creating command alias..."
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "alias streak=" "$SHELL_RC"; then
    echo "alias streak='python3 $INSTALL_DIR/streak.py'" >> "$SHELL_RC"
    echo "✓ Added 'streak' command to $SHELL_RC"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Usage:"
echo "  source $SHELL_RC  (or restart terminal)"
echo "  streak            - Start the tracker"
echo "  streak stats      - View your stats"
echo "  streak check      - Check now"
echo "  streak setup      - Configure settings"
echo "  streak mode strict/normal - Change reminder intensity"
echo ""
echo "To run at startup:"
echo "  1. Edit github-streak.service and update paths"
echo "  2. cp github-streak.service ~/.config/systemd/user/"
echo "  3. systemctl --user enable github-streak.service"
echo "  4. systemctl --user start github-streak.service"
echo ""
echo "Run 'streak' to get started!"
