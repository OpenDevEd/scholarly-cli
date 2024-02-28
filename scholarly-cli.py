#!/usr/bin/python3
import argparse
import datetime
import json
import os
from scholarly import scholarly, ProxyGenerator
import time
#import requests

def gettime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def timestamp(text):
    print(gettime() + ": " + text)
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, help='Search query', required=True)
    parser.add_argument('--results', type=int, default=20, help='Number of results to retrieve')
    parser.add_argument('--patents', type=bool, default=True, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--citations', type=bool, default=True, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--year_low', type=int, default=None, help='NEDS TO BE IMPLEMENTED.')
    parser.add_argument('--year_high', type=int, default=None, help='NEDS TO BE IMPLEMENTED.')
    # We may want both json and bibtex, hence using separate options.
    # Let's not use this:
    #parser.add_argument('--format', type=str, choices=['json', 'bibtex'], default='json', help='Output format')
    # But use this:
    parser.add_argument('--json', type=bool, default=True, help='Output json (default=True).')
    parser.add_argument('--ijson', type=bool, default=False, help='Output individual json files, one per result (default=False).')
    parser.add_argument('--bibtex', type=bool, default=False, help='Output bibtex (default=False).')
    parser.add_argument('--fill', type=bool, default=False, help='Fill results; requires extra queries (default=False).')
    parser.add_argument('--out', type=str, help='Output file name without extension - otherwise the search query will be used')
    parser.add_argument('--time', type=bool, default=True, help='Prefix data/time to the output file.')
    parser.add_argument('--apikey', type=str, help='Scraper API Key')
    parser.add_argument('--apikeyfile', type=str, help='Path to file containing Scraper API Key')
    parser.add_argument('--sort_by', type=str, choices=["relevance","date"], default="relevance", help="NEEDS TO BE IMPLEMENTED. relevance or date, defaults to relevance")
    parser.add_argument('--include_last_year', type=str, choices=['abstracts','everything'], default='abstracts', help='NEEDS TO BE IMPLEMENTED. abstracts or everything, defaults to abstracts and only applies if sort_by is date')
    parser.add_argument('--start_index', type=int, default=0, help='NEEDS TO BE IMPLEMENTED.... Starting index of list of publications, defaults to 0')
    return parser.parse_args()

"""
Also support:
- citedby
- author page query
"""

def read_api_key(api_key, api_key_file):
    if api_key_file:
        with open(api_key_file, 'r') as f:
            return f.read().strip()
    else:
        return api_key

def getproxy(args):
    pg = ProxyGenerator()
    # Use different ways of determining apikey:
    apikey = ""
    # Highest priority:
    if "apikey" in args and args.apikey:
        timestamp("api key from argument: "+str(args.apikey))
        apikey = args.apikey
    else:
        timestamp("api key from file")
        # If note via --apikey, then use files:
        scraperapifile = ""
        if "apikeyfile" in args and args.apikeyfile:
            if os.path.exists(args.apikeyfile):
                scraperapifile = args.apikeyfile
            else:
                print(f"{args.apikeyfile} does not exist!")
                exit()
        else:
            # If not using --apikeyfile, then look on files system:
            home = os.path.expanduser("~")
            if os.path.exists("scraperapi.json"):
                scraperapifile = "scraperapi.json"
            elif os.path.exists(home + "/.config/scraperapi/scraperapi.json"):
                scraperapifile = home + "/.config/scraperapi/scraperapi.json"

        # check wethere there is a file called scraperapi.json
        if os.path.exists(scraperapifile):
            with open(scraperapifile, 'r') as f:
                scraperapi = json.load(f)
        else:
            scraperapi = {}

        # check whether scraperapi has the key called key
        if "key" in scraperapi:
            apikey = scraperapi["key"]
        
    if apikey != "":    
       # try:            
        success = pg.ScraperAPI(apikey)
        #except requests.exceptions.RequestException as e:
        #    print(f"Error setting up proxy: {e}")
        #    exit()
        # This seems to be the recommended way:
        if not success:
            timestamp("failed connecting to scraperapi!")
            exit()
        else:  
            timestamp("connected to scraperapi!")    
    else:
        timestamp("Free proxy will be registered!")
        pg.FreeProxies()
            
    scholarly.use_proxy(pg)

def get_full_publication_details(publication):
    return scholarly.fill(publication)

def main():
    start_time = time.time()

    settings = {}
    args = parse_arguments()
    settings["time_start"] = gettime()
    settings["args"] = vars(args)

    if (not(args.json or args.ijson or args.bibtex)):
        print("No output will be produced! Use --json, --ijson or --bibtex to produce output.")

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



    timestamp("Output file name: "+outfile)

    timestamp("Querying...")
    search_query = scholarly.search_pubs(args.query)
    results = []

    timestamp("Query done! results: " + str(search_query.total_results))
    settings["total_results"] = search_query.total_results

    for i, result in enumerate(search_query):
        timestamp(str(i))
        if i >= args.results-1:
            break
        results.append(result)

    timestamp("Enumeration done!")
    settings["time_end"] = gettime()

    alljson = []

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

if __name__ == "__main__":
    main()