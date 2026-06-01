const LOCALE_MAP: Record<string, string> = {
  INR: 'en-IN',
  AED: 'en-AE',
  USD: 'en-US',
};

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
