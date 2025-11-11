import csv
import os
from collections import Counter

props_file = 'Models/10-ARBITRAGE/data/week10_props_2025-11-09.csv'

if not os.path.exists(props_file):
    print(f"File not found: {props_file}")
    exit(1)

sportsbooks = []
with open(props_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sportsbooks.append(row['bookmaker'])

unique_sportsbooks = sorted(set(sportsbooks))
counts = Counter(sportsbooks)

print("=" * 80)
print("UNIQUE SPORTSBOOKS SCRAPED FROM THE-ODDS-API.COM")
print("=" * 80)
print(f"\nTotal unique sportsbooks: {len(unique_sportsbooks)}\n")
print("List of all unique sportsbooks:")
for i, book in enumerate(unique_sportsbooks, 1):
    print(f"  {i:2d}. {book}")

print(f"\n\nCount per sportsbook:")
for book, count in sorted(counts.items()):
    print(f"  {book:30s}: {count:5d} props")
