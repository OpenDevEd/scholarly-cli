#!/usr/bin/python3
import argparse
import datetime
import json
import os
from scholarly import scholarly, ProxyGenerator

def gettime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def timestamp(text):
    print(gettime() + ": " + text)
    return

parser = argparse.ArgumentParser()
parser.add_argument('--query', type=str, help='Search query', required=True)
parser.add_argument('--results', type=int, default=20, help='Number of results to retrieve')
#parser.add_argument('--format', type=str, choices=['json', 'bibtex'], default='json', help='Output format')
parser.add_argument('--json', type=bool, default=True, help='Output json (default=True).')
parser.add_argument('--ijson', type=bool, default=False, help='Output individual json files, one per result (default=False).')
parser.add_argument('--bibtex', type=bool, default=False, help='Output bibtex (default=False).')
parser.add_argument('--out', type=str, help='Output file name without extension - otherwise the search query will be used')
parser.add_argument('--time', type=bool, default=True, help='Prefix data/time to the output file.')

"""
# These areguments should also be included:
parser.add_argument('--patents', type=bool, default=True, help='Fill me in.')
parser.add_argument('--citations', type=bool, default=True, help='Fill me in.')
parser.add_argument('--year_low', type=int, default=None, help='Fill me in.')
parser.add_argument('--year_high', type=int, default=None, help='Fill me in.')
parser.add_argument('sort_by (string, optional) – , help='Fill me in.'‘relevance’ or ‘date’, defaults to ‘relevance’
parser.add_argument('include_last_year (string, optional) – , help='Fill me in.'‘abstracts’ or ‘everything’, defaults to ‘abstracts’ and only applies if ‘sort_by’ is ‘date’
parser.add_argument('start_index (int, optional) – , help='Fill me in.'starting index of list of publications, defaults to 0

Also support:
- fill
- citedby
"""


settings = {}
args = parser.parse_args()
settings["time_start"] = gettime()
settings["args"] = vars(args)

if (not(args.json or args.bibtex)):
    print("No output will be produced! Use --json or --bibtex to produce output.")

if not args.json and args.ijson:
    print("For --ijson to work, please do not turn off --json.")
    exit()

timestamp("Registering proxy:")

scraperapifile = ""
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

pg = ProxyGenerator()

# check whether scraperapi has the key called key
if "key" in scraperapi:
    success = pg.ScraperAPI(scraperapi["key"])
    if not success:
        timestamp("failed connecting to scraperapi!")
        exit()
    else:  
        timestamp("connected to scraperapi!")
else:
    timestamp("Free proxy will be registered!")
    pg.FreeProxies()
    
scholarly.use_proxy(pg)

outfile = ""
if (args.out):
    outfile = f"{args.out}"
else:
    outfile = f"{args.query}"

if (args.time):
    settings["timestamp"] = gettime()
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

if args.json:
    for i, result in enumerate(results):
        if args.ijson:
            with open(f"{outfile}_{i+1}.json", 'w') as f:
                json.dump(result, f, indent=4)
        alljson.append(result)
    settings["results"] = alljson
    with open(f"{outfile}.json", 'w') as f:
        json.dump(settings, f, indent=4)
else:
    with open(f"{outfile}.settings.json", 'w', encoding='utf-8') as f:
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