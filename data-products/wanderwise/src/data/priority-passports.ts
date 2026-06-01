/**
 * Priority passports for static page generation.
 * Each entry produces a page at /{slug} with full visa-free data.
 *
 * To add a new passport page, just add an entry here. The slug must be
 * unique and kebab-cased; it becomes the URL path.
 */

export interface PriorityPassport {
  /** URL slug (without leading slash). */
  slug: string;
  /** Must exactly match a key in visa-matrix.json. */
  passport: string;
  /** SEO-friendly adjective form (e.g. "Indian", "British"). */
  nationality: string;
  /** Approx. yearly search volume for this passport's queries — used to order related links. */
  priority: number;
}

export const priorityPassports: PriorityPassport[] = [
  // Top-tier — high search volume
  { slug: 'indian-passport',        passport: 'India',                    nationality: 'Indian',       priority: 100 },
  { slug: 'uk-passport',            passport: 'United Kingdom',           nationality: 'British',      priority: 95 },
  { slug: 'us-passport',            passport: 'United States',            nationality: 'American',     priority: 95 },
  { slug: 'canadian-passport',      passport: 'Canada',                   nationality: 'Canadian',     priority: 90 },
  { slug: 'australian-passport',    passport: 'Australia',                nationality: 'Australian',   priority: 85 },
  { slug: 'japanese-passport',      passport: 'Japan',                    nationality: 'Japanese',     priority: 85 },
  { slug: 'singapore-passport',     passport: 'Singapore',                nationality: 'Singaporean',  priority: 80 },
  { slug: 'german-passport',        passport: 'Germany',                  nationality: 'German',       priority: 80 },
  { slug: 'french-passport',        passport: 'France',                   nationality: 'French',       priority: 75 },
  { slug: 'italian-passport',       passport: 'Italy',                    nationality: 'Italian',      priority: 75 },
  { slug: 'spanish-passport',       passport: 'Spain',                    nationality: 'Spanish',      priority: 75 },
  { slug: 'dutch-passport',         passport: 'Netherlands',              nationality: 'Dutch',        priority: 70 },
  { slug: 'swiss-passport',         passport: 'Switzerland',              nationality: 'Swiss',        priority: 70 },
  { slug: 'irish-passport',         passport: 'Ireland',                  nationality: 'Irish',        priority: 70 },
  { slug: 'uae-passport',           passport: 'United Arab Emirates',     nationality: 'Emirati',      priority: 75 },

  // South Asia + Asia
  { slug: 'pakistani-passport',     passport: 'Pakistan',                 nationality: 'Pakistani',    priority: 75 },
  { slug: 'bangladeshi-passport',   passport: 'Bangladesh',               nationality: 'Bangladeshi',  priority: 65 },
  { slug: 'sri-lankan-passport',    passport: 'Sri Lanka',                nationality: 'Sri Lankan',   priority: 55 },
  { slug: 'philippine-passport',    passport: 'Philippines',              nationality: 'Filipino',     priority: 70 },
  { slug: 'chinese-passport',       passport: 'China',                    nationality: 'Chinese',      priority: 80 },

  // Middle East / Africa
  { slug: 'egyptian-passport',      passport: 'Egypt',                    nationality: 'Egyptian',     priority: 55 },
  { slug: 'nigerian-passport',      passport: 'Nigeria',                  nationality: 'Nigerian',     priority: 65 },
  { slug: 'south-african-passport', passport: 'South Africa',             nationality: 'South African',priority: 55 },

  // Americas
  { slug: 'brazilian-passport',     passport: 'Brazil',                   nationality: 'Brazilian',    priority: 60 },
  { slug: 'mexican-passport',       passport: 'Mexico',                   nationality: 'Mexican',      priority: 55 },
  { slug: 'argentine-passport',     passport: 'Argentina',                nationality: 'Argentine',    priority: 50 },
  { slug: 'colombian-passport',     passport: 'Colombia',                 nationality: 'Colombian',    priority: 50 },
  { slug: 'chilean-passport',       passport: 'Chile',                    nationality: 'Chilean',      priority: 55 },

  // GCC + Middle East
  { slug: 'saudi-arabian-passport', passport: 'Saudi Arabia',             nationality: 'Saudi',        priority: 60 },
  { slug: 'qatari-passport',        passport: 'Qatar',                    nationality: 'Qatari',       priority: 55 },
  { slug: 'kuwaiti-passport',       passport: 'Kuwait',                   nationality: 'Kuwaiti',      priority: 50 },
  { slug: 'omani-passport',         passport: 'Oman',                     nationality: 'Omani',        priority: 45 },
  { slug: 'turkish-passport',       passport: 'Turkey',                   nationality: 'Turkish',      priority: 65 },
  { slug: 'israeli-passport',       passport: 'Israel',                   nationality: 'Israeli',      priority: 60 },

  // ASEAN + East Asia
  { slug: 'malaysian-passport',     passport: 'Malaysia',                 nationality: 'Malaysian',    priority: 65 },
  { slug: 'indonesian-passport',    passport: 'Indonesia',                nationality: 'Indonesian',   priority: 65 },
  { slug: 'thai-passport',          passport: 'Thailand',                 nationality: 'Thai',         priority: 60 },
  { slug: 'vietnamese-passport',    passport: 'Vietnam',                  nationality: 'Vietnamese',   priority: 55 },
  { slug: 'south-korean-passport',  passport: 'South Korea',              nationality: 'South Korean', priority: 70 },
  { slug: 'taiwanese-passport',     passport: 'Taiwan',                   nationality: 'Taiwanese',    priority: 55 },

  // Europe (additional)
  { slug: 'belgian-passport',       passport: 'Belgium',                  nationality: 'Belgian',      priority: 65 },
  { slug: 'swedish-passport',       passport: 'Sweden',                   nationality: 'Swedish',      priority: 70 },
  { slug: 'norwegian-passport',     passport: 'Norway',                   nationality: 'Norwegian',    priority: 65 },
  { slug: 'danish-passport',        passport: 'Denmark',                  nationality: 'Danish',       priority: 65 },
  { slug: 'finnish-passport',       passport: 'Finland',                  nationality: 'Finnish',      priority: 60 },
  { slug: 'polish-passport',        passport: 'Poland',                   nationality: 'Polish',       priority: 65 },
  { slug: 'greek-passport',         passport: 'Greece',                   nationality: 'Greek',        priority: 55 },
  { slug: 'portuguese-passport',    passport: 'Portugal',                 nationality: 'Portuguese',   priority: 60 },
  { slug: 'russian-passport',       passport: 'Russia',                   nationality: 'Russian',      priority: 60 },
  { slug: 'ukrainian-passport',     passport: 'Ukraine',                  nationality: 'Ukrainian',    priority: 55 },

  // Oceania
  { slug: 'new-zealand-passport',   passport: 'New Zealand',              nationality: 'New Zealand',  priority: 65 },

  // Africa (additional)
  { slug: 'kenyan-passport',        passport: 'Kenya',                    nationality: 'Kenyan',       priority: 45 },
  { slug: 'ghanaian-passport',      passport: 'Ghana',                    nationality: 'Ghanaian',     priority: 40 },
  { slug: 'moroccan-passport',      passport: 'Morocco',                  nationality: 'Moroccan',     priority: 50 },
];
