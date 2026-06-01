/**
 * Priority destinations for the reverse-index pages (/visa-free-to-<slug>).
 * Each entry produces a page listing every passport that can enter this
 * country visa-free, on arrival, with e-visa, or with ETA.
 *
 * Add entries to expand coverage. Slug must be unique kebab-case; country
 * must exactly match a destination name in visa-matrix.json columns.
 */

export interface PriorityDestination {
  slug: string;        // URL path segment (without leading /visa-free-to-)
  country: string;     // key used in visa-matrix lookups
  displayName: string; // nicer rendering (e.g. "the United States")
  searchVolume: number;// rough monthly search volume (for sorting / hints)
  blurb: string;
}

export const priorityDestinations: PriorityDestination[] = [
  { slug: 'thailand',        country: 'Thailand',             displayName: 'Thailand',          searchVolume: 27000, blurb: 'Bangkok, Phuket, Chiang Mai — one of Southeast Asia\'s most traveled destinations.' },
  { slug: 'turkey',          country: 'Turkey',               displayName: 'Turkey',            searchVolume: 18000, blurb: 'Istanbul, Cappadocia, Aegean coast — gateway between Europe and Asia.' },
  { slug: 'uae',             country: 'United Arab Emirates', displayName: 'the UAE',           searchVolume: 22000, blurb: 'Dubai and Abu Dhabi — a top global hub with widely-varying entry rules by passport.' },
  { slug: 'singapore',       country: 'Singapore',            displayName: 'Singapore',         searchVolume: 14000, blurb: 'Southeast Asia\'s financial hub, open to most Western passports visa-free.' },
  { slug: 'japan',           country: 'Japan',                displayName: 'Japan',             searchVolume: 16000, blurb: 'Tokyo, Kyoto, Osaka — strict visa regime but widely waived for tourism.' },
  { slug: 'south-korea',     country: 'South Korea',          displayName: 'South Korea',       searchVolume: 9000,  blurb: 'Seoul and Jeju — K-ETA required for most Western passports from 2024.' },
  { slug: 'malaysia',        country: 'Malaysia',             displayName: 'Malaysia',          searchVolume: 8000,  blurb: 'Kuala Lumpur, Penang, Langkawi — generous visa-free regime for many nationalities.' },
  { slug: 'indonesia',       country: 'Indonesia',            displayName: 'Indonesia',         searchVolume: 11000, blurb: 'Bali, Jakarta, Yogyakarta — paid VoA for most nationalities from 2022.' },
  { slug: 'vietnam',         country: 'Vietnam',              displayName: 'Vietnam',           searchVolume: 10000, blurb: 'Hanoi, Ho Chi Minh, Da Nang — e-visa system accepts 80+ nationalities.' },
  { slug: 'philippines',     country: 'Philippines',          displayName: 'the Philippines',   searchVolume: 6000,  blurb: 'Manila, Cebu, Palawan — 30-day visa-free entry for most travelers.' },
  { slug: 'sri-lanka',       country: 'Sri Lanka',            displayName: 'Sri Lanka',         searchVolume: 6000,  blurb: 'Colombo, Kandy, southern beaches — ETA required for most nationalities.' },
  { slug: 'maldives',        country: 'Maldives',             displayName: 'the Maldives',      searchVolume: 6500,  blurb: 'Male, resort islands — visa-free 30-day stay for all nationalities on arrival.' },
  { slug: 'uk',              country: 'United Kingdom',       displayName: 'the United Kingdom',searchVolume: 20000, blurb: 'London, Edinburgh, Manchester — ETA rolling out to additional nationalities from 2025.' },
  { slug: 'us',              country: 'United States',        displayName: 'the United States', searchVolume: 35000, blurb: 'New York, LA, San Francisco — ESTA for 40+ visa-waiver nationalities; B-2 visa otherwise.' },
  { slug: 'canada',          country: 'Canada',               displayName: 'Canada',            searchVolume: 14000, blurb: 'Toronto, Vancouver, Montreal — eTA required for most visa-exempt nationalities.' },
  { slug: 'australia',       country: 'Australia',            displayName: 'Australia',         searchVolume: 13000, blurb: 'Sydney, Melbourne, Cairns — ETA (601) or eVisitor (651) required for most.' },
  { slug: 'new-zealand',     country: 'New Zealand',          displayName: 'New Zealand',       searchVolume: 7000,  blurb: 'Auckland, Queenstown — NZeTA + IVL fee required for most visa-waiver nationalities.' },
  { slug: 'france',          country: 'France',               displayName: 'France',            searchVolume: 15000, blurb: 'Paris, French Riviera, Alps — Schengen zone (90-day rule applies across all Schengen).' },
  { slug: 'germany',         country: 'Germany',              displayName: 'Germany',           searchVolume: 11000, blurb: 'Berlin, Munich, Frankfurt — Schengen zone.' },
  { slug: 'italy',           country: 'Italy',                displayName: 'Italy',             searchVolume: 13000, blurb: 'Rome, Florence, Venice — Schengen zone.' },
  { slug: 'spain',           country: 'Spain',                displayName: 'Spain',             searchVolume: 12000, blurb: 'Madrid, Barcelona, Seville — Schengen zone.' },
  { slug: 'greece',          country: 'Greece',               displayName: 'Greece',            searchVolume: 9000,  blurb: 'Athens, Santorini, Mykonos — Schengen zone.' },
  { slug: 'portugal',        country: 'Portugal',             displayName: 'Portugal',          searchVolume: 7000,  blurb: 'Lisbon, Porto, Algarve — Schengen zone.' },
  { slug: 'switzerland',     country: 'Switzerland',          displayName: 'Switzerland',       searchVolume: 6000,  blurb: 'Zurich, Geneva, Alps — Schengen zone (non-EU).' },
  { slug: 'netherlands',     country: 'Netherlands',          displayName: 'the Netherlands',   searchVolume: 7500,  blurb: 'Amsterdam, Rotterdam, The Hague — Schengen zone.' },
  { slug: 'mexico',          country: 'Mexico',               displayName: 'Mexico',            searchVolume: 9000,  blurb: 'Mexico City, Cancun, Tulum — 180-day visa-free stay for many nationalities.' },
  { slug: 'egypt',           country: 'Egypt',                displayName: 'Egypt',             searchVolume: 5000,  blurb: 'Cairo, Luxor, Red Sea coast — paid VoA + growing e-visa program.' },
  { slug: 'morocco',         country: 'Morocco',              displayName: 'Morocco',           searchVolume: 5000,  blurb: 'Marrakech, Casablanca, Fes — visa-free for many, visa-required for some.' },
  { slug: 'kenya',           country: 'Kenya',                displayName: 'Kenya',             searchVolume: 4000,  blurb: 'Nairobi, Maasai Mara, coast — eTA required for all non-exempt nationalities from 2024.' },
  { slug: 'south-africa',    country: 'South Africa',         displayName: 'South Africa',      searchVolume: 4500,  blurb: 'Johannesburg, Cape Town, safari destinations.' },
];
