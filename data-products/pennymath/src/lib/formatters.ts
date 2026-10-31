const LOCALE_MAP: Record<string, string> = {
  INR: 'en-IN',
  AED: 'en-AE',
  USD: 'en-US',
  GBP: 'en-GB',
};

/**
 * BCP-47 locale that matches a currency's conventions (lakh/crore grouping for
 * INR, western grouping elsewhere). Components that need locale-correct numbers
 * take a `locale` prop instead of inspecting currency symbols themselves.
 */
export function localeForCurrency(currencyCode: string): string {
  return LOCALE_MAP[currencyCode] || 'en-US';
}

export function formatCurrency(
  value: number,
  currencyCode: string = 'INR'
): string {
  const locale = LOCALE_MAP[currencyCode] || 'en-US';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Short currency for chart axes: ₹15 L and ₹1.5 Cr for rupees, AED 1.5M and
 * £250K elsewhere. Rupees are done by hand because compact Intl output for
 * en-IN differs between Node and browsers.
 */
export function formatCompactCurrency(value: number, currencyCode: string = 'INR'): string {
  const trim = (n: number) => String(Number(n.toFixed(1)));
  if (currencyCode === 'INR') {
    const abs = Math.abs(value);
    const sign = value < 0 ? '-' : '';
    if (abs >= 1e7) return `${sign}₹${trim(abs / 1e7)} Cr`;
    if (abs >= 1e5) return `${sign}₹${trim(abs / 1e5)} L`;
    if (abs >= 1e3) return `${sign}₹${trim(abs / 1e3)}K`;
    return `${sign}₹${Math.round(abs)}`;
  }
  return new Intl.NumberFormat(LOCALE_MAP[currencyCode] || 'en-US', {
    style: 'currency',
    currency: currencyCode,
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatNumber(value: number, locale: string = 'en-IN'): string {
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

/** Indian numbering: 1,00,000 for lakh, 1,00,00,000 for crore */
export function formatIndianCurrency(value: number): string {
  return formatCurrency(value, 'INR');
}

/** A number of months as "11 yrs 3 mos". */
export function formatPeriod(months: number): string {
  if (months <= 0) return '0 months';
  const y = Math.floor(months / 12);
  const m = months % 12;
  const parts = [];
  if (y > 0) parts.push(`${y} ${y === 1 ? 'yr' : 'yrs'}`);
  if (m > 0) parts.push(`${m} ${m === 1 ? 'mo' : 'mos'}`);
  return parts.join(' ');
}
