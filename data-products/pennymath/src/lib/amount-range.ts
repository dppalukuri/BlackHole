/**
 * Range rules for money inputs.
 *
 * Every amount can be anything from 1,000 to 100 crore in rupees, or to 100
 * million in other currencies. The slider shows part of that range at a time,
 * and the ×10 and ÷10 buttons move it. Typing can go anywhere in the full range.
 */

export const AMOUNT_FLOOR = 1000;

/** Smallest slider range the ÷10 button can reach. */
export const MIN_WINDOW = 10_000;

/** Largest amount for a currency, identified by its locale: ₹100 crore, or 100 million. */
export function amountCeiling(locale: string): number {
  return locale === 'en-IN' ? 1e9 : 1e8;
}

/**
 * Top of a slider range that shows `value` no more than half way along: the
 * next 1, 2 or 5 × 10ⁿ at or above twice the value. With no value, `fallback`
 * (the calculator's own suggestion) is used instead.
 */
export function windowFor(value: number, fallback: number, ceiling: number): number {
  const target = value > 0 ? value * 2 : Math.max(fallback, 1);
  const power = 10 ** Math.floor(Math.log10(target));
  const top = [1, 2, 5, 10].map((m) => m * power).find((t) => t >= target - 1e-9) ?? 10 * power;
  return Math.min(ceiling, Math.max(MIN_WINDOW, top));
}

/** Slider step for a range: about a hundredth of it, as a power of ten. */
export function windowStep(top: number): number {
  return Math.max(1, 10 ** (Math.floor(Math.log10(top)) - 2));
}

const trim = (n: number) => String(Number(n.toFixed(1)));

/** Short form of an amount for the range hint: "₹1 Cr", "₹50 L", "AED 10M". */
export function shortAmount(n: number, locale: string, prefix: string): string {
  if (locale === 'en-IN') {
    if (n >= 1e7) return `${prefix}${trim(n / 1e7)} Cr`;
    if (n >= 1e5) return `${prefix}${trim(n / 1e5)} L`;
    return `${prefix}${trim(n / 1e3)}K`;
  }
  return prefix + new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
}
