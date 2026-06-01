export interface EMIResult {
  emi: number;
  totalPayment: number;
  totalInterest: number;
  schedule: Array<{
    month: number;
    principal: number;
    interest: number;
    balance: number;
  }>;
}

/** EMI calculation with amortization schedule */
export function calculateEMI(
  principal: number,
  annualRate: number,
  tenureMonths: number
): EMIResult {
  const monthlyRate = annualRate / 12 / 100;

  let emi: number;
  if (monthlyRate === 0) {
    emi = principal / tenureMonths;
  } else {
    emi =
      (principal * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) /
      (Math.pow(1 + monthlyRate, tenureMonths) - 1);
  }

  const totalPayment = emi * tenureMonths;
  const totalInterest = totalPayment - principal;

  const schedule = [];
  let balance = principal;
  for (let m = 1; m <= tenureMonths; m++) {
    const interestPortion = balance * monthlyRate;
    const principalPortion = emi - interestPortion;
    balance = balance - principalPortion;
    schedule.push({
      month: m,
      principal: principalPortion,
      interest: interestPortion,
      balance: Math.max(0, balance),
    });
  }

  return { emi, totalPayment, totalInterest, schedule };
}
