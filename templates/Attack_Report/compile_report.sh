#!/bin/bash
# DShield-MCP LaTeX Report Compilation Script

set -e

REPORT_FILE="${1:-main_report.tex}"
OUTPUT_DIR="${2:-output}"

echo "Compiling LaTeX report: $REPORT_FILE"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Compile LaTeX (run twice for references)
pdflatex -output-directory="$OUTPUT_DIR" "$REPORT_FILE"
pdflatex -output-directory="$OUTPUT_DIR" "$REPORT_FILE"

echo "Report compiled successfully!"
echo "Output: $OUTPUT_DIR/$(basename "$REPORT_FILE" .tex).pdf"
