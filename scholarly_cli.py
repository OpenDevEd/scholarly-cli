#!/usr/bin/env python3
import argparse
import datetime
import json
import os
from scholarly import scholarly, ProxyGenerator
import time
import requests

def gettime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def timestamp(text):
    print(gettime() + ": " + text)
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--results', type=int, default=20, help='Number of results to retrieve')
    parser.add_argument('--patents', type=bool, default=True, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--citations', type=bool, default=True, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--year_low', type=int, default=None, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--year_high', type=int, default=None, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--json', type=bool, default=True, help='Output json (default=True).')
    parser.add_argument('--ijson', type=bool, default=False, help='Output individual json files, one per result (default=False).')
    parser.add_argument('--bibtex', type=bool, default=False, help='Output bibtex (default=False).')
    parser.add_argument('--fill', type=bool, default=False, help='Fill results; requires extra queries (default=False).')
    parser.add_argument('--out', type=str, help='Output file name without extension - otherwise the search query will be used')
    parser.add_argument('--time', type=bool, default=True, help='Prefix data/time to the output file.')
    parser.add_argument('--sort_by', type=str, choices=["relevance","date"], default="relevance", help="NEEDS TO BE IMPLEMENTED. relevance or date, defaults to relevance")
    parser.add_argument('--include_last_year', type=str, choices=['abstracts','everything'], default='abstracts', help='NEEDS TO BE IMPLEMENTED. abstracts or everything, defaults to abstracts and only applies if sort_by is date')
    parser.add_argument('--start_index', type=int, default=0, help='NEEDS TO BE IMPLEMENTED.... Starting index of list of publications, defaults to 0')
    
    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('config', help='Configure API key')

    return parser.parse_args()

"""
Also support:
- citedby
- author page query
"""



def getproxy(args):
    pg = ProxyGenerator()

    # Use different ways of determining apikey:
    apikey = ""
    # Highest priority:
    timestamp("api key from file")
    apikey = read_api_key()
        
    print("API key read from file:", apikey)  # Add this line for debugging
    
    if apikey != "":
        success = pg.ScraperAPI(apikey)
        if not success:
            timestamp("Failed connecting to ScraperAPI using provided API key.")
            timestamp("Falling back to free proxies.")
            pg.FreeProxies()
            scholarly.use_proxy(pg)  # Use free proxies
    else:
        timestamp("API key not found or invalid. Using free proxies.")
        pg.FreeProxies()
        scholarly.use_proxy(pg)  # Use free proxies





# Function to retrieve additional details for a publication
def get_full_publication_details(publication):
    return scholarly.fill(publication)

# File path for storing the API key
api_key_file = os.path.expanduser("~/.config/scholarly-cli/api_key.txt")

# Function to read the API key from a file
def read_api_key():
    with open(api_key_file, 'r') as f:
        return f.read().strip()
        
# Function to prompt the user to input their API key
def ask_for_api_key():
    print("Please provide your API key: ")
    api_key = input()
    dirname = os.path.dirname(api_key_file)
    os.makedirs(dirname, exist_ok=True)
    with open(api_key_file, 'w') as f:
        f.write(api_key)
    return api_key

def main():
    start_time = time.time()

    settings = {}
    args = parse_arguments()

    # If the command is to configure API key
    if args.command == 'config':
        ask_for_api_key()
        exit(0)

    settings["time_start"] = gettime()
    settings["args"] = vars(args)

    if (not(args.json or args.ijson or args.bibtex)):
        print("No output will be produced! Use --json, --ijson or --bibtex to produce output.")

    # Registering a proxy for web scraping
    timestamp("Registering proxy:")
    getproxy(args)
    timestamp("Done!")

    outfile = ""
    if (args.out):
        outfile = f"{args.out}"
    else:
        outfile = f"{args.query}"

    if args.time:
        settings["timestamp"] = gettime().replace(':', '_')
        outfile = settings["timestamp"] + " - " + outfile


    # Determining the output file name
    timestamp("Output file name: "+outfile)

    timestamp("Querying...")
    search_query = scholarly.search_pubs(args.query)
    results = []

    timestamp("Query done! results: " + str(search_query.total_results))
    settings["total_results"] = search_query.total_results

    # Processing search results
    for i, result in enumerate(search_query):
        timestamp(str(i))
        if i >= args.results-1:
            break
        results.append(result)

    timestamp("Enumeration done!")
    settings["time_end"] = gettime()

    alljson = []
    
    # Generating JSON output
    if args.json or args.ijson:
        for i, result in enumerate(results):
            if (args.fill):
                fullresult = get_full_publication_details(result)
            else:
                fullresult = result
            if args.ijson:
                with open(f"{outfile}_{i+1}.json", 'w') as f:
                    json.dump(fullresult, f, indent=4)
            alljson.append(fullresult)
        if args.json:
            settings["results"] = alljson

        with open(f"{outfile}.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(settings, indent=4))
            
    # Generating BibTeX output
    if args.bibtex:
        bibtex_results = ""
        for i, result in enumerate(results):
            bibtex = scholarly.bibtex(result)
            filename = f"{args.out}_{i+1}.bibtex"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(bibtex)
            bibtex_results += bibtex + '\n\n'
        with open(f"{outfile}.bibtex", 'w', encoding='utf-8') as f:
            f.write(bibtex_results)

    timestamp("All done!")
    end_time = time.time()
    duration = end_time - start_time
    print(f"Script execution time: {duration} seconds")
    
#Entry point of the script
if __name__ == "__main__":
    main()