#!/bin/bash

# Directory containing the search terms
SEARCH_TERMS_DIR="./searchterms"

echo "Please enter the name of the file you wish to process:"
read file_name

# Construct the full path to the file based on the input
file_path="$SEARCH_TERMS_DIR/$file_name.txt"

if [! -f "$file_path" ]; then
    echo "File not found."
    exit 1
fi

# Extract the search term from the file name
search_term=$(basename "$file_path")

# Run the scholarly-cli command with the extracted search term
scholarly-cli --search "$search_term" --results 10 --json True --bibtex True --out "${search_term}_results" --sort_by date --sort_order desc --year_low 2011 --year_high 2023
