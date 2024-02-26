import argparse
import json
import os
from scholarly import scholarly, ProxyGenerator

parser = argparse.ArgumentParser()
parser.add_argument('--query', type=str, help='Search query')
parser.add_argument('--results', type=int, default=20, help='Number of results to retrieve')
parser.add_argument('--format', type=str, choices=['json', 'bibtex'], default='json', help='Output format')
parser.add_argument('--out', type=str, default='results', help='Output file name without extension')
"""
# These areguments should also be included:
parser.add_argument('--patents', type=bool, default=True, help='Fill me in.')
parser.add_argument('--citations', type=bool, default=True, help='Fill me in.')
parser.add_argument('--year_low', type=int, default=None, help='Fill me in.')
parser.add_argument('--year_high', type=int, default=None, help='Fill me in.')
parser.add_argument('sort_by (string, optional) – , help='Fill me in.'‘relevance’ or ‘date’, defaults to ‘relevance’
parser.add_argument('include_last_year (string, optional) – , help='Fill me in.'‘abstracts’ or ‘everything’, defaults to ‘abstracts’ and only applies if ‘sort_by’ is ‘date’
parser.add_argument('start_index (int, optional) – , help='Fill me in.'starting index of list of publications, defaults to 0
"""

args = parser.parse_args()

pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

search_query = scholarly.search_pubs(args.query)
results = []

for i, result in enumerate(search_query):
    if i == args.results:
        break
    results.append(result)

if args.format == 'json':
    for i, result in enumerate(results):
        with open(f"{args.out}_{i+1}.json", 'w') as f:
            json.dump(result, f, indent=4)
elif args.format == 'bibtex':
    bibtex_results = ""
    for i, result in enumerate(results):
        bibtex = scholarly.bibtex(result)
        bibtex_results += bibtex + '\n\n'

    with open(f"{args.out}.bibtex", 'w', encoding='utf-8') as f:
        f.write(bibtex_results)

# Consolidate all JSON results into a single file
all_results = []

for i in range(args.results):
    filename = f"{args.out}_{i+1}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            result_data = json.load(f)
            all_results.append(result_data)

with open('results.json', 'w') as f:
    json.dump(all_results, f, indent=4)
