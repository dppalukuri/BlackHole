import { monthlyPayment } from './loan-emi';

export interface FixedFloatingInput {
  principal: number;
  tenureMonths: number;
  /** Annual rate during the fixed period, in percent. */
  fixedRate: number;
  fixedMonths: number;
  /** Benchmark (EIBOR, repo rate) today, in percent. */
  benchmarkNow: number;
  /** Where the benchmark is assumed to be when the fixed period ends. */
  benchmarkAtFixEnd: number;
  /** Margin over the benchmark once the fixed loan reverts. */
  marginAfterFix: number;
  /** Margin over the benchmark on the loan that floats from day one. */
  floatingMargin: number;
  /** Lowest rate either floating phase may charge. 0 means no floor. */
  floorRate?: number;
  /** One-off cost of choosing the floating loan, e.g. an early settlement fee. */
  switchCost?: number;
}

export interface LoanLegYearRow {
  year: number;
  rate: number;
  payment: number;
  closingBalance: number;
}

export interface LoanLeg {
  firstRate: number;
  firstPayment: number;
  /** Payment in the month the fixed period ends, on this loan. */
  paymentAtFixEnd: number;
  /** Rate charged in the month the fixed period ends, on this loan. */
  rateAtFixEnd: number;
  totalInterest: number;
  /** Interest plus any one-off cost. This is what the two loans are compared on. */
  totalCost: number;
  yearlyBreakdown: LoanLegYearRow[];
}

export interface BreakEven {
  benchmark: number;
  /** True if fixing is the cheaper loan just above this benchmark level. */
  fixingWinsAbove: boolean;
}

export interface FixedFloatingResult {
  fixedThenFloating: LoanLeg;
  floating: LoanLeg;
  /** Change in the fixed loan's payment at reversion. */
  paymentJump: number;
  paymentJumpPercent: number;
  /** Floating cost minus fixed cost. Positive means fixing is cheaper. */
  costDifference: number;
  /**
   * Benchmark levels at the end of the fixed period, from 0% to
   * BREAK_EVEN_CEILING, at which both loans cost the same. Usually zero or one,
   * but floors and unequal margins can produce more.
   */
  breakEvens: BreakEven[];
}

const BREAK_EVEN_CEILING = 30;
const BREAK_EVEN_SCAN_STEP = 0.5;
const RESET_EVERY_MONTHS = 3;

/**
 * Amortises a loan whose rate may change, re-levelling the payment over the
 * remaining months at every change so the end date holds. That is why a rate
 * rise shows up as a bigger payment here rather than a longer tenure.
 */
function runLoan(
  principal: number,
  tenureMonths: number,
  fixMonth: number,
  oneOffCost: number,
  rateAtMonth: (month: number) => number
): LoanLeg {
  let balance = principal;
  let rate = NaN;
  let payment = 0;
  let totalInterest = 0;
  const firstRate = rateAtMonth(0);
  let firstPayment = 0;
  let paymentAtFixEnd = 0;
  let rateAtFixEnd = 0;
  const yearlyBreakdown: LoanLegYearRow[] = [];

  for (let m = 0; m < tenureMonths; m++) {
    const nextRate = rateAtMonth(m);
    if (nextRate !== rate) {
      rate = nextRate;
      payment = monthlyPayment(balance, rate, tenureMonths - m);
    }
    if (m === 0) firstPayment = payment;
    // With no reversion inside the term, the last month stands in for it.
    if (m === Math.min(fixMonth, tenureMonths - 1)) {
      paymentAtFixEnd = payment;
      rateAtFixEnd = rate;
    }

    const interest = (balance * rate) / 12 / 100;
    totalInterest += interest;
    balance = Math.max(0, balance + interest - payment);

    if ((m + 1) % 12 === 0) {
      yearlyBreakdown.push({ year: (m + 1) / 12, rate, payment, closingBalance: balance });
    }
  }

  return {
    firstRate,
    firstPayment,
    paymentAtFixEnd,
    rateAtFixEnd,
    totalInterest,
    totalCost: totalInterest + oneOffCost,
    yearlyBreakdown,
  };
}

function runBothLegs(input: FixedFloatingInput, benchmarkAtFixEnd: number) {
  const { principal, tenureMonths, fixedRate, benchmarkNow } = input;
  const floor = input.floorRate ?? 0;
  const fixedMonths = Math.max(1, Math.min(input.fixedMonths, tenureMonths));

  // The benchmark drifts in a straight line to the assumed level, then holds.
  const benchmarkAt = (m: number) =>
    benchmarkNow + (benchmarkAtFixEnd - benchmarkNow) * Math.min(1, m / fixedMonths);
  const floated = (benchmark: number, margin: number) => Math.max(floor, benchmark + margin);

  const fixedThenFloating = runLoan(principal, tenureMonths, fixedMonths, 0, (m) =>
    m < fixedMonths ? fixedRate : floated(benchmarkAt(m), input.marginAfterFix)
  );
  const floating = runLoan(principal, tenureMonths, fixedMonths, input.switchCost ?? 0, (m) =>
    floated(benchmarkAt(m - (m % RESET_EVERY_MONTHS)), input.floatingMargin)
  );

  return { fixedThenFloating, floating };
}

/**
 * Compares a loan that is fixed and then reverts to benchmark + margin against
 * one that floats from day one, both ending on the same date. Totals are plain
 * sums of money and are not discounted for when each payment falls due.
 *
 * The floating loan resets quarterly, matching 3-month EIBOR pricing and the
 * RBI's minimum reset frequency for external-benchmark loans.
 */
export function compareFixedFloating(input: FixedFloatingInput): FixedFloatingResult {
  const { fixedThenFloating, floating } = runBothLegs(input, input.benchmarkAtFixEnd);

  const costGapAt = (level: number) => {
    const legs = runBothLegs(input, level);
    return legs.floating.totalCost - legs.fixedThenFloating.totalCost;
  };

  // The gap does not always rise with the benchmark: a floor flattens one side
  // of it, and a lower floating margin can outweigh the floating loan's longer
  // exposure. So scan for every crossing instead of assuming there is one.
  const breakEvens: BreakEven[] = [];
  let prevLevel = 0;
  let prevGap = costGapAt(0);
  for (let level = BREAK_EVEN_SCAN_STEP; level <= BREAK_EVEN_CEILING; level += BREAK_EVEN_SCAN_STEP) {
    const gap = costGapAt(level);
    if (prevGap < 0 !== gap < 0) {
      let lo = prevLevel;
      let hi = level;
      for (let i = 0; i < 30; i++) {
        const mid = (lo + hi) / 2;
        if (costGapAt(mid) < 0 === prevGap < 0) lo = mid;
        else hi = mid;
      }
      breakEvens.push({ benchmark: (lo + hi) / 2, fixingWinsAbove: gap > prevGap });
    }
    prevLevel = level;
    prevGap = gap;
  }

  const paymentJump = fixedThenFloating.paymentAtFixEnd - fixedThenFloating.firstPayment;

  return {
    fixedThenFloating,
    floating,
    paymentJump,
    paymentJumpPercent: (paymentJump / fixedThenFloating.firstPayment) * 100,
    costDifference: floating.totalCost - fixedThenFloating.totalCost,
    breakEvens,
  };
}
