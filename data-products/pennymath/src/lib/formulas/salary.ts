import { indiaIncomeTaxNewRegime, indiaIncomeTaxOldRegime } from './tax-slab';

/** Statutory wage ceiling for mandatory EPF contributions, per month. */
export const EPF_WAGE_CEILING = 15000;
const EPF_RATE = 0.12;
/** Commonly used gratuity provision: 15/26 of a month's basic per year. */
const GRATUITY_RATE = 15 / 26 / 12;

export interface SalaryInput {
  annualCtc: number;
  /** Basic pay as a percent of CTC. */
  basicPercent: number;
  /** Yearly bonus or variable pay inside the CTC, assumed paid in full. */
  annualVariable: number;
  /** 'capped' uses the wage ceiling for EPF. 'full' uses all of basic. */
  pfBasis: 'capped' | 'full';
  includeGratuityInCtc: boolean;
  monthlyProfessionalTax: number;
  regime: 'new' | 'old';
  /** Old regime only: 80C, HRA exemption and any other deductions. */
  oldRegimeDeductions: number;
}

export interface SalaryResult {
  annualBasic: number;
  employerPf: number;
  employeePf: number;
  gratuityProvision: number;
  /** CTC less employer PF and any gratuity provision. */
  grossSalary: number;
  professionalTax: number;
  incomeTax: number;
  /** Salary paid out over the year, including variable pay. */
  annualTakeHome: number;
  /** A typical month's pay, leaving out variable pay and its tax. */
  monthlyInHand: number;
}

function taxFor(gross: number, input: SalaryInput) {
  // Employee PF qualifies under 80C only in the old regime. Professional tax is
  // deductible there as well. Neither is deductible in the new regime.
  if (input.regime === 'new') return indiaIncomeTaxNewRegime(gross).totalTaxWithCess;
  return indiaIncomeTaxOldRegime(gross, input.oldRegimeDeductions + input.monthlyProfessionalTax * 12).totalTaxWithCess;
}

/**
 * Splits a CTC into take-home pay. Surcharge on incomes above 50 lakh is left
 * out, and pages using this say so.
 */
export function salaryBreakdown(input: SalaryInput): SalaryResult {
  const { annualCtc, basicPercent, annualVariable, pfBasis, includeGratuityInCtc } = input;
  const annualBasic = (annualCtc * basicPercent) / 100;
  const pfWages = pfBasis === 'capped' ? Math.min(annualBasic, EPF_WAGE_CEILING * 12) : annualBasic;
  const employerPf = pfWages * EPF_RATE;
  const employeePf = employerPf;
  const gratuityProvision = includeGratuityInCtc ? annualBasic * GRATUITY_RATE : 0;

  const grossSalary = annualCtc - employerPf - gratuityProvision;
  const professionalTax = input.monthlyProfessionalTax * 12;
  const incomeTax = taxFor(grossSalary, input);
  const annualTakeHome = grossSalary - employeePf - professionalTax - incomeTax;

  // Monthly pay excludes the bonus, so the tax on the bonus is taken out with it.
  const taxWithoutVariable = taxFor(grossSalary - annualVariable, input);
  const monthlyInHand = (grossSalary - annualVariable - employeePf - professionalTax - taxWithoutVariable) / 12;

  return {
    annualBasic,
    employerPf,
    employeePf,
    gratuityProvision,
    grossSalary,
    professionalTax,
    incomeTax,
    annualTakeHome,
    monthlyInHand,
  };
}
