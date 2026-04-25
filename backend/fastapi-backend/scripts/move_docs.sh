#!/bin/bash
# Helper script to move new .md files to README folder
# Usage: ./scripts/move_docs.sh file1.md file2.md ...

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1.md> [file2.md] ..."
    echo "Moves markdown files to README/ folder"
    exit 1
fi

for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "Warning: $file does not exist, skipping..."
        continue
    fi
    
    if [[ "$file" != *.md ]]; then
        echo "Warning: $file is not a .md file, skipping..."
        continue
    fi
    
    # Don't move README.md from root
    if [ "$(basename "$file")" = "README.md" ] && [ "$(dirname "$file")" = "." ]; then
        echo "Skipping root README.md (should stay in root)"
        continue
    fi
    
    # Move to README folder
    mv "$file" README/
    echo "✓ Moved $file to README/"
done

echo ""
echo "Done! All files moved to README/ folder"

