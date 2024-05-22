#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import re
from pathlib import Path
from scholarly import scholarly, ProxyGenerator
import time
import requests

import threading

def count_results(search_query, timeout=30):
    """ Function to count results with a timeout. """
    try:
        search_results = scholarly.search_pubs(search_query)
        result_count = 0
        for _ in search_results:
            result_count += 1
            if result_count > 1000:  # Set a reasonable limit to prevent infinite loops
                print("Warning: Stopping count at 1000 for performance reasons.")
                break
        return result_count
    except Exception as e:
        print(f"Error counting results: {e}")
        return None
    
def sanitise(input_string):
    return input_string.strip().replace("'", "").replace('"', '')

def quote_if_needed(term):
    if " " in term:
        return f'"{term}"'
    return term

def search_builder(query):
    search_query = ''
    for item in query.split():
        match = re.search(r'(\w+)\.\.\.', item)
        if match:
            key = match.group(1)
            file_path = Path(f'./scholarly-cli/searchterms/{key}.txt')
            print(file_path)
            if not file_path.exists():
                file_path = Path.home() / f'.config/openalex-cli/searchterms/{key}.txt'
                print(file_path)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as file:
                    result = file.read()
            else:
                result = key
            result_arr = result.splitlines()
            result = ''
            operator = ''
            use_operator = False
            for line in result_arr:
                comment_match = re.search(r'#(OR|AND)\s*$', line)
                if comment_match:
                    operator = f"{comment_match.group(1)} "
                    use_operator = True
                if re.search(r'#(-)\s*$', line):
                    use_operator = True
                    operator = ' '
                term = sanitise(re.sub(r'#.+$', '', line))
                if term:
                    result += (operator if re.search(r'[\w")]\s+$', result) and not re.search(r'^\s*\)', term) else '') + (quote_if_needed(term) if use_operator else term) + " "
            result = re.sub(rf'{key}\.\.\.', result, item)
            search_query += f" {result}"
        else:
            search_query += f" {quote_if_needed(item)}"
    search_query = re.sub(r'\[', '(', search_query)
    search_query = re.sub(r'\]', ')', search_query)
    print(search_query)
    return search_query.strip()

def gettime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def timestamp(text):
    print(gettime() + ": " + text)
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--results', type=int, default=20, help='Number of results to retrieve')
    parser.add_argument('--count', action='store_true', help='Only count the number of results without processing them')
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
    parser.add_argument('--sort_by', type=str, choices=["relevance","date"], default="relevance", help="Sort by relevance or date, defaults to relevance")
    parser.add_argument('--sort_order', type=str, choices=["asc","desc"], default="asc", help="Sort order: asc or desc, defaults to asc")
    parser.add_argument('--testurllength', action='store_true', help='Test the length of the search query against common URL length limits')

    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('config', help='Configure API key')

    return parser.parse_args()

def test_url_length(search_query):
    url_length = len(search_query)
    print(f"Search query length: {url_length} characters")
    
    # Common URL length limits for web technologies
    browser_limit = 2**11
    nginx_limit = 2**12
    apache_limit = 2**13
    
    print(f"Browser URL length limit: {browser_limit} characters")
    print(f"Nginx URL length limit: {nginx_limit} characters")
    print(f"Apache URL length limit: {apache_limit} characters")
    
    if url_length > browser_limit:
        print("Warning: Search query exceeds browser URL length limit!")
    if url_length > nginx_limit:
        print("Warning: Search query exceeds Nginx URL length limit!")
    if url_length > apache_limit:
        print("Warning: Search query exceeds Apache URL length limit!")

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

def chunk_list(iterable, chunk_size):
    """Yield successive chunks from the iterable."""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

def main():
    start_time = time.time()

    settings = {}
    args = parse_arguments()

    print("Parsed arguments:", args)  # Debugging line to see all parsed arguments

    if args.testurllength:
        search_query = search_builder(args.search)
        test_url_length(search_query)
        return
    
    if args.count:
        search_query = search_builder(args.search)
        # Start a thread to count results with a timeout
        result_count = None
        count_thread = threading.Thread(target=lambda: count_results(search_query))
        count_thread.start()
        count_thread.join(timeout=30)  # Timeout after 30 seconds
        if count_thread.is_alive():
            print("Timeout reached while counting results.")
        else:
            print(f"Total number of results: {result_count}")
        return
    # If the command is to configure API key
    if args.command == 'config':
        ask_for_api_key()
        exit(0)

    settings["time_start"] = gettime()
    settings["args"] = vars(args)

    if (not(args.json or args.ijson or args.bibtex)):
        print("No output will be produced! Use --json, --ijson or --bibtex to specify output format.")
        exit(0)
        
    search_query = search_builder(args.search)
    print("search_query=", search_query)

    settings["search"] = search_query

    # Check if an API key is already configured
    if not os.path.exists(api_key_file):
        # Prompt the user to input their API key
        ask_for_api_key()

    # Fetch publications and process them
    getproxy(args)
    search_query = scholarly.search_pubs(search_query)

    counter = 0
    results = []
    while counter < args.results:
        try:
            publication = next(search_query)
            results.append(publication)
            counter += 1
        except StopIteration:
            break
        except Exception as e:
            print(f"Error retrieving publication: {e}")
            break

    # Sort the results based on the specified criteria
    if args.sort_by == 'date':
        results.sort(key=lambda x: x.get('pub_year', 0), reverse=(args.sort_order == 'desc'))
    elif args.sort_by == 'relevance':
        # Implement relevance sorting if needed
        pass

    settings["results"] = results

    out = args.out if args.out else re.sub(r'\W+', '_', search_query)
    filename = f"{out}_results"

    if args.time:
        filename = f"{gettime()}_{filename}"

    if args.json:
        with open(f"{filename}.json", 'w') as f:
            json.dump(results, f, indent=4)

    if args.ijson:
        for i, result in enumerate(results):
            with open(f"{filename}_{i}.json", 'w') as f:
                json.dump(result, f, indent=4)

    if args.bibtex:
        bibtex_str = ""
        for result in results:
            bibtex_str += scholarly.bibtex(result) + "\n"
        with open(f"{filename}.bib", 'w') as f:
            f.write(bibtex_str)

    timestamp("Data written to " + filename)
    settings["time_end"] = gettime()

    elapsed_time = time.time() - start_time
    timestamp(f"Script executed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()
