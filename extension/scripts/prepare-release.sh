#!/usr/bin/env bash
#
# prepare-release.sh — Prepare a SelfPublisherForge extension release.
#
# Usage:
#   ./scripts/prepare-release.sh <EXTENSION_ID> <VERSION>
#
# Example:
#   ./scripts/prepare-release.sh abcdefghijklmnopqrstuvwxyzabcdef 1.2.0
#
# What it does:
#   1. Validates the EXTENSION_ID (32 lowercase hex-alpha chars) and VERSION (semver).
#   2. Replaces the EXTENSION_ID placeholder in updates.xml.
#   3. Updates the version in updates.xml and manifest.json.
#   4. Creates a zip archive ready for Chrome Web Store upload.
#   5. Prints a summary of all changes.
#

set -euo pipefail

# ---------------------------------------------------------------------------
# Colors (disabled if stdout is not a terminal)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' CYAN='' BOLD='' NC=''
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { printf "${CYAN}[INFO]${NC}  %s\n" "$1"; }
ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$1" >&2; }
die()   { error "$1"; exit 1; }

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $(basename "$0") <EXTENSION_ID> <VERSION>

Arguments:
  EXTENSION_ID   32-character Chrome extension ID (lowercase a-p).
                 Find it at chrome://extensions after loading the unpacked
                 extension, or in the Chrome Web Store Developer Dashboard.

  VERSION        Semantic version string (e.g. 1.0.0, 2.1.3).

Examples:
  $(basename "$0") abcdefghijklmnopabcdefghijklmnop 1.0.0
  $(basename "$0") lmjnogfhijkabcdelmnopqrstuvwxyza 2.3.1
EOF
  exit 1
}

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
if [ $# -ne 2 ]; then
  error "Expected exactly 2 arguments, got $#."
  usage
fi

EXTENSION_ID="$1"
VERSION="$2"

# Validate extension ID: must be exactly 32 lowercase letters (a-p)
# Chrome extension IDs use a base-16 encoding mapped to a-p.
if ! echo "$EXTENSION_ID" | grep -qE '^[a-p]{32}$'; then
  die "Invalid EXTENSION_ID: '${EXTENSION_ID}'. Must be exactly 32 lowercase letters (a-p). Example: abcdefghijklmnopabcdefghijklmnop"
fi

# Validate version: semver-like (MAJOR.MINOR.PATCH), optionally with a fourth segment
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$'; then
  die "Invalid VERSION: '${VERSION}'. Must be a semver string like 1.0.0 or 1.2.3.4"
fi

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
UPDATES_XML="$EXT_DIR/updates.xml"
MANIFEST_JSON="$EXT_DIR/manifest.json"
BUILD_DIR="$EXT_DIR/build"
ZIP_NAME="selfpublisherforge-v${VERSION}.zip"

# Verify required files exist
[ -f "$UPDATES_XML" ]  || die "updates.xml not found at $UPDATES_XML"
[ -f "$MANIFEST_JSON" ] || die "manifest.json not found at $MANIFEST_JSON"

info "Preparing release v${VERSION} for extension ${EXTENSION_ID}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Update updates.xml
# ---------------------------------------------------------------------------
info "Updating updates.xml ..."

# Replace EXTENSION_ID placeholder (or any previous ID) in the appid attribute
sed -i.bak -E "s/appid='[^']+'/appid='${EXTENSION_ID}'/" "$UPDATES_XML"

# Update version in the updatecheck tag
sed -i.bak -E "s/version='[^']+'/version='${VERSION}'/" "$UPDATES_XML"

# Clean up backup files
rm -f "$UPDATES_XML.bak"

ok "updates.xml: appid='${EXTENSION_ID}', version='${VERSION}'"

# ---------------------------------------------------------------------------
# Step 2: Update manifest.json
# ---------------------------------------------------------------------------
info "Updating manifest.json ..."

# Use a portable approach: read, transform with sed, write back.
# Update the "version" field (top-level, not inside nested objects).
sed -i.bak -E 's/"version":\s*"[^"]+"/"version": "'"${VERSION}"'"/' "$MANIFEST_JSON"

# Clean up backup files
rm -f "$MANIFEST_JSON.bak"

ok "manifest.json: version='${VERSION}'"

# ---------------------------------------------------------------------------
# Step 3: Create release zip
# ---------------------------------------------------------------------------
info "Creating release zip ..."

mkdir -p "$BUILD_DIR"

# Build the zip from the extension directory, excluding dev/build artifacts
(
  cd "$EXT_DIR"
  zip -r "$BUILD_DIR/$ZIP_NAME" . \
    -x "build/*" \
    -x "scripts/*" \
    -x "*.bak" \
    -x ".git/*" \
    -x "*.md" \
    -x "node_modules/*" \
    -x ".DS_Store" \
    -x "Thumbs.db"
)

ZIP_PATH="$BUILD_DIR/$ZIP_NAME"
ZIP_SIZE=$(wc -c < "$ZIP_PATH" | tr -d ' ')

ok "Created $ZIP_PATH (${ZIP_SIZE} bytes)"

# ---------------------------------------------------------------------------
# Step 4: Summary
# ---------------------------------------------------------------------------
echo ""
printf "${BOLD}============================================${NC}\n"
printf "${BOLD}  Release Summary${NC}\n"
printf "${BOLD}============================================${NC}\n"
echo ""
printf "  Extension ID : ${CYAN}%s${NC}\n" "$EXTENSION_ID"
printf "  Version      : ${CYAN}%s${NC}\n" "$VERSION"
printf "  Zip file     : ${CYAN}%s${NC}\n" "$ZIP_PATH"
printf "  Zip size     : ${CYAN}%s bytes${NC}\n" "$ZIP_SIZE"
echo ""
printf "${BOLD}  Files modified:${NC}\n"
printf "    - %s\n" "$UPDATES_XML"
printf "    - %s\n" "$MANIFEST_JSON"
echo ""
printf "${BOLD}  Next steps:${NC}\n"
printf "    1. Test the extension locally (load unpacked from %s)\n" "$EXT_DIR"
printf "    2. Upload ${CYAN}%s${NC} to the Chrome Web Store Developer Dashboard\n" "$ZIP_NAME"
printf "    3. If self-hosting, upload the .crx to your server and ensure\n"
printf "       updates.xml is served at the update_url in manifest.json\n"
printf "    4. Commit and tag the release: git tag v%s\n" "$VERSION"
echo ""
printf "${GREEN}Done!${NC}\n"
