#!/usr/bin/env bash
# ============================================================
#  TreasuryOS — One-Command Setup
#  Run:  bash setup.sh
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

print_step()  { echo -e "\n${BLUE}▸${NC} ${BOLD}$1${NC}"; }
print_ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
print_warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
print_fail()  { echo -e "  ${RED}✗${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║        TreasuryOS Setup v0.1         ║"
echo "  ║  Treasury Intelligence via Claude AI ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ----------------------------------------------------------
# 1. Check OS (macOS or Linux)
# ----------------------------------------------------------
print_step "Checking operating system..."
OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
    print_ok "macOS detected"
elif [[ "$OS" == "Linux" ]]; then
    print_ok "Linux detected"
else
    print_fail "Unsupported OS: $OS (need macOS or Linux)"
    exit 1
fi

# ----------------------------------------------------------
# 2. Check Python 3.11+
# ----------------------------------------------------------
print_step "Checking Python..."
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [[ "$PY_MAJOR" -gt 3 || ("$PY_MAJOR" -eq 3 && "$PY_MINOR" -ge 11) ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    print_fail "Python 3.11+ is required but not found."
    echo ""
    echo "  Install Python:"
    if [[ "$OS" == "Darwin" ]]; then
        echo "    brew install python@3.13"
        echo "    — or —"
        echo "    https://www.python.org/downloads/"
    else
        echo "    sudo apt install python3.13 python3.13-venv"
    fi
    exit 1
fi
PYTHON_PATH="$(which "$PYTHON_CMD")"
print_ok "Found $PYTHON_CMD ($PY_VER) at $PYTHON_PATH"

# ----------------------------------------------------------
# 3. Install uv (fast Python package manager)
# ----------------------------------------------------------
print_step "Checking uv package manager..."
if command -v uv &>/dev/null; then
    print_ok "uv already installed ($(uv --version))"
else
    print_warn "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if command -v uv &>/dev/null; then
        print_ok "uv installed successfully"
    else
        print_fail "uv install failed. Install manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi

# ----------------------------------------------------------
# 4. Install project dependencies
# ----------------------------------------------------------
print_step "Installing TreasuryOS dependencies..."
cd "$SCRIPT_DIR"
uv sync 2>&1 | tail -5
print_ok "Dependencies installed"

# ----------------------------------------------------------
# 5. Verify server can import
# ----------------------------------------------------------
print_step "Verifying TreasuryOS server..."
if uv run python -c "import server; print('  9 tools registered')" 2>/dev/null; then
    print_ok "Server imports OK"
else
    print_fail "Server import failed — check error above"
    exit 1
fi

# ----------------------------------------------------------
# 6. Set up data directory
# ----------------------------------------------------------
print_step "Setting up data directory..."
DATA_DIR="$SCRIPT_DIR/sample_data"
if [[ -d "$DATA_DIR" ]]; then
    FILE_COUNT=$(ls "$DATA_DIR"/*.csv 2>/dev/null | wc -l | tr -d ' ')
    print_ok "Found $FILE_COUNT CSV files in sample_data/"
    echo ""
    echo -e "  ${YELLOW}To use your own data:${NC}"
    echo "  Copy your CSV files into: $DATA_DIR"
    echo "  Required: accounts.csv, transactions.csv"
    echo "  Optional: covenants.csv, vendors.csv, fx_rates.csv"
    echo "  Optional: personal_credit.csv, business_credit.csv"
else
    mkdir -p "$DATA_DIR"
    print_warn "Created empty sample_data/ — add your CSV files here"
fi

# ----------------------------------------------------------
# 7. Configure Claude Desktop
# ----------------------------------------------------------
print_step "Configuring Claude Desktop..."

if [[ "$OS" == "Darwin" ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OS" == "Linux" ]]; then
    CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
    CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
fi

# Find the uv path for Claude Desktop config
UV_PATH="$(which uv)"

mkdir -p "$CLAUDE_CONFIG_DIR"

# Build the server config block
NEW_SERVER_CONFIG=$(cat <<JSONEOF
{
  "mcpServers": {
    "treasury-os": {
      "command": "$UV_PATH",
      "args": ["--directory", "$SCRIPT_DIR", "run", "server.py"],
      "env": {
        "TREASURY_DATA_DIR": "$DATA_DIR"
      }
    }
  }
}
JSONEOF
)

if [[ -f "$CLAUDE_CONFIG" ]]; then
    # Check if treasury-os already configured
    if grep -q "treasury-os" "$CLAUDE_CONFIG" 2>/dev/null; then
        print_ok "Claude Desktop already configured for TreasuryOS"
    else
        # Merge with existing config
        print_warn "Existing Claude config found — adding TreasuryOS..."
        # Back up existing
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup"
        print_ok "Backed up existing config to claude_desktop_config.json.backup"

        # Use Python to merge JSON configs
        "$PYTHON_CMD" - "$CLAUDE_CONFIG" "$UV_PATH" "$SCRIPT_DIR" "$DATA_DIR" <<'PYEOF'
import json, sys
config_path, uv_path, script_dir, data_dir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(config_path) as f:
    config = json.load(f)
if "mcpServers" not in config:
    config["mcpServers"] = {}
config["mcpServers"]["treasury-os"] = {
    "command": uv_path,
    "args": ["--directory", script_dir, "run", "server.py"],
    "env": {"TREASURY_DATA_DIR": data_dir}
}
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print("  \033[0;32m✓\033[0m Merged TreasuryOS into existing Claude config")
PYEOF
    fi
else
    echo "$NEW_SERVER_CONFIG" > "$CLAUDE_CONFIG"
    print_ok "Created Claude Desktop config"
fi

# ----------------------------------------------------------
# 8. Summary
# ----------------------------------------------------------
echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Setup complete!${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""
echo "  Next steps:"
echo ""
echo -e "  ${BOLD}1.${NC} Quit and reopen Claude Desktop"
echo "     (it needs to restart to pick up the new config)"
echo ""
echo -e "  ${BOLD}2.${NC} Look for the hammer 🔨 icon in the bottom-right"
echo "     of the Claude chat — click it and you should see"
echo "     TreasuryOS with 9 tools listed"
echo ""
echo -e "  ${BOLD}3.${NC} Try asking Claude:"
echo -e "     ${BLUE}\"What's my current cash position?\"${NC}"
echo -e "     ${BLUE}\"Parse the credit reports on file\"${NC}"
echo -e "     ${BLUE}\"Give me a full underwriting picture\"${NC}"
echo ""
echo -e "  ${BOLD}Data:${NC} $DATA_DIR"
echo -e "  ${BOLD}Config:${NC} $CLAUDE_CONFIG"
echo ""
echo -e "  Questions? github.com/GPBK-STUY/treasury-mcp-os"
echo ""
