"""
Process passport-index-dataset CSV into compact JSON for VisaPathway.
Outputs:
  - visa-matrix.json: {passport: {destination: requirement}}
  - countries.json: sorted list of country names
  - residence-permits.json: manually curated residence permit exemptions
"""
import csv
import json
import os

INPUT_CSV = os.path.join(os.path.dirname(__file__), '..', '..', 'passport-index-data', 'passport-index-tidy.csv')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Process visa matrix
matrix = {}
countries = set()

with open(INPUT_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        passport = row['Passport']
        destination = row['Destination']
        requirement = row['Requirement']

        countries.add(passport)
        countries.add(destination)

        if passport not in matrix:
            matrix[passport] = {}

        # Normalize values to short codes for smaller file size
        # Numbers = visa-free days, vr = visa required, voa = visa on arrival,
        # ev = e-visa, vf = visa free, eta = electronic travel authorization
        req = requirement.strip().lower()
        if req == 'visa required':
            matrix[passport][destination] = 'vr'
        elif req == 'visa on arrival':
            matrix[passport][destination] = 'voa'
        elif req == 'e-visa':
            matrix[passport][destination] = 'ev'
        elif req == 'visa free':
            matrix[passport][destination] = 'vf'
        elif req == 'eta':
            matrix[passport][destination] = 'eta'
        elif req == 'no admission' or req == '-1':
            matrix[passport][destination] = 'na'
        else:
            # Try to parse as number (visa-free days)
            try:
                days = int(req)
                matrix[passport][destination] = days
            except ValueError:
                matrix[passport][destination] = req

sorted_countries = sorted(countries)

# Write visa matrix
with open(os.path.join(OUTPUT_DIR, 'visa-matrix.json'), 'w', encoding='utf-8') as f:
    json.dump(matrix, f, separators=(',', ':'))

# Write countries list
with open(os.path.join(OUTPUT_DIR, 'countries.json'), 'w', encoding='utf-8') as f:
    json.dump(sorted_countries, f, separators=(',', ':'))

# Residence permit / additional visa exemptions
# IMPORTANT: Only add entries that have been verified from official
# government immigration authority websites. Each entry MUST have a
# verified source URL and must apply to ALL passport holders with
# that document, OR be structured as nationality-specific rules.
# TEMPORARILY EMPTY — all permit/visa exemption data has been removed
# because it was not properly verified and showed incorrect results.
#
# The correct approach: research each destination country's official
# immigration rules for each passport+document combination individually.
# This is a manual research task that will be done country-by-country.
#
# The UI still shows the permit/visa selection options, but they won't
# affect results until verified data is added back.
residence_permits = {
    "UAE Residence Permit": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}},
    "US Green Card (Permanent Resident)": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}},
    "Schengen Residence Permit": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}},
    "UK Residence Permit (BRP)": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}},
    "Canada Permanent Resident": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}},
    "Valid US Visa (B1/B2)": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}},
    "Valid Schengen Visa": {"source": "Pending verification", "last_verified": "Not yet verified", "exemptions": {}}
}

with open(os.path.join(OUTPUT_DIR, 'residence-permits.json'), 'w', encoding='utf-8') as f:
    json.dump(residence_permits, f, indent=2)

print(f"Processed {len(matrix)} passports x {len(sorted_countries)} countries")
print(f"Visa matrix: {os.path.getsize(os.path.join(OUTPUT_DIR, 'visa-matrix.json')) / 1024:.0f} KB")
print(f"Countries: {len(sorted_countries)}")
print(f"Residence permits: {len(residence_permits)} permit types")
