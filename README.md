# Scholarly CLI

This is a command-line tool (`scholarly-cli.py`) built using Python to interact with Google Scholar and retrieve publication data based on a user query.

## Usage

### Prerequisites
- Python 3.x installed on your machine (https://www.python.org/downloads/)
- Here's how to install python : https://kinsta.com/knowledgebase/install-python/
- Here's how to install Git : https://kinsta.com/knowledgebase/install-git/
- Install dependencies: `pip install scholarly` for windows
- Install dependencies: `pip3 install scholarly` for Linux

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
python scholarly-cli.py --query "Attention is all you need" --results 10 --json True --bibtex True --out results 
```
```bash
python3 scholarly-cli.py --query "Attention is all you need" --results 10 --json True --bibtex True --out results 
```


#### Using an API key
To use the Scraper API, you need to obtain an API key from https://developer.unpaywall.org/. You can then pass this as an argument using the `--api_
If you have access to a paid API, such as Google's Academic API, you can use it with the following command:

#### For Linux
```bash
python3 scholarly-cli.py --query "Definition of artificial neural networks with comparison to other networks" --results 20 --json True --bibtex True --out result --api_key_file "API_KEY.txt"
```
#### For Windows
```bash
python scholarly-cli.py --query "Definition of artificial neural networks with comparison to other networks" --results 20 --json True --bibtex True --out result --api_key_file "API_KEY.txt"
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