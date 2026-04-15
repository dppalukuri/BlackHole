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
# VERIFIED DATA — researched April 2026 from official immigration sources.
# Each entry applies to ALL nationalities holding the document unless noted.
# UAE Residence Permit has NO verified universal exemptions for any country.
residence_permits = {
    "UAE Residence Permit": {
        "source": "Official government sources — geoconsul.gov.ge, mfa.am, evisa.gov.az",
        "last_verified": "April 2026",
        "exemptions": {
            "Georgia": {"access": "vf", "days": 90, "source": "https://uae.mfa.gov.ge/en/visa-information", "note": "Permit must be valid 1+ year on arrival. 17 nationalities (Pakistan, Afghanistan, Bangladesh, Nigeria, etc.) face stricter screening — verify at geoconsul.gov.ge"},
            "Armenia": {"access": "vf", "days": 180, "source": "https://www.mfa.am", "note": "All GCC residence permit holders get 180 days visa-free"},
            "Azerbaijan": {"access": "voa", "days": 30, "source": "https://evisa.gov.az", "note": "Visa on arrival at Baku airport for UAE residence permit holders. Permit must have 6+ months validity. e-Visa also available."},
            "Oman": {"access": "ev", "days": 30, "source": "https://evisa.rop.gov.om", "note": "GCC residents get eVisa (~5 OMR / $13). Apply at evisa.rop.gov.om as 'GCC Resident'. UAE residence must have 3+ months validity."},
            "Bahrain": {"access": "voa", "days": 14, "source": "https://www.evisa.gov.bh", "note": "GCC residence holders can get VoA (14 days). Laborer occupations excluded. Alternatively apply for eVisa at evisa.gov.bh."}
        }
        # Turkey: UAE residence does NOT qualify for e-visa (confirmed evisa.gov.tr)
        # Serbia: UAE residence does NOT help (nationality-dependent)
        # Mexico/Colombia/Panama/Costa Rica: UAE residence does NOT help
        # Albania: requires 10-year UAE RP valid 1+ year — too restrictive, excluded
    },
    "US Green Card (Permanent Resident)": {
        "source": "Official immigration authorities of each country",
        "last_verified": "April 2026",
        "exemptions": {
            "Turkey": {"access": "ev", "days": 30, "source": "https://www.evisa.gov.tr", "note": "e-visa via evisa.gov.tr (single entry, 30 days)"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://geoconsul.gov.ge"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx"},
            "Canada": {"access": "vf", "days": 180, "source": "https://www.canada.ca/en/immigration-refugees-citizenship.html", "note": "No visa required for US permanent residents"},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.migracioncolombia.gov.co"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs/en/citizens/travel-serbia/visa-requirements"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://bhmc.ae/visa-information/"},
            "Egypt": {"access": "voa", "days": 30, "source": "https://visa2egypt.gov.eg", "note": "Visa on arrival at select airports. Officer discretion."}
        }
    },
    "Valid US Visa (B1/B2)": {
        "source": "Official immigration authorities of each country",
        "last_verified": "April 2026",
        "exemptions": {
            "Turkey": {"access": "ev", "days": 30, "source": "https://www.evisa.gov.tr", "note": "Single-entry e-visa via evisa.gov.tr. Must have valid US/Schengen/UK/Ireland visa."},
            "Georgia": {"access": "vf", "days": 90, "source": "https://geoconsul.gov.ge", "note": "Visa-free entry with any valid US visa — all nationalities"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx", "note": "No Mexican visa needed. Any valid US visa type qualifies — all nationalities."},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.migracioncolombia.gov.co", "note": "Must be currently valid. 90 days, extendable to 180/year."},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa", "note": "Tourist card at entry (~$20). US visa should have been used at least once."},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr", "note": "Valid US visa allows entry up to 30 days"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al", "note": "Multi-entry US visa that has been used at least once. 90 days in 180-day period."},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs/en/citizens/travel-serbia/visa-requirements", "note": "Valid US visa or residence permit. 90 days in 6-month period."},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me", "note": "Valid US visa allows entry up to 30 days"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://bhmc.ae/visa-information/", "note": "Multi-entry US visa. Stay up to 30 days."},
            "Egypt": {"access": "voa", "days": 30, "source": "https://visa2egypt.gov.eg", "note": "Visa on arrival at select airports for holders of valid US/UK/Schengen visa. Not guaranteed — at immigration officer discretion."},
            "Bahrain": {"access": "voa", "days": 14, "source": "https://www.evisa.gov.bh", "note": "VoA available for holders of valid US visa, or apply for eVisa at evisa.gov.bh"}
        }
    },
    "Valid Schengen Visa": {
        "source": "Official immigration authorities of each country",
        "last_verified": "April 2026",
        "exemptions": {
            "Turkey": {"access": "ev", "days": 30, "source": "https://www.evisa.gov.tr", "note": "e-visa via evisa.gov.tr with valid Schengen visa"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://geoconsul.gov.ge"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx"},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.migracioncolombia.gov.co"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al", "note": "Multi-entry Schengen visa, used at least once"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs/en/citizens/travel-serbia/visa-requirements"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://bhmc.ae/visa-information/"},
            "Egypt": {"access": "voa", "days": 30, "source": "https://visa2egypt.gov.eg", "note": "Visa on arrival at select airports. Not guaranteed — officer discretion."}
        }
    },
    "Schengen Residence Permit": {
        "source": "Official immigration authorities of each country",
        "last_verified": "April 2026",
        "exemptions": {
            "Turkey": {"access": "ev", "days": 30, "source": "https://www.evisa.gov.tr"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://geoconsul.gov.ge"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx"},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.migracioncolombia.gov.co"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs/en/citizens/travel-serbia/visa-requirements"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://bhmc.ae/visa-information/"},
            "Egypt": {"access": "voa", "days": 30, "source": "https://visa2egypt.gov.eg", "note": "Visa on arrival at select airports. Officer discretion."}
        }
    },
    "UK Residence Permit (BRP)": {
        "source": "Official immigration authorities of each country",
        "last_verified": "April 2026",
        "exemptions": {
            "Turkey": {"access": "ev", "days": 30, "source": "https://www.evisa.gov.tr", "note": "e-visa via evisa.gov.tr with valid UK visa/BRP"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://geoconsul.gov.ge"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al", "note": "Multi-entry UK visa/BRP, used at least once"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs/en/citizens/travel-serbia/visa-requirements"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "Egypt": {"access": "voa", "days": 30, "source": "https://visa2egypt.gov.eg", "note": "Visa on arrival at select airports. Not guaranteed."}
        }
    },
    "Canada Permanent Resident": {
        "source": "Official immigration authorities of each country",
        "last_verified": "April 2026",
        "exemptions": {
            "Georgia": {"access": "vf", "days": 90, "source": "https://geoconsul.gov.ge"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"}
        }
    }
}

with open(os.path.join(OUTPUT_DIR, 'residence-permits.json'), 'w', encoding='utf-8') as f:
    json.dump(residence_permits, f, indent=2)

print(f"Processed {len(matrix)} passports x {len(sorted_countries)} countries")
print(f"Visa matrix: {os.path.getsize(os.path.join(OUTPUT_DIR, 'visa-matrix.json')) / 1024:.0f} KB")
print(f"Countries: {len(sorted_countries)}")
print(f"Residence permits: {len(residence_permits)} permit types")
