# Scholarly CLI

This is a command-line tool (`scholarly-cli.py`) built using Python to interact with Google Scholar and retrieve publication data based on a user query.

## Usage

### Prerequisites
- Python 3.x installed on your machine (https://www.python.org/downloads/)
- Install dependencies: `pip install scholarly` for windows
- Install dependencies: `pip install scholarly` for Linux

### Command-line Arguments

- `--query`: Search query. Specify the topic you want to search for.
- `--results`: Number of results to retrieve (default is 20).
- `--format`: Output format (`json` or `bibtex`, default is `json`).
- `--out`: Output file name without extension (default is `results`).
- `--api_key`: Scraper API Key (optional).
- `--api_key_file`: Path to a file containing Scraper API Key (optional).

### Example Usage

#### Basic Usage
```bash
python scholarly-cli.py --query "Machine Learning" --results 10 --format json --out machine_learning_results 
```
```
python3 test_1.py --query "GPT understands, too" --results 20 --format json --out result --api_key_file "API_KEY.txt"
```

#### Using an API key
To use the Scraper API, you need to obtain an API key from https://developer.unpaywall.org/. You can then pass this as an argument using the `--api_
If you have access to a paid API, such as Google's Academic API, you can use it with the following command:

bash


## Output

- If the output format is JSON, the results will be saved in a JSON file named `results.json` or the specified output file name.
- If the output format is BibTeX, the results will be saved in a BibTeX file named `results.bib` or the specified output file name.

## Features

- Retrieve publication data from Google Scholar.
- Supports specifying the number of results to retrieve.
- Supports output formats JSON and BibTeX.
- Option to specify Scraper API Key.

## Additional Notes

- If no API key is provided, the tool uses free proxies for accessing Google Scholar.
- The script measures and displays the execution time.
- 