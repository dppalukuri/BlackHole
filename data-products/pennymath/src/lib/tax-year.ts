/**
 * Single source of truth for which financial year the India tax data reflects.
 *
 * The slab tables in `formulas/tax-slab.ts` are statutory numbers that change
 * with each Finance Act. They were previously described only in a code comment
 * and re-typed into eight page strings, so nothing connected the data to the
 * calendar and nothing flagged when it aged out.
 *
 * WHEN THE FINANCE ACT CHANGES: update the slabs in `formulas/tax-slab.ts`,
 * then bump the three constants below. Everything user-facing follows.
 */

/** Financial year the slab data in `formulas/tax-slab.ts` encodes. */
export const TAX_DATA_FY = 'FY 2025-26';

/** Assessment year corresponding to `TAX_DATA_FY`. */
export const TAX_DATA_AY = 'AY 2026-27';

/** Calendar year in which `TAX_DATA_FY` began (Indian FY starts 1 April). */
export const TAX_DATA_FY_START_YEAR = 2025;

/**
 * The Indian financial year containing `date`. The FY runs 1 April to 31 March,
 * so January–March belongs to the FY that began the previous calendar year.
 */
export function indianFinancialYear(date: Date = new Date()): {
  startYear: number;
  fy: string;
  ay: string;
} {
  const startYear = date.getMonth() >= 3 ? date.getFullYear() : date.getFullYear() - 1;
  const two = (y: number) => String(y % 100).padStart(2, '0');
  return {
    startYear,
    fy: `FY ${startYear}-${two(startYear + 1)}`,
    ay: `AY ${startYear + 1}-${two(startYear + 2)}`,
  };
}

/**
 * True when the current financial year has moved past the one the slab data
 * encodes — i.e. the calculator is serving last year's tax law.
 */
export function isTaxDataStale(date: Date = new Date()): boolean {
  return indianFinancialYear(date).startYear > TAX_DATA_FY_START_YEAR;
}

/** How many financial years behind the slab data is (0 when current). */
export function taxDataYearsBehind(date: Date = new Date()): number {
  return Math.max(0, indianFinancialYear(date).startYear - TAX_DATA_FY_START_YEAR);
}
