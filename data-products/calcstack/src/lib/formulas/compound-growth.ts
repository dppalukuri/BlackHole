export interface CompoundGrowthResult {
  investedAmount: number;
  estimatedReturns: number;
  totalValue: number;
  yearlyBreakdown: Array<{
    year: number;
    invested: number;
    returns: number;
    total: number;
  }>;
}

/** SIP future value — periodic monthly investment compounding monthly */
export function sipFutureValue(
  monthlyInvestment: number,
  annualRate: number,
  years: number
): CompoundGrowthResult {
  const monthlyRate = annualRate / 12 / 100;
  const months = years * 12;

  let totalValue = 0;
  if (monthlyRate === 0) {
    totalValue = monthlyInvestment * months;
  } else {
    totalValue =
      monthlyInvestment *
      ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate) *
      (1 + monthlyRate);
  }

  const investedAmount = monthlyInvestment * months;
  const estimatedReturns = totalValue - investedAmount;

  const yearlyBreakdown = [];
  for (let y = 1; y <= years; y++) {
    const m = y * 12;
    let yTotal = 0;
    if (monthlyRate === 0) {
      yTotal = monthlyInvestment * m;
    } else {
      yTotal =
        monthlyInvestment *
        ((Math.pow(1 + monthlyRate, m) - 1) / monthlyRate) *
        (1 + monthlyRate);
    }
    yearlyBreakdown.push({
      year: y,
      invested: monthlyInvestment * m,
      returns: yTotal - monthlyInvestment * m,
      total: yTotal,
    });
  }

  return { investedAmount, estimatedReturns, totalValue, yearlyBreakdown };
}

/** Lump sum compound interest */
export function lumpSumFutureValue(
  principal: number,
  annualRate: number,
  years: number,
  compoundingFrequency: number = 12
): CompoundGrowthResult {
  const r = annualRate / 100;
  const n = compoundingFrequency;
  const totalValue = principal * Math.pow(1 + r / n, n * years);
  const investedAmount = principal;
  const estimatedReturns = totalValue - investedAmount;

  const yearlyBreakdown = [];
  for (let y = 1; y <= years; y++) {
    const yTotal = principal * Math.pow(1 + r / n, n * y);
    yearlyBreakdown.push({
      year: y,
      invested: principal,
      returns: yTotal - principal,
      total: yTotal,
    });
  }

  return { investedAmount, estimatedReturns, totalValue, yearlyBreakdown };
}

/** PPF calculator — annual deposits, compounding annually at fixed rate */
export function ppfFutureValue(
  yearlyDeposit: number,
  annualRate: number,
  years: number
): CompoundGrowthResult {
  const r = annualRate / 100;
  let totalValue = 0;
  const yearlyBreakdown = [];

  for (let y = 1; y <= years; y++) {
    totalValue = (totalValue + yearlyDeposit) * (1 + r);
    yearlyBreakdown.push({
      year: y,
      invested: yearlyDeposit * y,
      returns: totalValue - yearlyDeposit * y,
      total: totalValue,
    });
  }

  const investedAmount = yearlyDeposit * years;
  const estimatedReturns = totalValue - investedAmount;

  return { investedAmount, estimatedReturns, totalValue, yearlyBreakdown };
}
