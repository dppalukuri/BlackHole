const LOCALE_MAP: Record<string, string> = {
  INR: 'en-IN',
  AED: 'en-AE',
  USD: 'en-US',
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
