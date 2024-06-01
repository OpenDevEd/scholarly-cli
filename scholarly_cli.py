#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import math
import re
import time
import uuid
import logging
from pathlib import Path
from scholarly import scholarly, ProxyGenerator

def configure_logging():
    """Configure logging settings."""
    log_file = 'script.log'
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    return logger

logger = configure_logging()

def gettime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def timestamp(text):
    logger.info(text)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--limit', type=int, default=20,
                        help='Number of results to retrieve (default=20)')
    parser.add_argument('--count', action='store_true',
                        help='Only count the number of results without processing them')
    parser.add_argument('--patents', type=bool, default=False,
                        help='Include patents in the search results.')
    parser.add_argument('--citations', type=bool, default=False,
                        help='Include citations in the search results.')
    parser.add_argument('--date', type=str, help='Date range in format year_low-year_high')
    parser.add_argument('--sort_by', type=str, choices=["relevance", "date"],
                        default="relevance", help="Sort by relevance or date, defaults to relevance")
    parser.add_argument('--sort_order', type=str, choices=[
                        "asc", "desc"], default="desc", help="Sort order: asc or desc, defaults to asc")
    parser.add_argument('--json', type=bool,
                        default=True,
                        help='Output json (default=True).')
    parser.add_argument('--ijson', action='store_true',
                        help='Output individual json files, one per result (default=False).')
    parser.add_argument('--bibtex', action='store_true',
                        help='Output bibtex (default=False).')
    parser.add_argument('--fill', action='store_true',
                        help='Fill results; requires extra queries (default=False).')
    parser.add_argument(
        '--save', type=str, help='Output file name without extension - otherwise the search query will be used')
    parser.add_argument('--time', action='store_true',
                        help='Prefix data/time to the output file.')
    parser.add_argument('--testurllength', action='store_true',
                        help='Test the length of the search query against common URL length limits')
    parser.add_argument('--chunksize', type=int,
                        help='Number of items per chunk')

    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('config', help='Configure API key')

    return parser.parse_args()

def log_additional_info(page, progress, remaining_queries, total_results, items_per_page, start_time, quota_after_search_has_finished):
    current_time = time.time()
    time_elapsed = current_time - start_time
    total_time_estimated = time_elapsed / \
        (progress / 100) if progress > 0 else 0
    time_remaining = total_time_estimated - time_elapsed
    time_remaining_formatted = format_as_time(time_remaining)
    estimated_completion_time = datetime.datetime.now(
    ) + datetime.timedelta(seconds=time_remaining)
    estimated_completion_time_iso = estimated_completion_time.isoformat()
    info_string = (
        f"Retrieving Item: {page}\n"
        f"- Progress: {progress} %\n"
        f"- Remaining duration: {time_remaining_formatted}\n"
        f"- Estimated completion time: {estimated_completion_time_iso}\n"
        f"- Query quota: {remaining_queries}\n"
        f"- Query Quota remaining after search: {quota_after_search_has_finished}\n"
    )
    logger.info(info_string)

    if quota_after_search_has_finished < 0:
        logger.warning(
            "Warning: Query quota will be exhausted before search is finished.")

def format_as_time(seconds):
    """Formats time in seconds to a human-readable format."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

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
        print("Using ScraperAPI with provided API key.")
    else:
        timestamp("API key not found or invalid. Using free proxies.")
        pg.FreeProxies()
        scholarly.use_proxy(pg)  # Use free proxies

def get_full_publication_details(publication):
    return scholarly.fill(publication)

api_key_file = os.path.expanduser("~/.config/scholarly-cli/api_key.txt")

def read_api_key():
    try:
        with open(api_key_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error("API key file not found.")
        return None

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

def create_metadata(search_query, args, total_results, searchID, queryUrl, chunk_number=None, chunk_size=None, start_time=None):
    firstItem = 1
    if chunk_size is not None:
        firstItem = (chunk_number - 1) * chunk_size + 1 if chunk_number is not None else "1"
    metadata = {
        "version": "OpenDevEd_jsonUploaderV01",
        "query": search_query,
        "searchTerm": args.search,
        "totalResults": count_results(args),
        "source": "Google Scholar",
        "sourceFormat": "original",
        "date": gettime(),
        "searchsFiled": "title_abstract",
        "resultsPerPage": chunk_size if chunk_size is not None else args.limit,
        "firstItem": firstItem,
        "startingPage": "",
        "endingPage": "",
        "filters": {
            "dateFrom": args.year_low,
            "dateTo": args.year_high
        },
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
        "numResults": chunk_size if chunk_size is not None else args.limit,
        "searchID": searchID,
        "queryUrl": queryUrl,
        "start_time": start_time,
        "end_time": gettime(),
        "args": vars(args)
    }
    return metadata

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
def count_results(args, timeout=30):
    """ Function to count results with a timeout. """
    try:
        search_query = args.search
        search_results = scholarly.search_pubs(search_query, patents=args.patents, citations=args.citations, year_low=args.year_low, year_high=args.year_high)
        result_count = search_results._get_total_results()
        formatted_count = "{:,}".format(result_count) if result_count is not None else "Unknown"
        return formatted_count
    except Exception as e:
        print(f"Error counting results: {e}")
        return None

def main():
    start_time = time.time()
    args = parse_arguments()

    if args.command == 'config':
        api_key = ask_for_api_key()
        logger.info(f"API key saved to {api_key_file}")
        return

    if not args.search:
        logger.error("Please provide a search query using --search argument.")
        return

    if args.date:
        try:
            year_low, year_high = map(int, args.date.split('-'))
            args.year_low = year_low
            args.year_high = year_high
        except ValueError:
            logger.error("Invalid date format. Please use year_low-year_high format.")
            return

    search_query = args.search
    searchID = str(uuid.uuid4())
    queryUrl = f"https://scholar.google.com/scholar?q={search_query}"

    if args.testurllength:
        test_url_length(search_query)
        return

    getproxy(args)

    search_results = scholarly.search_pubs(search_query, patents=args.patents, citations=args.citations, year_low=args.year_low, year_high=args.year_high)

    remaining_queries = 20000  # Example initial value, replace with actual value

    total_number_of_items = args.limit
    total_results_estimated = 0

    if args.count:
        count = count_results(args)
        print(f"Total number of results: {count}")
        return

    items_retrieved = 0
    retrieved_results = []
    items_in_chunk = 0
    chunk_number = -1

    for result in search_results:
        items_retrieved += 1
        items_in_chunk += 1

        if items_retrieved > total_number_of_items:
            break

        remaining_queries -= 1

        if args.fill:
            result = get_full_publication_details(result)

        retrieved_results.append(result)
        total_results_estimated += 1  # Increment total results estimate

        if args.chunksize and items_in_chunk >= args.chunksize:
            chunk_number += 1
            write_data(args, search_query, start_time, total_results_estimated, searchID, queryUrl, chunk_number, retrieved_results)
            retrieved_results = []
            items_in_chunk = 0

        progress = round((items_retrieved / total_number_of_items) * 100)
        log_additional_info(items_retrieved, progress, remaining_queries, total_results_estimated, 10, start_time, remaining_queries)

    if retrieved_results:
        if args.chunksize is not None:
            chunk_number += 1
        write_data(args, search_query, start_time, total_results_estimated, searchID, queryUrl, chunk_number, retrieved_results)

    if not (args.json or args.ijson or args.bibtex):
        logger.error("No output will be produced! Use --json, --ijson or --bibtex to specify output format.")
        return

    settings = {
        "time_start": gettime(),
        "args": vars(args),
        "sort_by": args.sort_by
    }
    settings["time_end"] = gettime()
    elapsed_time = time.time() - start_time
    logger.info(f"Script executed in {elapsed_time:.2f} seconds.")
    logger.info("Script execution completed.")


def write_data(args, search_query, start_time, total_results, searchID, queryUrl, chunk_number, result):
    if args.json:
        output_data = {
            "meta": create_metadata(search_query, args, total_results, searchID, queryUrl, chunk_number, args.chunksize, start_time),
            "results": result
        }
        if chunk_number > -1:
            output_filename = f"{args.save if args.save else args.search}_{chunk_number}.json"
            save_to_json(output_data, output_filename)
            logger.info(f"Chunk {chunk_number} saved to {output_filename}")
        else:
            output_filename = f"{args.save if args.save else args.search}.json"
            save_to_json(output_data, output_filename)
            logger.info(f"Results saved to {output_filename}")

    if args.ijson:
        for i, result in enumerate(result):
            output_data = {
                "meta": create_metadata(search_query, args, total_results, searchID, queryUrl, chunk_number, args.chunksize, start_time),
                "results": [result]
            }
            output_filename = f"{args.save if args.save else args.search}_{i+1}.json"
            save_to_json(output_data, output_filename)
            logger.info(f"Individual result saved to {output_filename}")

if __name__ == "__main__":
    main()
