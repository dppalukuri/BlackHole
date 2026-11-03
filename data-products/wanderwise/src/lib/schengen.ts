/**
 * Destinations covered by a Schengen short-stay visa: the 29 Schengen countries,
 * plus Monaco, San Marino and the Vatican, which are reached only through them.
 * Names match the visa data.
 */
export const SCHENGEN_AREA = new Set([
  'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Czech Republic', 'Denmark', 'Estonia', 'Finland',
  'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Italy', 'Latvia', 'Liechtenstein',
  'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania',
  'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland',
  'Monaco', 'San Marino', 'Vatican',
]);

export const isSchengen = (country: string): boolean => SCHENGEN_AREA.has(country);
