export interface StepUpSipYear {
  year: number;
  /** The monthly contribution in force during this year. */
  monthlySIP: number;
  /** Cumulative amount invested by the end of this year. */
  invested: number;
  /** Portfolio value at the end of this year. */
  value: number;
}

export interface StepUpSipResult {
  totalInvested: number;
  totalValue: number;
  totalReturns: number;
  yearlyBreakdown: StepUpSipYear[];
}

/**
 * Step-up SIP: a monthly investment that increases by a fixed percentage at
 * the end of every year, which is how most people actually invest as income
 * rises. Simulated month by month because the contribution changes annually,
 * so there is no single closed form.
 *
 * Compare against `sipFutureValue` (compound-growth) for the flat-SIP case.
 */
export function stepUpSipProjection(
  monthly: number,
  annualRate: number,
  years: number,
  stepUpPct: number
): StepUpSipResult {
  const monthlyRate = annualRate / 12 / 100;
  const yearlyBreakdown: StepUpSipYear[] = [];

  let totalInvested = 0;
  let totalValue = 0;
  let currentMonthly = monthly;

  for (let y = 1; y <= years; y++) {
    for (let m = 0; m < 12; m++) {
      totalInvested += currentMonthly;
      totalValue = (totalValue + currentMonthly) * (1 + monthlyRate);
    }
    yearlyBreakdown.push({
      year: y,
      monthlySIP: currentMonthly,
      invested: totalInvested,
      value: totalValue,
    });
    currentMonthly = Math.round(currentMonthly * (1 + stepUpPct / 100));
  }

  return {
    totalInvested,
    totalValue,
    totalReturns: totalValue - totalInvested,
    yearlyBreakdown,
  };
}
