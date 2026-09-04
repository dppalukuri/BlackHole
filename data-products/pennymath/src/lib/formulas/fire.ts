export interface FireMilestone {
  year: number;
  corpus: number;
  pctToFire: number;
}

export interface FireInput {
  monthlyExpenses: number;
  currentSavings: number;
  monthlySavings: number;
  /** Nominal expected return, % p.a. */
  expectedReturn: number;
  /** Expected inflation, % p.a. */
  inflationRate: number;
  /** Safe withdrawal rate, % p.a. (the "4% rule" dial). */
  withdrawalRate: number;
  currentAge: number;
}

export interface FireResult {
  /** Inflation-adjusted (real) return, % p.a. */
  realReturn: number;
  annualExpenses: number;
  /** Corpus that sustains current expenses at the chosen withdrawal rate. */
  fireNumber: number;
  monthsToFire: number;
  yearsToFire: number;
  fireAge: number;
  /** False when the corpus does not reach the target within the 50-year cap. */
  canRetire: boolean;
  monthlyPassiveIncome: number;
  milestones: FireMilestone[];
}

/** Hard stop for the accumulation loop — a real return <= 0 never converges. */
const MAX_MONTHS = 600;

/**
 * FIRE (Financial Independence, Retire Early) projection.
 *
 * Growth is modelled in REAL terms — the nominal return is deflated by
 * inflation — so the resulting corpus is expressed in today's rupees and can
 * be compared directly against today's expenses.
 */
export function fireProjection({
  monthlyExpenses,
  currentSavings,
  monthlySavings,
  expectedReturn,
  inflationRate,
  withdrawalRate,
  currentAge,
}: FireInput): FireResult {
  const realReturn = ((1 + expectedReturn / 100) / (1 + inflationRate / 100) - 1) * 100;
  const annualExpenses = monthlyExpenses * 12;
  const fireNumber = annualExpenses / (withdrawalRate / 100);

  const monthlyRate = realReturn / 12 / 100;
  const milestones: FireMilestone[] = [];

  let corpus = currentSavings;
  let months = 0;

  while (corpus < fireNumber && months < MAX_MONTHS) {
    corpus = (corpus + monthlySavings) * (1 + monthlyRate);
    months++;
    if (months % 12 === 0) {
      milestones.push({
        year: months / 12,
        corpus,
        pctToFire: Math.min(100, (corpus / fireNumber) * 100),
      });
    }
  }

  const yearsToFire = months / 12;

  return {
    realReturn,
    annualExpenses,
    fireNumber,
    monthsToFire: months,
    yearsToFire,
    fireAge: currentAge + yearsToFire,
    canRetire: months < MAX_MONTHS,
    monthlyPassiveIncome: (fireNumber * (withdrawalRate / 100)) / 12,
    milestones,
  };
}
