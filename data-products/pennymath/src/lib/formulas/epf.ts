import { EPF_WAGE_CEILING } from './salary';

const CONTRIBUTION_RATE = 0.12;
/** Part of the employer's 12% that goes to the pension scheme, on capped wages. */
const EPS_RATE = 0.0833;

export interface EpfInput {
  currentAge: number;
  retirementAge: number;
  monthlyBasic: number;
  annualRaisePercent: number;
  /** 'capped' contributes on wages up to the ceiling. 'full' on all of basic. */
  pfBasis: 'capped' | 'full';
  existingBalance: number;
  interestRatePercent: number;
}

export interface EpfYearRow {
  age: number;
  employee: number;
  employer: number;
  interest: number;
  closingBalance: number;
}

export interface EpfResult {
  firstMonthEmployee: number;
  firstMonthEmployerEpf: number;
  firstMonthEps: number;
  totalEmployee: number;
  totalEmployer: number;
  totalInterest: number;
  finalBalance: number;
  yearlyBreakdown: EpfYearRow[];
}

/** One month's split. EPS comes out of the employer's share, on capped wages. */
function monthlySplit(basic: number, pfBasis: EpfInput['pfBasis']) {
  const wages = pfBasis === 'capped' ? Math.min(basic, EPF_WAGE_CEILING) : basic;
  const employee = wages * CONTRIBUTION_RATE;
  const eps = Math.min(wages, EPF_WAGE_CEILING) * EPS_RATE;
  return { employee, employerEpf: employee - eps, eps };
}

/**
 * EPF balance projection. Interest accrues on the running monthly balance and is
 * credited at the end of each year, so a month's contribution starts earning the
 * following month. Pension from EPS is not part of this balance.
 */
export function epfProjection(input: EpfInput): EpfResult {
  const { currentAge, retirementAge, annualRaisePercent, pfBasis, existingBalance, interestRatePercent } = input;
  const years = Math.max(0, retirementAge - currentAge);
  const monthlyRate = interestRatePercent / 1200;

  let basic = input.monthlyBasic;
  let balance = existingBalance;
  let totalEmployee = 0;
  let totalEmployer = 0;
  let totalInterest = 0;
  const yearlyBreakdown: EpfYearRow[] = [];
  const first = monthlySplit(basic, pfBasis);

  for (let y = 1; y <= years; y++) {
    const { employee, employerEpf } = monthlySplit(basic, pfBasis);
    let interest = 0;
    for (let m = 0; m < 12; m++) {
      interest += balance * monthlyRate;
      balance += employee + employerEpf;
    }
    balance += interest;
    totalEmployee += employee * 12;
    totalEmployer += employerEpf * 12;
    totalInterest += interest;
    yearlyBreakdown.push({ age: currentAge + y, employee: employee * 12, employer: employerEpf * 12, interest, closingBalance: balance });
    basic *= 1 + annualRaisePercent / 100;
  }

  return {
    firstMonthEmployee: first.employee,
    firstMonthEmployerEpf: first.employerEpf,
    firstMonthEps: first.eps,
    totalEmployee,
    totalEmployer,
    totalInterest,
    finalBalance: balance,
    yearlyBreakdown,
  };
}
