export interface SWPYearRow {
  year: number;
  openingBalance: number;
  withdrawn: number;
  returnsEarned: number;
  closingBalance: number;
}

export interface SWPResult {
  investedAmount: number;
  totalWithdrawn: number;
  estimatedReturns: number;
  finalBalance: number;
  /** True if the corpus hit zero at any point inside the plan. */
  depleted: boolean;
  /** 1-indexed month the corpus ran dry, or null if it survived the full term. */
  depletedAtMonth: number | null;
  /** Months actually funded — equals the full term unless the corpus ran dry. */
  monthsLasted: number;
  /**
   * Monthly withdrawal the corpus can fund from growth alone, leaving the
   * capital untouched. Withdraw more than this and the balance shrinks.
   */
  sustainableWithdrawal: number;
  yearlyBreakdown: SWPYearRow[];
}

/**
 * SWP (Systematic Withdrawal Plan) projection.
 *
 * Month-by-month simulation rather than the closed form
 * `FV = P(1+i)^n - W[((1+i)^n - 1)/i]` because the closed form divides by zero
 * at a 0% return and, more importantly, happily returns a negative balance when
 * the withdrawal outruns the corpus. Simulating lets us stop at zero and report
 * exactly when the money ran out, which is the answer most people come to an
 * SWP calculator for.
 *
 * Convention: growth is credited first, then the withdrawal is taken at the end
 * of the month (ordinary annuity) — the same order used by the major Indian
 * fund-house SWP calculators.
 */
export function swpProjection(
  initialInvestment: number,
  monthlyWithdrawal: number,
  annualRate: number,
  years: number
): SWPResult {
  const monthlyRate = annualRate / 12 / 100;
  const totalMonths = Math.max(0, Math.round(years * 12));

  let balance = initialInvestment;
  let totalWithdrawn = 0;
  let estimatedReturns = 0;
  let depletedAtMonth: number | null = null;
  let monthsLasted = 0;

  const yearlyBreakdown: SWPYearRow[] = [];

  for (let y = 1; y <= years; y++) {
    const openingBalance = balance;
    let withdrawn = 0;
    let returnsEarned = 0;

    for (let m = 1; m <= 12; m++) {
      const monthIndex = (y - 1) * 12 + m;
      if (monthIndex > totalMonths || balance <= 0) break;

      const growth = balance * monthlyRate;
      balance += growth;
      returnsEarned += growth;
      estimatedReturns += growth;

      // A final partial withdrawal is all the corpus can fund.
      const payout = Math.min(monthlyWithdrawal, balance);
      balance -= payout;
      withdrawn += payout;
      totalWithdrawn += payout;
      monthsLasted = monthIndex;

      // Sub-paisa residue is zero for our purposes.
      if (balance <= 0.005) {
        balance = 0;
        if (depletedAtMonth === null) depletedAtMonth = monthIndex;
      }
    }

    yearlyBreakdown.push({
      year: y,
      openingBalance,
      withdrawn,
      returnsEarned,
      closingBalance: balance,
    });

    // Nothing left to project — don't pad the table with empty years.
    if (balance <= 0) break;
  }

  return {
    investedAmount: initialInvestment,
    totalWithdrawn,
    estimatedReturns,
    finalBalance: balance,
    depleted: depletedAtMonth !== null,
    depletedAtMonth,
    monthsLasted,
    sustainableWithdrawal: initialInvestment * monthlyRate,
    yearlyBreakdown,
  };
}
