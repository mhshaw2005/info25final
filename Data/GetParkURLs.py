import json
import requests

# settings
save_file = "USNP_Park_URLs.json"

# the sparql query to get parks with visitor data
query = """
SELECT ?park ?parkLabel ?visitors
WHERE {
  ?park wdt:P31 wd:Q34918903.  # instance of US National Park
  ?park wdt:P1174 ?visitors.    # has visitor data
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""

# query wikidata
print("Getting US National Parks from Wikidata...")
response = requests.get(
    "https://query.wikidata.org/sparql",
    params={'format': 'json', 'query': query},
)

data = response.json()
results = data['results']['bindings']
print(f"Got {len(results)} results")

# extract park info
parks = []
seen_names = {}  # for deduplication

for item in results:
    # get the basic info
    park_id = item['park']['value'].split('/')[-1]
    park_name = item['parkLabel']['value']
    park_url = f"https://www.wikidata.org/wiki/{park_id}"
    
    # deduplication: strip common words and check if we've seen this park
    simple_name = park_name.lower().replace('national', '').replace('park', '').strip()
    
    # if we've seen a similar name, skip it
    if simple_name in seen_names:
        print(f"Skipping duplicate: {park_name}")
        continue
    
    seen_names[simple_name] = True
    
    parks.append({
        'name': park_name,
        'id': park_id,
        'url': park_url
    })

# sort by name
parks.sort(key=lambda x: x['name'])

# print them out
print(f"\nFound {len(parks)} unique parks:\n")
for i, park in enumerate(parks, 1):
    print(f"{i}. {park['name']} ({park['id']})")

# save to json
with open(save_file, 'w') as f:
    json.dump({'parks': parks, 'total': len(parks)}, f, indent=2)

print(f"\nSaved to {save_file}")
