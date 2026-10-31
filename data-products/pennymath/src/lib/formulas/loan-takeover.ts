import { monthlyPayment } from './loan-emi';

export interface LoanTakeoverInput {
  balance: number;
  currentRate: number;
  remainingMonths: number;
  newRate: number;
  newTenureMonths: number;
  /** Charged by the current lender for leaving. */
  exitFee: number;
  /** Processing, valuation, registration and legal costs on the new loan. */
  newLoanCosts: number;
}

export interface LoanTakeoverResult {
  currentPayment: number;
  newPayment: number;
  monthlySaving: number;
  currentInterest: number;
  newInterest: number;
  totalFees: number;
  /** Interest saved minus all fees. Negative means the move loses money. */
  netSaving: number;
  /**
   * First month in which you would be ahead if you sold or repaid at that point,
   * counting payments made, debt left and fees. Null if that never happens.
   */
  breakEvenMonth: number | null;
}

/**
 * Compares staying on the current loan with moving it to a new lender. The fees
 * are paid upfront, in cash.
 *
 * Break-even compares what each path has cost by a given month, including the
 * balance still owed. Comparing monthly payments alone would flatter a longer
 * new tenure, whose lower payment comes partly from repaying debt more slowly.
 */
export function compareLoanTakeover(input: LoanTakeoverInput): LoanTakeoverResult {
  const { balance, currentRate, remainingMonths, newRate, newTenureMonths } = input;
  const totalFees = input.exitFee + input.newLoanCosts;
  const currentPayment = monthlyPayment(balance, currentRate, remainingMonths);
  const newPayment = monthlyPayment(balance, newRate, newTenureMonths);

  let oldBalance = balance;
  let newBalance = balance;
  let oldPaid = 0;
  let newPaid = 0;
  let breakEvenMonth: number | null = null;
  const horizon = Math.max(remainingMonths, newTenureMonths);

  for (let m = 1; m <= horizon; m++) {
    if (m <= remainingMonths) {
      oldBalance = Math.max(0, oldBalance * (1 + currentRate / 1200) - currentPayment);
      oldPaid += currentPayment;
    }
    if (m <= newTenureMonths) {
      newBalance = Math.max(0, newBalance * (1 + newRate / 1200) - newPayment);
      newPaid += newPayment;
    }
    if (breakEvenMonth === null && oldPaid + oldBalance >= newPaid + newBalance + totalFees) {
      breakEvenMonth = m;
    }
  }

  const currentInterest = currentPayment * remainingMonths - balance;
  const newInterest = newPayment * newTenureMonths - balance;

  return {
    currentPayment,
    newPayment,
    monthlySaving: currentPayment - newPayment,
    currentInterest,
    newInterest,
    totalFees,
    netSaving: currentInterest - newInterest - totalFees,
    breakEvenMonth,
  };
}
