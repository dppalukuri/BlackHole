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

# Residence permit exemptions
# These are countries that grant visa-free or simplified entry to holders of
# residence permits from specific countries.
# Source: Official government immigration websites, compiled April 2026
residence_permits = {
    "UAE Residence Permit": {
        "source": "Individual country embassy websites and UAE MOFA",
        "last_verified": "April 2026",
        "note": "ONLY includes exemptions confirmed to apply regardless of passport nationality. Nationality-dependent exemptions are excluded to avoid inaccurate results.",
        "exemptions": {
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge", "note": "Valid UAE residence permit grants visa-free entry regardless of nationality"},
            "Serbia": {"access": "vf", "days": 30, "source": "https://www.mfa.gov.rs", "note": "Valid UAE residence permit grants visa-free entry regardless of nationality"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://www.mvp.gov.ba", "note": "Valid UAE residence permit grants visa-free entry regardless of nationality"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me", "note": "Valid UAE residence permit grants visa-free entry regardless of nationality"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al", "note": "Valid UAE/US/Schengen/UK residence permit grants visa-free entry"},
            "Kyrgyzstan": {"access": "vf", "days": 30, "source": "https://www.mfa.gov.kg", "note": "Valid UAE residence permit grants visa-free entry regardless of nationality"}
        }
    },
    "US Green Card (Permanent Resident)": {
        "source": "Individual country immigration authorities",
        "last_verified": "April 2026",
        "exemptions": {
            "Canada": {"access": "vf", "days": 180, "source": "https://www.canada.ca/en/immigration-refugees-citizenship.html", "note": "No visa required for US permanent residents traveling by air with valid Green Card"},
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx", "note": "Valid Green Card = no visa needed"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Peru": {"access": "vf", "days": 180, "source": "https://www.migraciones.gob.pe"},
            "Belize": {"access": "vf", "days": 30, "source": "https://www.immigration.gov.bz"},
            "British Virgin Islands": {"access": "vf", "days": 30, "source": "https://bvi.gov.vg"},
            "Turks and Caicos": {"access": "vf", "days": 30, "source": "https://www.gov.tc"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"}
        }
    },
    "Schengen Residence Permit": {
        "source": "EU regulations and bilateral agreements",
        "last_verified": "April 2026",
        "exemptions": {
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 90, "source": "https://www.mvp.gov.ba"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge"},
            "Kosovo": {"access": "vf", "days": 15, "source": "https://www.mfa-ks.net"},
            "Moldova": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.md"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "North Macedonia": {"access": "vf", "days": 15, "source": "https://www.mfa.gov.mk"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs"},
            "Turkey": {"access": "ev", "days": 90, "source": "https://www.evisa.gov.tr"},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.cancilleria.gov.co"}
        }
    },
    "UK Residence Permit (BRP)": {
        "source": "Individual country immigration authorities",
        "last_verified": "April 2026",
        "note": "ONLY includes exemptions confirmed to apply regardless of passport nationality.",
        "exemptions": {
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://www.mvp.gov.ba"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"}
        }
    },
    "Canada Permanent Resident": {
        "source": "Individual country immigration authorities",
        "last_verified": "April 2026",
        "exemptions": {
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"}
        }
    },
    "Valid US Visa (B1/B2)": {
        "source": "Individual country immigration authorities",
        "last_verified": "April 2026",
        "note": "ONLY includes exemptions confirmed to apply regardless of passport nationality. Turkey and Philippines excluded as their US-visa exemptions are nationality-dependent.",
        "exemptions": {
            "Mexico": {"access": "vf", "days": 180, "source": "https://www.inm.gob.mx", "note": "Valid US visa holders can enter Mexico without a Mexican visa — confirmed for all nationalities"},
            "Panama": {"access": "vf", "days": 30, "source": "https://www.migracion.gob.pa", "note": "Valid US visa (used or unused) allows entry for all nationalities"},
            "Costa Rica": {"access": "vf", "days": 30, "source": "https://www.migracion.go.cr", "note": "Valid US visa allows entry regardless of nationality"},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.cancilleria.gov.co", "note": "Valid US visa allows visa-free entry for up to 90 days for all nationalities"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge"},
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://www.mvp.gov.ba"},
            "Dominican Republic": {"access": "vf", "days": 30, "source": "https://www.dgm.gob.do"},
            "Belize": {"access": "vf", "days": 30, "source": "https://www.immigration.gov.bz"}
        }
    },
    "Valid Schengen Visa": {
        "source": "Individual country immigration authorities and EU bilateral agreements",
        "last_verified": "April 2026",
        "note": "ONLY includes exemptions confirmed to apply regardless of passport nationality. Turkey excluded as its Schengen-visa e-visa is nationality-dependent.",
        "exemptions": {
            "Albania": {"access": "vf", "days": 90, "source": "https://punetejashtme.gov.al", "note": "Valid multi-entry Schengen visa allows entry without Albanian visa — all nationalities"},
            "Bosnia and Herzegovina": {"access": "vf", "days": 30, "source": "https://www.mvp.gov.ba"},
            "Colombia": {"access": "vf", "days": 90, "source": "https://www.cancilleria.gov.co"},
            "Georgia": {"access": "vf", "days": 90, "source": "https://www.geoconsul.gov.ge"},
            "Kosovo": {"access": "vf", "days": 15, "source": "https://www.mfa-ks.net"},
            "Moldova": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.md"},
            "Montenegro": {"access": "vf", "days": 30, "source": "https://www.gov.me"},
            "North Macedonia": {"access": "vf", "days": 15, "source": "https://www.mfa.gov.mk"},
            "Serbia": {"access": "vf", "days": 90, "source": "https://www.mfa.gov.rs"},
            "Romania": {"access": "vf", "days": 90, "source": "https://www.mae.ro", "note": "Valid Schengen visa allows entry — all nationalities"},
            "Bulgaria": {"access": "vf", "days": 90, "source": "https://www.mfa.bg", "note": "Valid Schengen visa allows entry — all nationalities"}
        }
    }
}

with open(os.path.join(OUTPUT_DIR, 'residence-permits.json'), 'w', encoding='utf-8') as f:
    json.dump(residence_permits, f, indent=2)

print(f"Processed {len(matrix)} passports x {len(sorted_countries)} countries")
print(f"Visa matrix: {os.path.getsize(os.path.join(OUTPUT_DIR, 'visa-matrix.json')) / 1024:.0f} KB")
print(f"Countries: {len(sorted_countries)}")
print(f"Residence permits: {len(residence_permits)} permit types")
