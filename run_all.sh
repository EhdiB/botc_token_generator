#!/bin/bash

# Ensure the script stops on errors
set -e

echo "Step 1: Running 'get_assets_from_wiki.py'..."
python get_assets_from_wiki.py
echo "Step 1 complete!"

echo "Step 2: Running 'generate_tokens_and_reminders.py'..."
python generate_tokens_and_reminders.py
echo "Step 2 complete!"

echo "Step 3: Running 'save_tokens_to_pdf.py'..."
python save_tokens_to_pdf.py
echo "Step 3 complete!"

echo "Step 4: Running 'generate_night_order_sheet.py'..."
python generate_night_order_sheet.py
echo "Step 4 complete!"

echo "All steps completed successfully!"