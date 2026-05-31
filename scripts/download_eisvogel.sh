#!/usr/bin/env bash
#
# Download the Eisvogel pandoc LaTeX template into templates/eisvogel.latex.
# Re-run this to update the bundled template to a new release.
#
# Usage: scripts/download_eisvogel.sh [VERSION]   (default: version in templates/EISVOGEL_VERSION)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/templates"
VERSION="${1:-$(cat "$TEMPLATE_DIR/EISVOGEL_VERSION" 2>/dev/null || echo v3.4.0)}"
VERSION="${VERSION#v}"  # normalize: strip a leading "v" if present

URL="https://github.com/Wandmalfarbe/pandoc-latex-template/releases/download/v${VERSION}/Eisvogel.tar.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading Eisvogel v${VERSION} ..."
curl -sSL -o "$TMP/eisvogel.tar.gz" "$URL"
tar xzf "$TMP/eisvogel.tar.gz" -C "$TMP" \
    "Eisvogel-${VERSION}/eisvogel.latex" "Eisvogel-${VERSION}/LICENSE"

mkdir -p "$TEMPLATE_DIR"
cp "$TMP/Eisvogel-${VERSION}/eisvogel.latex" "$TEMPLATE_DIR/eisvogel.latex"
cp "$TMP/Eisvogel-${VERSION}/LICENSE" "$TEMPLATE_DIR/EISVOGEL-LICENSE"
echo "v${VERSION}" > "$TEMPLATE_DIR/EISVOGEL_VERSION"

echo "Installed templates/eisvogel.latex (Eisvogel v${VERSION})"
