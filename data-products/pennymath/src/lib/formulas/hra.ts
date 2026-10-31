export type HraCityGroup = 'original-metro' | 'new-metro' | 'other';
export type HraYear = 'fy-2026-27' | 'fy-2025-26';

/**
 * Share of salary allowed in the "percent of salary" test. Bengaluru, Hyderabad,
 * Pune and Ahmedabad moved to 50% from FY 2026-27 under the Income-tax Rules, 2026.
 */
export function hraSalaryPercent(city: HraCityGroup, year: HraYear): number {
  if (city === 'original-metro') return 50;
  if (city === 'new-metro' && year === 'fy-2026-27') return 50;
  return 40;
}

export interface HraInput {
  /** Basic pay plus any dearness allowance that counts for retirement benefits. */
  annualSalary: number;
  annualHraReceived: number;
  annualRentPaid: number;
  city: HraCityGroup;
  year: HraYear;
}

export interface HraResult {
  salaryPercent: number;
  /** The three limits. The exemption is the lowest. */
  actualHra: number;
  rentMinusTenPercent: number;
  percentOfSalary: number;
  exempt: number;
  taxable: number;
  limitedBy: 'actual-hra' | 'rent' | 'salary';
}

/** HRA exemption: the lowest of HRA received, rent less 10% of salary, or 40-50% of salary. */
export function hraExemption(input: HraInput): HraResult {
  const { annualSalary, annualHraReceived, annualRentPaid, city, year } = input;
  const salaryPercent = hraSalaryPercent(city, year);
  const rentMinusTenPercent = Math.max(0, annualRentPaid - annualSalary * 0.1);
  const percentOfSalary = (annualSalary * salaryPercent) / 100;
  const exempt = Math.min(annualHraReceived, rentMinusTenPercent, percentOfSalary);

  let limitedBy: HraResult['limitedBy'] = 'actual-hra';
  if (exempt === rentMinusTenPercent && exempt < annualHraReceived) limitedBy = 'rent';
  else if (exempt === percentOfSalary && exempt < annualHraReceived) limitedBy = 'salary';

  return {
    salaryPercent,
    actualHra: annualHraReceived,
    rentMinusTenPercent,
    percentOfSalary,
    exempt,
    taxable: annualHraReceived - exempt,
    limitedBy,
  };
}
