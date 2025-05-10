#!/bin/bash

BASE_URL="https://www.siperb.com/kb/"
OUTPUT_DIR="./output"
DEPTH=3
LOG_FILE="log.txt"

echo "🔍 Scraping Website ${BASE_URL}"

# Check if output directory exists, if not create it
if [ ! -d "$OUTPUT_DIR" ]; then
  echo "📂 Output directory '$OUTPUT_DIR' does not exist. Creating..."
  mkdir -p "$OUTPUT_DIR"
else
  echo "📂 Output directory '$OUTPUT_DIR' already exists."
fi

# Run the scraper
python3 AdvancedScrap.py "${BASE_URL}*" -o "$OUTPUT_DIR" -depth "$DEPTH" > "$LOG_FILE" 2>&1

echo "✅ Finished. Logs saved to $LOG_FILE"