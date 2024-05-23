# Scholarly CLI

This is a command-line tool (`scholarly-cli.py`) built using Python to interact with Google Scholar and retrieve publication data based on a user query.

## Usage

### Prerequisites
- Python 3.x installed on your machine (https://www.python.org/downloads/)
- Here's how to install python : https://kinsta.com/knowledgebase/install-python/
- Here's how to install Git : https://kinsta.com/knowledgebase/install-git/
- Install dependencies (https://github.com/scholarly-python-package/scholarly):
-- `pip install scholarly` for windows 
-- `pip3 install scholarly` for Linux

### Installation

- Clone the repository:
```bash
git clone https://github.com/OpenDevEd/scholarly-cli.git
```
- Navigate to the project directory:
```bash
cd scholarly-cli
```
- Install the script:
```bash
pip3 install -e .
```
- Run the script:
```bash
scholarly-cli --help
```

### Command-line Arguments

- `--query`: Search query. Specify the topic you want to search for.
- `--results`: Number of results to retrieve (default is 20).
- `--patents`: Specifies whether you want to include patents in the results (True or False).
- `--citations`: Specifies whether you want to include citations in the results (True or False).
- `--format`: Output format (`json` or `bibtex`, default is `json`).
    
    The --bibtex command triggers additional queries to complete publication metadata. If data is incomplete, detailed information is fetched, leading to extra network requests and processing. Upon completion, data is converted and formatted for BibTeX.
- `--out`: Output file name without extension (default is `results`).
- `--api_key`: Scraper API Key (optional).
- `--api_key_file`: Path to a file containing Scraper API Key (optional).

### Example Usage

#### Basic Usage
```bash
python scholarly-cli.py --search "Attention is all you need" --results 10 --json True --bibtex True --out results 
```
```bash
python3 scholarly-cli.py --search "Attention is all you need" --results 10 --json True --bibtex True --out results 
```
scholarly-cli --search "techhigh_v1..." --results 100 --json --out results --sort_by relevance --sort_order desc --year_low 2011 --year_high 2023 --chunks 10

#### Using an API key
To use the Scraper API, you need to obtain an API key from https://developer.unpaywall.org/. You can then pass this as an argument using the `--api_
If you have access to a paid API, such as Google's Academic API, you can use it with the following command:

#### For Linux
```bash
scholarly-cli --search "Attention is all you need" --results 10 --json True --bibtex True --out results --sort_by date --sort_order desc --year_l
ow 2010 --year_high 2010
```
#### For Windows
```bash
python scholarly-cli.py --search "Definition of artificial neural networks with comparison to other networks" --results 20 --json True --bibtex True --out result --api_key_file "API_KEY.txt"
```          

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
- The API key can be found in the file specified by API_KEY.txt
- For more informations just write `‘scholarly-cli.py —help’` will show you help.