#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import re
import time
import uuid
from pathlib import Path
from scholarly import scholarly, ProxyGenerator

def count_results(search_query, timeout=30):
    """ Function to count results with a timeout. """
    try:
        search_results = scholarly.search_pubs(search_query)
        result_count = 0
        start_time = time.time()
        for _ in search_results:
            result_count += 1
            if time.time() - start_time > timeout:
                print("Timeout reached while counting results.")
                return result_count
            if result_count > 10000:  # Set a reasonable limit to prevent infinite loops
                print("Warning: Stopping count at 10000 for performance reasons.")
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
            if not file_path.exists():
                file_path = Path.home() / f'.config/openalex-cli/searchterms/{key}.txt'
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
    parser.add_argument('--json', action='store_true', help='Output json (default=True).')
    parser.add_argument('--ijson', action='store_true', help='Output individual json files, one per result (default=False).')
    parser.add_argument('--bibtex', action='store_true', help='Output bibtex (default=False).')
    parser.add_argument('--fill', action='store_true', help='Fill results; requires extra queries (default=False).')
    parser.add_argument('--out', type=str, help='Output file name without extension - otherwise the search query will be used')
    parser.add_argument('--time', action='store_true', help='Prefix data/time to the output file.')
    parser.add_argument('--sort_by', type=str, choices=["relevance","date"], default="relevance", help="Sort by relevance or date, defaults to relevance")
    parser.add_argument('--sort_order', type=str, choices=["asc","desc"], default="desc", help="Sort order: asc or desc, defaults to asc")
    parser.add_argument('--testurllength', action='store_true', help='Test the length of the search query against common URL length limits')
    parser.add_argument('--chunks', type=int, help='Number of results per chunk')

    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('config', help='Configure API key')

    return parser.parse_args()

def test_url_length(search_query):
    query_length = len(search_query)
    base_url = "https://scholar.google.com/scholar?q="
    full_url_length = len(base_url) + query_length

    print(f"Search query length: {query_length} characters")
    print(f"Full URL length: {full_url_length} characters")
    print(f"Limit: 2048")

    if query_length > 2048:
        print("Warning: The search query is too long and may exceed URL length limits.")

    full_url = base_url + search_query
    print("Full URL:", full_url)

    if full_url_length > 2048:
        print("Warning: The full URL exceeds the typical maximum length of 2048 characters for URLs.")

def getproxy(args):
    pg = ProxyGenerator()
    timestamp("api key from file")
    apikey = read_api_key()
    print("API key read from file:", apikey)  # Debugging line

    if apikey:
        success = pg.ScraperAPI(apikey)
        if not success:
            print("API key:", apikey)  # Debugging line
            timestamp("Failed connecting to ScraperAPI using provided API key.")
            # timestamp("Falling back to free proxies.")
            pg.FreeProxies()
            scholarly.use_proxy(pg)  # Use free proxies
            timestamp("Falling back to free proxies.")
        scholarly.use_proxy(pg)
        timestamp("Falling back to free proxies.")
    else:
        timestamp("API key not found or invalid. Using free proxies.")
        pg.FreeProxies()
        scholarly.use_proxy(pg)  # Use free proxies

def get_full_publication_details(publication):
    return scholarly.fill(publication)

api_key_file = os.path.expanduser("~/.config/scholarly-cli/api_key.txt")

def read_api_key():
    with open(api_key_file, 'r') as f:
        return f.read().strip()
        
def ask_for_api_key():
    print("Please provide your API key: ")
    api_key = input()
    dirname     = os.path.dirname(api_key_file)
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

def create_metadata(search_query, args, total_results, searchID, queryUrl, chunk_number=None, chunk_size=None):
    metadata = {
        "version": "OpenDevEd_jsonUploaderV01",
        "query": search_query,
        "searchTerm": args.search,
        "totalResults": total_results if total_results is not None else "Unknown",
        "source": "Google Scholar",
        "sourceFormat": "original",
        "date": gettime(),
        "searchsFiled": "title_abstract",
        "page": chunk_number if chunk_number is not None else "1",
        "resultsPerPage": chunk_size if chunk_size is not None else args.results,
        "firstItem": (chunk_number - 1) * chunk_size + 1 if chunk_number is not None else "1",
        "startingPage": "",
        "endingPage": "",
        "filters": {
            "dateFrom": args.year_low,
            "dateTo": args.year_high
        },
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
        "numResults": chunk_size if chunk_size is not None else args.results,
        "searchID": searchID,
        "queryUrl": queryUrl
    }
    return metadata

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    start_time = time.time()
    args = parse_arguments()

    if args.command == 'config':
        api_key = ask_for_api_key()
        print(f"API key saved to {api_key_file}")
        return

    if not args.search:
        print("Please provide a search query using --search argument.")
        return

    search_query = search_builder(args.search)
    searchID = str(uuid.uuid4())
    queryUrl = f"https://scholar.google.com/scholar?q={search_query}"
    
    if args.testurllength:
        test_url_length(search_query)
        return

    getproxy(args)

    if args.count:
        total_results = count_results(search_query)
        print(f"Total results for '{args.search}': {total_results}")
        return

    search_results = scholarly.search_pubs(search_query)
    # print the search results length
    
    
    # total_results = count_results(search_query)
    # print(f"Total results for '{args.search}': {total_results}")

    retrieved_results = []
    for i, result in enumerate(search_results):
        if i >= args.results:
            break
        if args.fill:
            result = get_full_publication_details(result)
            
        result["time_start"] = start_time
        result["args"] = vars(args)
        result["timestamp"] = gettime()
        result["time_end"] = gettime()

        
        retrieved_results.append(result)
    
    # Sorting based on args.sort_by
    try:
        if args.sort_by == "relevance":
            retrieved_results.sort(key=lambda x: x['num_citations'], reverse=((args.sort_order == 'desc')))
        elif args.sort_by == "date":
            retrieved_results.sort(key=lambda x: x.get('pub_year', 0), reverse=(args.sort_order == 'desc'))
    except KeyError:
        print("The specified sort key is not found in the search results. Falling back to sorting by date.")


    if not (args.json or args.ijson or args.bibtex):
        print("No output will be produced! Use --json, --ijson or --bibtex to specify output format.")
        return

    if args.json:
        if args.chunks:
            for chunk_number, chunk in enumerate(chunk_list(retrieved_results, args.chunks), start=1):
                output_data = {
                    "meta": create_metadata(search_query, args, None, searchID, queryUrl, chunk_number, args.chunks),
                    "time_start": start_time,
                    "args": vars(args),
                    "timestamp": gettime(),
                    "time_end": gettime(),
                    "results": chunk
                }
                output_filename = f"{args.out if args.out else args.search}_{chunk_number}.json"
                save_to_json(output_data, output_filename)
                print(f"Chunk {chunk_number} saved to {output_filename}")
        else:
            output_data = {
                "meta": create_metadata(search_query, args, None, searchID, queryUrl),
                "time_start": start_time,
                "args": vars(args),
                "timestamp": gettime(),
                "time_end": gettime(),
                "results": retrieved_results
            }
            output_filename = f"{args.out if args.out else args.search}.json"
            save_to_json(output_data, output_filename)
            print(f"Results saved to {output_filename}")

    if args.ijson:
        for i, result in enumerate(retrieved_results):
            output_data = {
                "meta": create_metadata(search_query, args, None, searchID, queryUrl, chunk_number=i+1, chunk_size=1),
                "time_start": start_time,
                "args": vars(args),
                "timestamp": gettime(),
                "time_end": gettime(),
                "results": [result]
            }
            output_filename = f"{args.out if args.out else args.search}_{i+1}.json"
            save_to_json(output_data, output_filename)
            print(f"Individual result saved to {output_filename}")

    settings = {
        "time_start": gettime(),
        "args": vars(args),
        "sort_by": args.sort_by
    }

    settings["time_end"] = gettime()
    elapsed_time = time.time() - start_time
    timestamp(f"Script executed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()
