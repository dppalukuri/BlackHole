export interface NpsInput {
  currentAge: number;
  retirementAge: number;
  monthlyContribution: number;
  /** Yearly rise in the monthly contribution, in percent. */
  annualStepUpPercent: number;
  /** Assumed yearly return on the NPS portfolio, in percent. */
  expectedReturnPercent: number;
  existingCorpus: number;
  /** Share of the final corpus used to buy an annuity, in percent. */
  annuityPercent: number;
  /** Yearly payout rate of the annuity, in percent. */
  annuityRatePercent: number;
}

export interface NpsYearRow {
  age: number;
  invested: number;
  corpus: number;
}

export interface NpsResult {
  totalInvested: number;
  growth: number;
  corpus: number;
  lumpSum: number;
  annuityPurchase: number;
  monthlyPension: number;
  yearlyBreakdown: NpsYearRow[];
}

/** NPS projection, with contributions at the start of each month. */
export function npsProjection(input: NpsInput): NpsResult {
  const { currentAge, retirementAge, annualStepUpPercent, expectedReturnPercent, existingCorpus, annuityPercent, annuityRatePercent } = input;
  const monthlyReturn = Math.pow(1 + expectedReturnPercent / 100, 1 / 12) - 1;
  const years = Math.max(0, retirementAge - currentAge);

  let corpus = existingCorpus;
  let contribution = input.monthlyContribution;
  let totalInvested = 0;
  const yearlyBreakdown: NpsYearRow[] = [];

  for (let y = 1; y <= years; y++) {
    for (let m = 0; m < 12; m++) {
      corpus = (corpus + contribution) * (1 + monthlyReturn);
      totalInvested += contribution;
    }
    yearlyBreakdown.push({ age: currentAge + y, invested: totalInvested, corpus });
    contribution *= 1 + annualStepUpPercent / 100;
  }

  const annuityPurchase = (corpus * annuityPercent) / 100;
  return {
    totalInvested,
    growth: corpus - totalInvested - existingCorpus,
    corpus,
    lumpSum: corpus - annuityPurchase,
    annuityPurchase,
    monthlyPension: (annuityPurchase * annuityRatePercent) / 100 / 12,
    yearlyBreakdown,
  };
}
