import { monthlyPayment } from './loan-emi';

/** Highest loan-to-value allowed for properties up to `maxPrice`. */
export interface LtvTier {
  maxPrice: number;
  ltvPercent: number;
}

export interface AffordabilityInput {
  monthlyIncome: number;
  existingMonthlyDebts: number;
  /** Largest share of income all debt payments may take, in percent. */
  debtRatioPercent: number;
  annualRate: number;
  tenureMonths: number;
  /** Cash available for the down payment and buying costs. */
  savings: number;
  /** Buying costs as a percent of the price, paid in cash. */
  buyingCostPercent: number;
  /** Ordered from lowest price to highest. The last tier must be unbounded. */
  ltvTiers: LtvTier[];
}

export type LimitingFactor = 'income' | 'savings';

export interface AffordabilityResult {
  /** The payment the debt limit leaves for this loan. Zero if debts use it all. */
  maxPayment: number;
  /** Largest loan your income supports, before looking at any property. */
  incomeLoanLimit: number;
  maxPrice: number;
  loan: number;
  payment: number;
  downPayment: number;
  buyingCosts: number;
  /** Which constraint stops the price going higher. */
  limitedBy: LimitingFactor;
  ltvPercent: number;
}

/**
 * The highest property price that satisfies every limit at once: the loan must
 * fit within the income limit and the LTV cap, and savings must cover whatever
 * the loan leaves unpaid plus the buying costs.
 *
 * For price p, loan = min(I, L·p), and cash needed is p(1 + k) − loan ≤ C. That
 * expands to two bounds, p ≤ (I + C)/(1 + k) and p ≤ C/(1 + k − L), checked in
 * each LTV tier. A higher tier can give a lower loan than the top of the tier
 * below, because its LTV is lower, so every tier is tested rather than stopping
 * at the first that fits.
 */
export function maxAffordability(input: AffordabilityInput): AffordabilityResult {
  const { monthlyIncome, existingMonthlyDebts, debtRatioPercent, annualRate, tenureMonths, savings, ltvTiers } = input;
  const k = input.buyingCostPercent / 100;

  const maxPayment = Math.max(0, (monthlyIncome * debtRatioPercent) / 100 - existingMonthlyDebts);
  const perUnit = monthlyPayment(1, annualRate, tenureMonths);
  const incomeLoanLimit = maxPayment / perUnit;

  let maxPrice = 0;
  let previousCeiling = 0;
  let ltvPercent = ltvTiers[0].ltvPercent;
  for (const tier of ltvTiers) {
    const L = tier.ltvPercent / 100;
    const best = Math.min(tier.maxPrice, (incomeLoanLimit + savings) / (1 + k), savings / (1 + k - L));
    // A result below this tier's floor belongs to a tier already tested.
    if (best > maxPrice && best >= previousCeiling) {
      maxPrice = best;
      ltvPercent = tier.ltvPercent;
    }
    previousCeiling = tier.maxPrice;
  }

  const loan = Math.min(incomeLoanLimit, (maxPrice * ltvPercent) / 100);
  const loanFromIncome = incomeLoanLimit <= (maxPrice * ltvPercent) / 100 + 0.01;

  return {
    maxPayment,
    incomeLoanLimit,
    maxPrice,
    loan,
    payment: loan * perUnit,
    downPayment: maxPrice - loan,
    buyingCosts: maxPrice * k,
    limitedBy: loanFromIncome ? 'income' : 'savings',
    ltvPercent,
  };
}

/** RBI's LTV ceilings on individual housing loans. */
export const INDIA_LTV_TIERS: LtvTier[] = [
  { maxPrice: 3000000, ltvPercent: 90 },
  { maxPrice: 7500000, ltvPercent: 80 },
  { maxPrice: Infinity, ltvPercent: 75 },
];
