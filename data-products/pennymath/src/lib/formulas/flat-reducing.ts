import { monthlyPayment } from './loan-emi';

export interface LoanCost {
  /** Monthly instalment. */
  emi: number;
  totalInterest: number;
  /** Loan plus interest. */
  totalAmount: number;
}

export interface FlatReducingResult {
  flat: LoanCost;
  /** The same quoted rate, charged on the reducing balance. */
  reducing: LoanCost;
  /** Reducing-balance rate per year whose instalment equals the flat-rate instalment. */
  equivalentReducingRate: number;
}

/** Flat rate: interest on the full loan for the whole tenure, split evenly over the months. */
export function flatRateLoan(principal: number, annualRate: number, months: number): LoanCost {
  const totalInterest = (principal * annualRate * months) / 1200;
  const totalAmount = principal + totalInterest;
  return { emi: totalAmount / months, totalInterest, totalAmount };
}

/** Reducing balance: each month's interest is charged only on what is still owed. */
export function reducingRateLoan(principal: number, annualRate: number, months: number): LoanCost {
  const emi = monthlyPayment(principal, annualRate, months);
  return { emi, totalInterest: emi * months - principal, totalAmount: emi * months };
}

/**
 * The reducing-balance rate that costs the same as a flat rate: the rate whose
 * instalment matches the flat-rate instalment, found by bisection.
 */
export function equivalentReducingRate(principal: number, flatRate: number, months: number): number {
  if (principal <= 0 || flatRate <= 0 || months <= 0) return 0;
  const target = flatRateLoan(principal, flatRate, months).emi;
  let lo = 0;
  let hi = Math.max(1, flatRate * 4);
  while (monthlyPayment(principal, hi, months) < target) hi *= 2;
  for (let i = 0; i < 100; i++) {
    const mid = (lo + hi) / 2;
    if (monthlyPayment(principal, mid, months) < target) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

export function compareFlatReducing(principal: number, annualRate: number, months: number): FlatReducingResult {
  return {
    flat: flatRateLoan(principal, annualRate, months),
    reducing: reducingRateLoan(principal, annualRate, months),
    equivalentReducingRate: equivalentReducingRate(principal, annualRate, months),
  };
}
