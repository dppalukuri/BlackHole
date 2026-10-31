import { monthlyPayment } from './loan-emi';

export interface RentVsBuyInput {
  price: number;
  /** Down payment as a percent of the price. */
  downPercent: number;
  annualRate: number;
  tenureMonths: number;
  /** Paid on purchase, as a percent of the price. */
  buyingCostPercent: number;
  /** Paid on sale, as a percent of the sale price. */
  sellingCostPercent: number;
  /** Maintenance, service charges and insurance, as a percent of the price a year. */
  ownershipCostPercent: number;
  appreciationPercent: number;
  monthlyRent: number;
  rentGrowthPercent: number;
  /** Return on the money either household invests instead. */
  investmentReturnPercent: number;
  years: number;
}

export interface RentVsBuyYear {
  year: number;
  buyerNetWorth: number;
  renterNetWorth: number;
}

export interface RentVsBuyResult {
  upfrontCash: number;
  monthlyLoanPayment: number;
  firstYearOwnershipCost: number;
  yearly: RentVsBuyYear[];
  buyerNetWorth: number;
  renterNetWorth: number;
  /** Buyer minus renter at the end. Positive means buying comes out ahead. */
  advantage: number;
  /**
   * First year from which buying stays ahead through to the end of the period.
   * Null if buying is behind at the end.
   */
  breakEvenYear: number | null;
}

/**
 * Compares two households with the same budget. Both start with enough cash to
 * buy. The renter invests it instead. Each month, whichever household has lower
 * housing costs invests the difference, so the comparison never depends on
 * one household simply spending less.
 *
 * Buyer net worth assumes a sale at that date: home value less selling costs,
 * less the loan balance, plus anything the buyer has invested.
 * Tax is left out, as is any rental income or home loan tax relief.
 */
export function compareRentVsBuy(input: RentVsBuyInput): RentVsBuyResult {
  const {
    price, annualRate, tenureMonths, monthlyRent, years,
    buyingCostPercent, sellingCostPercent, ownershipCostPercent,
    appreciationPercent, rentGrowthPercent, investmentReturnPercent,
  } = input;

  const loan = price * (1 - input.downPercent / 100);
  const upfrontCash = price - loan + (price * buyingCostPercent) / 100;
  const payment = loan > 0 ? monthlyPayment(loan, annualRate, tenureMonths) : 0;
  const investMonthly = Math.pow(1 + investmentReturnPercent / 100, 1 / 12) - 1;
  const homeMonthly = Math.pow(1 + appreciationPercent / 100, 1 / 12) - 1;

  let balance = loan;
  let homeValue = price;
  let rent = monthlyRent;
  let ownershipCost = (price * ownershipCostPercent) / 1200;
  let renterPot = upfrontCash;
  let buyerPot = 0;
  const yearly: RentVsBuyYear[] = [];

  for (let m = 1; m <= years * 12; m++) {
    const interest = balance * (annualRate / 1200);
    const loanOutflow = m <= tenureMonths ? payment : 0;
    if (m <= tenureMonths) balance = Math.max(0, balance + interest - payment);

    const buyerCost = loanOutflow + ownershipCost;
    renterPot = renterPot * (1 + investMonthly) + Math.max(0, buyerCost - rent);
    buyerPot = buyerPot * (1 + investMonthly) + Math.max(0, rent - buyerCost);
    homeValue *= 1 + homeMonthly;

    if (m % 12 === 0) {
      rent *= 1 + rentGrowthPercent / 100;
      ownershipCost *= 1 + appreciationPercent / 100;
      yearly.push({
        year: m / 12,
        buyerNetWorth: homeValue * (1 - sellingCostPercent / 100) - balance + buyerPot,
        renterNetWorth: renterPot,
      });
    }
  }

  const last = yearly[yearly.length - 1];
  let breakEvenYear: number | null = null;
  if (last.buyerNetWorth > last.renterNetWorth) {
    breakEvenYear = last.year;
    for (let i = yearly.length - 2; i >= 0 && yearly[i].buyerNetWorth > yearly[i].renterNetWorth; i--) {
      breakEvenYear = yearly[i].year;
    }
  }

  return {
    upfrontCash,
    monthlyLoanPayment: payment,
    firstYearOwnershipCost: (price * ownershipCostPercent) / 100,
    yearly,
    buyerNetWorth: last.buyerNetWorth,
    renterNetWorth: last.renterNetWorth,
    advantage: last.buyerNetWorth - last.renterNetWorth,
    breakEvenYear,
  };
}
