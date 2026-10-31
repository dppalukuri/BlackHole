import { monthlyPayment } from './loan-emi';

export interface PrepaymentInput {
  balance: number;
  annualRate: number;
  remainingMonths: number;
  /** Paid today, on top of the regular payment. */
  lumpSum: number;
  /** Paid every month on top of the regular payment. */
  extraMonthly: number;
  /** One-off fee charged for prepaying. */
  fee: number;
}

export interface PrepaymentOption {
  payment: number;
  months: number;
  totalInterest: number;
  /** Interest saved against making no prepayment, after the fee. */
  netSaving: number;
}

export interface PrepaymentResult {
  baselinePayment: number;
  baselineInterest: number;
  /** Keep paying the same amount, and finish the loan sooner. */
  shorterTerm: PrepaymentOption;
  /** Keep the end date, and lower the payment. Extra monthly still goes on top. */
  lowerPayment: PrepaymentOption;
}

/** Runs a loan at a fixed monthly outflow until it clears. */
function amortise(balance: number, annualRate: number, outflow: number, maxMonths: number) {
  const i = annualRate / 1200;
  let remaining = balance;
  let months = 0;
  let totalInterest = 0;
  while (remaining > 0.005 && months < maxMonths) {
    const interest = remaining * i;
    totalInterest += interest;
    remaining = remaining + interest - Math.min(outflow, remaining + interest);
    months++;
  }
  return { months, totalInterest };
}

/**
 * Models a lump sum today and an optional monthly top-up, assuming the rate holds.
 * Tracking the months avoids a closed form that breaks when a part-payment
 * clears the loan outright.
 */
export function comparePrepayment(input: PrepaymentInput): PrepaymentResult {
  const { balance, annualRate, remainingMonths, extraMonthly, fee } = input;
  const lumpSum = Math.min(input.lumpSum, balance);
  const after = balance - lumpSum;

  const baselinePayment = monthlyPayment(balance, annualRate, remainingMonths);
  const baselineInterest = baselinePayment * remainingMonths - balance;
  const option = (payment: number): PrepaymentOption => {
    const run = amortise(after, annualRate, payment + extraMonthly, remainingMonths);
    return {
      payment,
      months: run.months,
      totalInterest: run.totalInterest,
      netSaving: baselineInterest - run.totalInterest - fee,
    };
  };

  return {
    baselinePayment,
    baselineInterest,
    shorterTerm: option(baselinePayment),
    lowerPayment: option(monthlyPayment(after, annualRate, remainingMonths)),
  };
}
