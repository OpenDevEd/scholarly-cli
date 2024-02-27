import argparse
import json
import os
from scholarly import scholarly, ProxyGenerator
import time
import requests

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--results', type=int, default=20, help='Number of results to retrieve')
    parser.add_argument('--format', type=str, choices=['json', 'bibtex'], default='json', help='Output format')
    parser.add_argument('--out', type=str, default='results', help='Output file name without extension')
    parser.add_argument('--api_key', type=str, help='Scraper API Key')
    parser.add_argument('--api_key_file', type=str, help='Path to file containing Scraper API Key')

    return parser.parse_args()

def read_api_key(api_key, api_key_file):
    if api_key_file:
        with open(api_key_file, 'r') as f:
            return f.read().strip()
    else:
        return api_key

def get_full_publication_details(publication):
    return scholarly.fill(publication)

def main():
    start_time = time.time()

    args = parse_arguments()

    api_key = read_api_key(args.api_key, args.api_key_file)  

    pg = ProxyGenerator()
    if api_key:
        try:
            pg.ScraperAPI(api_key)
        except requests.exceptions.RequestException as e:
            print(f"Error setting up proxy: {e}")
            return
    else:
        print("No API key provided. Using free proxies.")
        pg.FreeProxies()

    scholarly.use_proxy(pg)

    search_query = scholarly.search_pubs(args.query)
    results = []

    print("Start looking for publications in Google Scholar for the query:", args.query)
    for i, publication in enumerate(search_query):
        print("Retrieving publication", i + 1, "of", args.results)
        if i == args.results - 1:
            break
        full_publication = get_full_publication_details(publication)
        results.append(full_publication)

    if args.format == 'json':
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=4)
    elif args.format == 'bibtex':
        bibtex_results = ""
        for result in results:
            bibtex = scholarly.bibtex(result)
            bibtex_results += bibtex + '\n\n'
        with open('results.bib', 'w', encoding='utf-8') as f:
            f.write(bibtex_results)

    end_time = time.time()
    duration = end_time - start_time
    print(f"Script execution time: {duration} seconds")

if __name__ == "__main__":
    main()
