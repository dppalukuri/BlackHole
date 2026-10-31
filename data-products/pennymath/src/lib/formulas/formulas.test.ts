import { describe, it, expect } from 'vitest';
import { sipFutureValue, lumpSumFutureValue, ppfFutureValue } from './compound-growth';
import { calculateEMI } from './loan-emi';
import { uaeGratuity, indiaGratuity, calculateVAT } from './flat-rate';
import { indiaIncomeTaxNewRegime, indiaIncomeTaxOldRegime } from './tax-slab';
import { swpProjection } from './swp';
import { fireProjection } from './fire';
import { stepUpSipProjection } from './step-up-sip';
import { compareFixedFloating } from './fixed-floating';
import { salaryBreakdown } from './salary';
import { compareRentVsBuy } from './rent-vs-buy';
import { maxAffordability, INDIA_LTV_TIERS } from './affordability';
import { dubaiPurchaseCosts } from './dubai-purchase-costs';
import { comparePrepayment } from './prepayment';
import { compareLoanTakeover } from './loan-takeover';

/**
 * These calculators are the product. A wrong number here is the one defect
 * that destroys trust, so each formula is pinned against an independently
 * derived closed form, an accounting identity, or a published statutory
 * example — not against whatever the code happened to return.
 */

describe('sipFutureValue', () => {
  it('matches the closed-form annuity-due future value', () => {
    const P = 5000, r = 0.12 / 12, n = 120;
    const expected = P * ((Math.pow(1 + r, n) - 1) / r) * (1 + r);
    expect(sipFutureValue(5000, 12, 10).totalValue).toBeCloseTo(expected, 6);
  });

  it('invested + returns reconciles to total value', () => {
    const r = sipFutureValue(5000, 12, 10);
    expect(r.investedAmount + r.estimatedReturns).toBeCloseTo(r.totalValue, 6);
    expect(r.investedAmount).toBe(5000 * 120);
  });

  it('degenerates to plain contributions at 0%', () => {
    const r = sipFutureValue(1000, 0, 5);
    expect(r.totalValue).toBe(1000 * 60);
    expect(r.estimatedReturns).toBe(0);
  });

  it('emits one breakdown row per year, increasing monotonically', () => {
    const rows = sipFutureValue(5000, 12, 10).yearlyBreakdown;
    expect(rows).toHaveLength(10);
    for (let i = 1; i < rows.length; i++) {
      expect(rows[i].total).toBeGreaterThan(rows[i - 1].total);
    }
  });
});

describe('lumpSumFutureValue', () => {
  it('matches P(1 + r/n)^(nt)', () => {
    expect(lumpSumFutureValue(100000, 12, 10).totalValue).toBeCloseTo(
      100000 * Math.pow(1 + 0.12 / 12, 120), 6);
  });

  it('doubles at roughly the rule-of-72 horizon', () => {
    // 12% p.a. compounded monthly doubles in ~5.8 years
    const v = lumpSumFutureValue(100000, 12, 5.8).totalValue;
    expect(v / 100000).toBeGreaterThan(1.95);
    expect(v / 100000).toBeLessThan(2.05);
  });

  it('respects the compounding frequency argument', () => {
    const annual = lumpSumFutureValue(100000, 12, 10, 1).totalValue;
    const monthly = lumpSumFutureValue(100000, 12, 10, 12).totalValue;
    expect(monthly).toBeGreaterThan(annual);
    expect(annual).toBeCloseTo(100000 * Math.pow(1.12, 10), 6);
  });
});

describe('ppfFutureValue', () => {
  it('compounds annual deposits at the statutory rate', () => {
    // Deposit at the start of each year, credited interest at year end.
    let expected = 0;
    for (let y = 0; y < 15; y++) expected = (expected + 150000) * 1.071;
    expect(ppfFutureValue(150000, 7.1, 15).totalValue).toBeCloseTo(expected, 6);
  });

  it('reconciles invested against returns', () => {
    const r = ppfFutureValue(150000, 7.1, 15);
    expect(r.investedAmount).toBe(150000 * 15);
    expect(r.investedAmount + r.estimatedReturns).toBeCloseTo(r.totalValue, 6);
  });
});

describe('calculateEMI', () => {
  it('matches the standard amortisation formula', () => {
    const P = 5000000, r = 0.085 / 12, n = 240;
    const expected = (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
    expect(calculateEMI(5000000, 8.5, 240).emi).toBeCloseTo(expected, 6);
  });

  it('amortises the balance to zero by the final instalment', () => {
    const r = calculateEMI(5000000, 8.5, 240);
    expect(r.schedule).toHaveLength(240);
    expect(r.schedule[239].balance).toBeCloseTo(0, 4);
  });

  it('shifts each instalment from interest toward principal', () => {
    const s = calculateEMI(5000000, 8.5, 240).schedule;
    expect(s[0].interest).toBeGreaterThan(s[0].principal);
    expect(s[239].principal).toBeGreaterThan(s[239].interest);
  });

  it('splits principal evenly and charges no interest at 0%', () => {
    const r = calculateEMI(120000, 0, 12);
    expect(r.emi).toBe(10000);
    expect(r.totalInterest).toBeCloseTo(0, 6);
  });

  it('reconciles total payment against principal and interest', () => {
    const r = calculateEMI(5000000, 8.5, 240);
    expect(r.totalInterest).toBeCloseTo(r.totalPayment - 5000000, 6);
  });
});

describe('uaeGratuity (Federal Decree-Law No. 33 of 2021)', () => {
  it('pays nothing below one year of service', () => {
    expect(uaeGratuity(10000, 0.9).gratuityAmount).toBe(0);
  });

  it('accrues 21 days per year for the first five years', () => {
    expect(uaeGratuity(30000, 3).gratuityAmount).toBeCloseTo((30000 / 30) * 21 * 3, 6);
  });

  it('accrues 30 days per year beyond five years', () => {
    const daily = 30000 / 30;
    expect(uaeGratuity(30000, 8).gratuityAmount).toBeCloseTo(daily * 21 * 5 + daily * 30 * 3, 6);
  });

  it('caps the award at two years of salary', () => {
    expect(uaeGratuity(10000, 40).gratuityAmount).toBe(10000 * 24);
  });
});

describe('indiaGratuity (Payment of Gratuity Act, 1972)', () => {
  it('requires five years of service', () => {
    expect(indiaGratuity(50000, 4.9).gratuityAmount).toBe(0);
  });

  it('applies the 15/26 formula', () => {
    expect(indiaGratuity(50000, 10).gratuityAmount).toBeCloseTo((15 * 50000 * 10) / 26, 6);
  });

  it('caps the award at 20 lakh', () => {
    expect(indiaGratuity(500000, 30).gratuityAmount).toBe(2000000);
  });
});

describe('calculateVAT', () => {
  it('adds VAT to an exclusive amount', () => {
    const r = calculateVAT(1000, 5);
    expect(r.vatAmount).toBeCloseTo(50, 6);
    expect(r.totalAmount).toBeCloseTo(1050, 6);
  });

  it('extracts VAT from an inclusive amount', () => {
    const r = calculateVAT(1050, 5, true);
    expect(r.netAmount).toBeCloseTo(1000, 6);
    expect(r.vatAmount).toBeCloseTo(50, 6);
  });

  it('round-trips exclusive -> inclusive', () => {
    const gross = calculateVAT(2399, 5).totalAmount;
    expect(calculateVAT(gross, 5, true).netAmount).toBeCloseTo(2399, 6);
  });
});

describe('indiaIncomeTaxNewRegime', () => {
  it('applies the 75,000 standard deduction', () => {
    expect(indiaIncomeTaxNewRegime(1000000).taxableIncome).toBe(925000);
  });

  it('levies no tax up to the 87A rebate ceiling', () => {
    // 12,00,000 taxable + 75,000 standard deduction
    expect(indiaIncomeTaxNewRegime(1275000).totalTaxWithCess).toBe(0);
  });

  it('taxes the first rupee past the rebate ceiling', () => {
    expect(indiaIncomeTaxNewRegime(1275001).totalTaxWithCess).toBeGreaterThan(0);
  });

  it('applies marginal relief just past the rebate ceiling', () => {
    // 12,10,000 taxable: slab tax is 61,500, but relief caps it at the 10,000 excess.
    expect(indiaIncomeTaxNewRegime(1285000).totalTax).toBe(10000);
    // By 12,75,000 taxable the slab tax of 71,250 is below the 75,000 excess.
    expect(indiaIncomeTaxNewRegime(1350000).totalTax).toBe(71250);
  });

  it('sums the slabs progressively', () => {
    // taxable 20,00,000: 4L nil + 4L@5% + 4L@10% + 4L@15% + 4L@20%
    const expected = 400000 * 0.05 + 400000 * 0.1 + 400000 * 0.15 + 400000 * 0.2;
    const r = indiaIncomeTaxNewRegime(2075000);
    expect(r.totalTax).toBeCloseTo(expected, 6);
  });

  it('adds 4% health and education cess', () => {
    const r = indiaIncomeTaxNewRegime(2075000);
    expect(r.cess).toBeCloseTo(r.totalTax * 0.04, 6);
    expect(r.totalTaxWithCess).toBeCloseTo(r.totalTax * 1.04, 6);
  });

  it('keeps the effective rate below the top marginal rate', () => {
    const r = indiaIncomeTaxNewRegime(5000000);
    expect(r.effectiveRate).toBeGreaterThan(0);
    expect(r.effectiveRate).toBeLessThan(31.2);
  });

  it('handles zero income without dividing by zero', () => {
    const r = indiaIncomeTaxNewRegime(0);
    expect(r.totalTaxWithCess).toBe(0);
    expect(r.effectiveRate).toBe(0);
  });
});

describe('indiaIncomeTaxOldRegime', () => {
  it('applies the 50,000 standard deduction and other deductions', () => {
    expect(indiaIncomeTaxOldRegime(1000000, 150000).taxableIncome).toBe(800000);
  });

  it('levies no tax when taxable income is within the 87A limit', () => {
    expect(indiaIncomeTaxOldRegime(550000).totalTaxWithCess).toBe(0);
  });

  it('sums the slabs progressively with cess', () => {
    // 12,00,000 taxable: 12,500 + 1,00,000 + 60,000 = 1,72,500, plus 4% cess.
    const r = indiaIncomeTaxOldRegime(1250000);
    expect(r.totalTax).toBe(172500);
    expect(r.totalTaxWithCess).toBeCloseTo(179400, 6);
  });
});

describe('swpProjection', () => {
  it('matches the closed form while the corpus survives', () => {
    const P = 1000000, W = 8000, i = 0.08 / 12, n = 120;
    const expected = P * Math.pow(1 + i, n) - W * ((Math.pow(1 + i, n) - 1) / i);
    expect(swpProjection(1000000, 8000, 8, 10).finalBalance).toBeCloseTo(expected, 4);
  });

  it('reconciles withdrawals, returns and closing balance', () => {
    const r = swpProjection(1000000, 8000, 8, 10);
    expect(r.finalBalance + r.totalWithdrawn - r.investedAmount).toBeCloseTo(r.estimatedReturns, 4);
  });

  it('survives a 0% return, where the closed form divides by zero', () => {
    const r = swpProjection(1200000, 10000, 0, 10);
    expect(r.monthsLasted).toBe(120);
    expect(r.finalBalance).toBe(0);
    expect(r.totalWithdrawn).toBeCloseTo(1200000, 6);
  });

  it('stops at zero instead of going negative when over-withdrawn', () => {
    const r = swpProjection(500000, 20000, 8, 10);
    expect(r.depleted).toBe(true);
    expect(r.depletedAtMonth).toBe(28);
    expect(r.finalBalance).toBe(0);
    expect(r.yearlyBreakdown.every((y) => y.closingBalance >= 0)).toBe(true);
  });

  it('never reports more withdrawn than the corpus could fund', () => {
    const r = swpProjection(500000, 20000, 8, 10);
    expect(r.totalWithdrawn).toBeCloseTo(r.investedAmount + r.estimatedReturns, 4);
  });

  it('preserves capital at exactly the sustainable withdrawal', () => {
    const r0 = swpProjection(1000000, 0, 8, 1);
    const r = swpProjection(1000000, r0.sustainableWithdrawal, 8, 30);
    expect(r.finalBalance).toBeCloseTo(1000000, 4);
    expect(r.depleted).toBe(false);
  });

  it('truncates the table at depletion rather than padding empty years', () => {
    expect(swpProjection(500000, 20000, 8, 10).yearlyBreakdown).toHaveLength(3);
  });
});

describe('fireProjection', () => {
  const base = {
    monthlyExpenses: 50000,
    currentSavings: 500000,
    monthlySavings: 30000,
    expectedReturn: 12,
    inflationRate: 6,
    withdrawalRate: 3,
    currentAge: 28,
  };

  it('derives the FIRE number from annual expenses and withdrawal rate', () => {
    const r = fireProjection(base);
    expect(r.annualExpenses).toBe(600000);
    expect(r.fireNumber).toBeCloseTo(600000 / 0.03, 6);
  });

  it('deflates the nominal return by inflation', () => {
    const r = fireProjection(base);
    expect(r.realReturn).toBeCloseTo(((1.12 / 1.06) - 1) * 100, 10);
    expect(r.realReturn).toBeLessThan(base.expectedReturn);
  });

  it('reaches the target and reports a retirement age', () => {
    const r = fireProjection(base);
    expect(r.canRetire).toBe(true);
    expect(r.monthsToFire).toBeGreaterThan(0);
    expect(r.fireAge).toBeCloseTo(base.currentAge + r.yearsToFire, 10);
  });

  it('saving more shortens the runway', () => {
    const slow = fireProjection(base).monthsToFire;
    const fast = fireProjection({ ...base, monthlySavings: 100000 }).monthsToFire;
    expect(fast).toBeLessThan(slow);
  });

  it('a lower withdrawal rate demands a bigger corpus', () => {
    expect(fireProjection({ ...base, withdrawalRate: 2 }).fireNumber)
      .toBeGreaterThan(fireProjection({ ...base, withdrawalRate: 4 }).fireNumber);
  });

  it('gives up when inflation outruns returns', () => {
    const r = fireProjection({ ...base, expectedReturn: 4, inflationRate: 9, monthlySavings: 1000 });
    expect(r.realReturn).toBeLessThan(0);
    expect(r.canRetire).toBe(false);
    expect(r.monthsToFire).toBe(600);
  });

  it('reports one milestone per completed year', () => {
    const r = fireProjection(base);
    expect(r.milestones).toHaveLength(Math.floor(r.monthsToFire / 12));
    expect(r.milestones.every((m) => m.pctToFire <= 100)).toBe(true);
  });

  it('pays passive income equal to the withdrawal rate on the corpus', () => {
    const r = fireProjection(base);
    expect(r.monthlyPassiveIncome).toBeCloseTo(r.fireNumber * 0.03 / 12, 6);
    // At the FIRE number, passive income covers today's expenses exactly.
    expect(r.monthlyPassiveIncome).toBeCloseTo(base.monthlyExpenses, 6);
  });
});

describe('stepUpSipProjection', () => {
  it('collapses to a flat SIP when the step-up is zero', () => {
    const stepped = stepUpSipProjection(10000, 12, 15, 0);
    const flat = sipFutureValue(10000, 12, 15);
    expect(stepped.totalInvested).toBe(flat.investedAmount);
    // Flat SIP is an annuity-due; the step-up loop compounds after each
    // deposit, so they agree to within one month of growth.
    expect(stepped.totalValue).toBeGreaterThan(flat.totalValue * 0.99);
    expect(stepped.totalValue).toBeLessThanOrEqual(flat.totalValue);
  });

  it('beats a flat SIP once contributions step up', () => {
    const stepped = stepUpSipProjection(10000, 12, 15, 10);
    expect(stepped.totalValue).toBeGreaterThan(sipFutureValue(10000, 12, 15).totalValue);
  });

  it('raises the contribution by the step-up each year', () => {
    const rows = stepUpSipProjection(10000, 12, 3, 10).yearlyBreakdown;
    expect(rows.map((r) => r.monthlySIP)).toEqual([10000, 11000, 12100]);
  });

  it('reconciles returns against invested and final value', () => {
    const r = stepUpSipProjection(10000, 12, 15, 10);
    expect(r.totalReturns).toBeCloseTo(r.totalValue - r.totalInvested, 6);
  });

  it('accumulates contributions monotonically', () => {
    const rows = stepUpSipProjection(10000, 12, 10, 10).yearlyBreakdown;
    expect(rows).toHaveLength(10);
    for (let i = 1; i < rows.length; i++) {
      expect(rows[i].invested).toBeGreaterThan(rows[i - 1].invested);
      expect(rows[i].value).toBeGreaterThan(rows[i - 1].value);
    }
  });

  it('earns nothing at a 0% return', () => {
    const r = stepUpSipProjection(10000, 0, 3, 0);
    expect(r.totalValue).toBeCloseTo(10000 * 36, 6);
    expect(r.totalReturns).toBeCloseTo(0, 6);
  });
});

describe('compareFixedFloating', () => {
  const base = {
    principal: 1500000,
    tenureMonths: 300,
    fixedRate: 4.25,
    fixedMonths: 36,
    benchmarkNow: 4.45,
    benchmarkAtFixEnd: 4.45,
    marginAfterFix: 1.5,
    floatingMargin: 1.5,
  };

  it('prices the fixed period and the floating loan with the plain EMI formula', () => {
    const r = compareFixedFloating(base);
    expect(r.fixedThenFloating.firstPayment).toBeCloseTo(calculateEMI(1500000, 4.25, 300).emi, 6);
    // A flat benchmark means the floating loan never changes rate.
    const flat = calculateEMI(1500000, 5.95, 300);
    expect(r.floating.firstPayment).toBeCloseTo(flat.emi, 6);
    expect(r.floating.totalInterest).toBeCloseTo(flat.totalInterest, 4);
  });

  it('re-levels the payment at reversion over the months remaining', () => {
    const r = compareFixedFloating(base);
    const balanceAtReversion = r.fixedThenFloating.yearlyBreakdown[2].closingBalance;
    const expected = calculateEMI(balanceAtReversion, 5.95, 264).emi;
    expect(r.fixedThenFloating.paymentAtFixEnd).toBeCloseTo(expected, 6);
    expect(r.paymentJump).toBeCloseTo(expected - r.fixedThenFloating.firstPayment, 6);
  });

  it('clears both loans by the end of the term', () => {
    const r = compareFixedFloating({ ...base, benchmarkAtFixEnd: 6.5 });
    expect(r.fixedThenFloating.yearlyBreakdown[24].closingBalance).toBeCloseTo(0, 4);
    expect(r.floating.yearlyBreakdown[24].closingBalance).toBeCloseTo(0, 4);
  });

  it('reconciles interest against everything paid', () => {
    // Fixed payments for 36 months, then the re-levelled payment for 264.
    const leg = compareFixedFloating(base).fixedThenFloating;
    const paid = leg.firstPayment * 36 + leg.paymentAtFixEnd * 264;
    expect(leg.totalInterest).toBeCloseTo(paid - 1500000, 4);
  });

  it('moves the floating rate in a straight line, resetting quarterly', () => {
    const r = compareFixedFloating({ ...base, benchmarkAtFixEnd: 7.45 });
    const rows = r.floating.yearlyBreakdown;
    // Month 11 was last reset at month 9: 4.45 + 3 * 9/36, plus the 1.5 margin.
    expect(rows[0].rate).toBeCloseTo(6.7, 6);
    expect(rows[1].rate).toBeCloseTo(7.7, 6);
    // Held at 7.45 + 1.5 from the end of the fixed period onward.
    expect(rows[3].rate).toBeCloseTo(8.95, 6);
    expect(r.floating.rateAtFixEnd).toBeCloseTo(8.95, 6);
  });

  it('applies the floor to both floating phases but not to the fixed period', () => {
    const r = compareFixedFloating({ ...base, benchmarkNow: 1, benchmarkAtFixEnd: 1, floorRate: 4.75 });
    expect(r.floating.rateAtFixEnd).toBe(4.75);
    expect(r.fixedThenFloating.rateAtFixEnd).toBe(4.75);
    expect(r.fixedThenFloating.yearlyBreakdown[0].rate).toBe(4.25);
  });

  it('adds the one-off cost to the floating loan only', () => {
    const without = compareFixedFloating(base);
    const withFee = compareFixedFloating({ ...base, switchCost: 10000 });
    expect(withFee.floating.totalCost).toBeCloseTo(without.floating.totalCost + 10000, 6);
    expect(withFee.floating.totalInterest).toBeCloseTo(without.floating.totalInterest, 6);
    expect(withFee.fixedThenFloating.totalCost).toBeCloseTo(without.fixedThenFloating.totalCost, 6);
  });

  it('finds the benchmark level at which both loans cost the same', () => {
    const { breakEvens } = compareFixedFloating({ ...base, fixedRate: 6.5 });
    expect(breakEvens).toHaveLength(1);
    const { benchmark, fixingWinsAbove } = breakEvens[0];
    expect(fixingWinsAbove).toBe(true);
    const atBreakEven = compareFixedFloating({ ...base, fixedRate: 6.5, benchmarkAtFixEnd: benchmark });
    expect(atBreakEven.costDifference).toBeCloseTo(0, 2);
    const above = compareFixedFloating({ ...base, fixedRate: 6.5, benchmarkAtFixEnd: benchmark + 1 });
    const below = compareFixedFloating({ ...base, fixedRate: 6.5, benchmarkAtFixEnd: benchmark - 1 });
    expect(above.costDifference).toBeGreaterThan(0);
    expect(below.costDifference).toBeLessThan(0);
  });

  it('reports no break-even when one loan wins at every benchmark level', () => {
    const r = compareFixedFloating({ ...base, fixedRate: 1, benchmarkNow: 0, floatingMargin: 3 });
    expect(r.breakEvens).toEqual([]);
    expect(r.costDifference).toBeGreaterThan(0);
  });

  it('reports every crossing with the direction measured, across unusual inputs', () => {
    // Seeded so a failure reproduces. Covers the floors and unequal margins that
    // break the assumption that the cost gap simply rises with the benchmark.
    let seed = 12345;
    const rand = (lo: number, hi: number) => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return lo + (seed / 4294967296) * (hi - lo);
    };
    for (let i = 0; i < 150; i++) {
      const years = Math.floor(rand(3, 31));
      const input = {
        principal: 1000000,
        tenureMonths: years * 12,
        fixedRate: rand(1, 16),
        fixedMonths: Math.floor(rand(1, Math.min(10, years - 1) + 1)) * 12,
        benchmarkNow: rand(0, 12),
        benchmarkAtFixEnd: 5,
        marginAfterFix: rand(0, 6),
        floatingMargin: rand(0, 6),
        floorRate: rand(0, 1) < 0.3 ? rand(0, 10) : 0,
        switchCost: rand(0, 1) < 0.3 ? rand(0, 30000) : 0,
      };
      const gapAt = (level: number) =>
        compareFixedFloating({ ...input, benchmarkAtFixEnd: level }).costDifference;
      for (const { benchmark, fixingWinsAbove } of compareFixedFloating(input).breakEvens) {
        expect(Math.abs(gapAt(benchmark))).toBeLessThan(1);
        expect(gapAt(benchmark + 0.01) > gapAt(benchmark - 0.01)).toBe(fixingWinsAbove);
      }
    }
  });

  it('never reverts when the fixed period covers the whole term', () => {
    const r = compareFixedFloating({ ...base, fixedMonths: 300 });
    expect(r.paymentJump).toBeCloseTo(0, 6);
    expect(r.fixedThenFloating.totalInterest).toBeCloseTo(calculateEMI(1500000, 4.25, 300).totalInterest, 4);
  });
});

describe('compareLoanTakeover', () => {
  const base = { balance: 1200000, currentRate: 5.75, remainingMonths: 240, newRate: 4.75, newTenureMonths: 240, exitFee: 10000, newLoanCosts: 20000 };

  it('prices both loans with the plain EMI formula', () => {
    const r = compareLoanTakeover(base);
    expect(r.currentPayment).toBeCloseTo(calculateEMI(1200000, 5.75, 240).emi, 6);
    expect(r.newPayment).toBeCloseTo(calculateEMI(1200000, 4.75, 240).emi, 6);
  });

  it('nets the fees off the interest saved', () => {
    const r = compareLoanTakeover(base);
    const saved = calculateEMI(1200000, 5.75, 240).totalInterest - calculateEMI(1200000, 4.75, 240).totalInterest;
    expect(r.totalFees).toBe(30000);
    expect(r.netSaving).toBeCloseTo(saved - 30000, 4);
  });

  it('breaks even around fees / monthly interest gap, on the same term', () => {
    // A 1% gap on 12 lakh is about 1,000 a month in the early years.
    const m = compareLoanTakeover(base).breakEvenMonth!;
    expect(m).toBeGreaterThan(25);
    expect(m).toBeLessThan(35);
  });

  it('breaks even immediately with no fees and a lower rate', () => {
    expect(compareLoanTakeover({ ...base, exitFee: 0, newLoanCosts: 0 }).breakEvenMonth).toBe(1);
  });

  it('never breaks even at a higher rate', () => {
    const r = compareLoanTakeover({ ...base, newRate: 6.25 });
    expect(r.breakEvenMonth).toBeNull();
    expect(r.netSaving).toBeLessThan(0);
  });

  it('flags that a longer term can cut the payment yet cost more overall', () => {
    const r = compareLoanTakeover({ ...base, newRate: 5.5, newTenureMonths: 300, exitFee: 0, newLoanCosts: 0 });
    expect(r.monthlySaving).toBeGreaterThan(0);
    expect(r.netSaving).toBeLessThan(0);
  });

  it('treats a shorter term at the same rate as no change in net worth by month', () => {
    const r = compareLoanTakeover({ ...base, newRate: 5.75, newTenureMonths: 120, exitFee: 0, newLoanCosts: 0 });
    expect(r.monthlySaving).toBeLessThan(0);
    expect(r.netSaving).toBeGreaterThan(0);
  });
});

describe('comparePrepayment', () => {
  const base = { balance: 4000000, annualRate: 8.5, remainingMonths: 240, lumpSum: 500000, extraMonthly: 0, fee: 0 };

  it('matches the plain loan when nothing is prepaid', () => {
    const r = comparePrepayment({ ...base, lumpSum: 0 });
    const plain = calculateEMI(4000000, 8.5, 240);
    expect(r.baselinePayment).toBeCloseTo(plain.emi, 6);
    expect(r.shorterTerm.months).toBe(240);
    expect(r.shorterTerm.netSaving).toBeCloseTo(0, 2);
    expect(r.lowerPayment.netSaving).toBeCloseTo(0, 2);
  });

  it('prices the lower payment as a new loan on the reduced balance', () => {
    const r = comparePrepayment(base);
    const reduced = calculateEMI(3500000, 8.5, 240);
    expect(r.lowerPayment.payment).toBeCloseTo(reduced.emi, 6);
    expect(r.lowerPayment.months).toBe(240);
    expect(r.lowerPayment.totalInterest).toBeCloseTo(reduced.totalInterest, 2);
  });

  it('saves more by finishing sooner than by lowering the payment', () => {
    const r = comparePrepayment(base);
    expect(r.shorterTerm.months).toBeLessThan(240);
    expect(r.shorterTerm.payment).toBeCloseTo(r.baselinePayment, 6);
    expect(r.shorterTerm.netSaving).toBeGreaterThan(r.lowerPayment.netSaving);
  });

  it('takes the fee off both savings', () => {
    const free = comparePrepayment(base);
    const paid = comparePrepayment({ ...base, fee: 10000 });
    expect(paid.shorterTerm.netSaving).toBeCloseTo(free.shorterTerm.netSaving - 10000, 6);
    expect(paid.lowerPayment.netSaving).toBeCloseTo(free.lowerPayment.netSaving - 10000, 6);
  });

  it('clears the loan today when the lump sum covers it', () => {
    const r = comparePrepayment({ ...base, lumpSum: 9000000 });
    expect(r.shorterTerm.months).toBe(0);
    expect(r.shorterTerm.totalInterest).toBe(0);
    expect(r.lowerPayment.payment).toBe(0);
    expect(r.shorterTerm.netSaving).toBeCloseTo(r.baselineInterest, 6);
  });

  it('shortens the loan further with a monthly top-up', () => {
    const r = comparePrepayment({ ...base, lumpSum: 0, extraMonthly: 5000 });
    expect(r.shorterTerm.months).toBeLessThan(240);
    expect(r.shorterTerm.netSaving).toBeGreaterThan(0);
  });

  it('handles a 0% rate', () => {
    const r = comparePrepayment({ ...base, annualRate: 0 });
    expect(r.shorterTerm.months).toBe(210);
    expect(r.shorterTerm.totalInterest).toBe(0);
  });
});

describe('dubaiPurchaseCosts', () => {
  const base = { price: 1500000, loanPercent: 80, useAgent: true, agentPercent: 2, bankFeePercent: 1, valuationFee: 3000, otherCosts: 0 };

  it('adds up a financed purchase through an agent', () => {
    const r = dubaiPurchaseCosts(base);
    const expected =
      60000 + 580 + 4200 + // DLD, admin, trustee
      31500 + // 2% agent with VAT
      (3000 + 290) + // registration on 12,00,000
      12600 + // 1% bank fee with VAT
      3000; // valuation
    expect(r.loan).toBe(1200000);
    expect(r.downPayment).toBe(300000);
    expect(r.totalCosts).toBeCloseTo(expected, 6);
    expect(r.cashNeeded).toBeCloseTo(300000 + expected, 6);
  });

  it('drops the mortgage costs on a cash purchase', () => {
    const r = dubaiPurchaseCosts({ ...base, loanPercent: 0 });
    expect(r.downPayment).toBe(1500000);
    expect(r.totalCosts).toBeCloseTo(60000 + 580 + 4200 + 31500, 6);
    expect(r.costs.some((c) => c.label.includes('Mortgage'))).toBe(false);
  });

  it('drops the commission without an agent', () => {
    const withAgent = dubaiPurchaseCosts(base).totalCosts;
    expect(dubaiPurchaseCosts({ ...base, useAgent: false }).totalCosts).toBeCloseTo(withAgent - 31500, 6);
  });

  it('charges the lower trustee fee below AED 500,000', () => {
    const line = (price: number) => dubaiPurchaseCosts({ ...base, price }).costs.find((c) => c.label.includes('Trustee'))!.amount;
    expect(line(499999)).toBeCloseTo(2100, 6);
    expect(line(500000)).toBeCloseTo(4200, 6);
  });

  it('reports costs as a share of the price', () => {
    const r = dubaiPurchaseCosts(base);
    expect(r.costsPercentOfPrice).toBeCloseTo((r.totalCosts / 1500000) * 100, 6);
  });
});

describe('maxAffordability', () => {
  const base = {
    monthlyIncome: 30000,
    existingMonthlyDebts: 2000,
    debtRatioPercent: 50,
    annualRate: 5,
    tenureMonths: 300,
    savings: 500000,
    buyingCostPercent: 7,
    ltvTiers: [{ maxPrice: Infinity, ltvPercent: 80 }],
  };

  // Largest price with every limit respected, found the slow and obvious way.
  const bruteForce = (input: typeof base) => {
    const perUnit = calculateEMI(1, input.annualRate, input.tenureMonths).emi;
    const incomeLoan = Math.max(0, (input.monthlyIncome * input.debtRatioPercent) / 100 - input.existingMonthlyDebts) / perUnit;
    let best = 0;
    for (let p = 0; p <= 50000000; p += 1000) {
      const tier = input.ltvTiers.find((t) => p <= t.maxPrice)!;
      const loan = Math.min(incomeLoan, (p * tier.ltvPercent) / 100);
      if (p * (1 + input.buyingCostPercent / 100) - loan <= input.savings) best = p;
    }
    return best;
  };

  it('turns the debt limit into a loan with the EMI formula', () => {
    const r = maxAffordability(base);
    expect(r.maxPayment).toBe(13000);
    expect(calculateEMI(r.incomeLoanLimit, 5, 300).emi).toBeCloseTo(13000, 4);
  });

  it('stops at savings when income would allow more', () => {
    const r = maxAffordability({ ...base, monthlyIncome: 100000 });
    expect(r.limitedBy).toBe('savings');
    expect(r.maxPrice).toBeCloseTo(500000 / (1.07 - 0.8), 4);
    expect(r.downPayment + r.buyingCosts).toBeCloseTo(500000, 4);
    expect(r.loan).toBeCloseTo(r.maxPrice * 0.8, 4);
  });

  it('stops at income when savings would allow more', () => {
    const r = maxAffordability({ ...base, monthlyIncome: 15000, savings: 5000000 });
    expect(r.limitedBy).toBe('income');
    expect(r.payment).toBeCloseTo(5500, 4);
    expect(r.loan).toBeCloseTo(r.incomeLoanLimit, 4);
  });

  it('returns only what savings buy when debts use up the limit', () => {
    const r = maxAffordability({ ...base, existingMonthlyDebts: 20000 });
    expect(r.maxPayment).toBe(0);
    expect(r.loan).toBe(0);
    expect(r.maxPrice).toBeCloseTo(500000 / 1.07, 4);
  });

  it('applies the RBI tier for the resulting price', () => {
    const r = maxAffordability({ ...base, monthlyIncome: 300000, annualRate: 8.5, tenureMonths: 240, savings: 2500000, buyingCostPercent: 6, ltvTiers: INDIA_LTV_TIERS });
    expect(r.ltvPercent).toBe(75);
    expect(r.maxPrice).toBeGreaterThan(7500000);
  });

  it('stays inside a lower tier when a higher one would need more cash', () => {
    // At exactly 30 lakh, 90% LTV needs far less cash than 80% just above it.
    const r = maxAffordability({ ...base, monthlyIncome: 300000, annualRate: 8.5, tenureMonths: 240, savings: 480000, buyingCostPercent: 6, ltvTiers: INDIA_LTV_TIERS });
    expect(r.maxPrice).toBeCloseTo(3000000, 2);
    expect(r.ltvPercent).toBe(90);
  });

  it('agrees with a brute-force search across tiers', () => {
    for (const income of [40000, 90000, 200000, 500000]) {
      for (const savings of [300000, 700000, 1500000, 4000000]) {
        const input = { ...base, monthlyIncome: income, annualRate: 8.5, tenureMonths: 240, savings, buyingCostPercent: 6, ltvTiers: INDIA_LTV_TIERS };
        expect(Math.abs(maxAffordability(input).maxPrice - bruteForce(input))).toBeLessThanOrEqual(1000);
      }
    }
  });
});

describe('compareRentVsBuy', () => {
  const base = {
    price: 1500000, downPercent: 20, annualRate: 5, tenureMonths: 300,
    buyingCostPercent: 7, sellingCostPercent: 2, ownershipCostPercent: 1,
    appreciationPercent: 3, monthlyRent: 7000, rentGrowthPercent: 3,
    investmentReturnPercent: 6, years: 10,
  };

  it('gives the renter the buyer\'s upfront cash to invest', () => {
    const r = compareRentVsBuy(base);
    expect(r.upfrontCash).toBeCloseTo(300000 + 105000, 6);
    // With no growth, equal housing costs and a 0% return, the pot stays put.
    const flat = compareRentVsBuy({ ...base, investmentReturnPercent: 0, ownershipCostPercent: 0, rentGrowthPercent: 0, monthlyRent: r.monthlyLoanPayment });
    expect(flat.renterNetWorth).toBeCloseTo(405000, 4);
  });

  it('values the home at a sale, net of costs and debt', () => {
    const cash = compareRentVsBuy({ ...base, downPercent: 100, appreciationPercent: 0, sellingCostPercent: 0, ownershipCostPercent: 0, monthlyRent: 0, rentGrowthPercent: 0, investmentReturnPercent: 0 });
    expect(cash.monthlyLoanPayment).toBe(0);
    expect(cash.buyerNetWorth).toBeCloseTo(1500000, 4);
    // The renter keeps the price and the buying costs: buying loses just the costs.
    expect(cash.advantage).toBeCloseTo(-105000, 4);
  });

  it('applies appreciation at the stated annual rate', () => {
    const r = compareRentVsBuy({ ...base, downPercent: 100, sellingCostPercent: 0, ownershipCostPercent: 0, monthlyRent: 0, rentGrowthPercent: 0, investmentReturnPercent: 0, years: 5 });
    expect(r.buyerNetWorth).toBeCloseTo(1500000 * Math.pow(1.03, 5), 2);
  });

  it('has the buyer invest the saving when rent costs more than owning', () => {
    const r = compareRentVsBuy({ ...base, downPercent: 100, ownershipCostPercent: 0, sellingCostPercent: 0, appreciationPercent: 0, rentGrowthPercent: 0, investmentReturnPercent: 0, monthlyRent: 1000, years: 2 });
    expect(r.buyerNetWorth).toBeCloseTo(1500000 + 24000, 4);
  });

  it('stops the loan payment once the tenure ends', () => {
    const r = compareRentVsBuy({ ...base, tenureMonths: 60, ownershipCostPercent: 0, monthlyRent: 0, rentGrowthPercent: 0, investmentReturnPercent: 0, years: 10 });
    expect(r.renterNetWorth).toBeCloseTo(405000 + r.monthlyLoanPayment * 60, 2);
  });

  it('favours buying as rents rise, all else equal', () => {
    const low = compareRentVsBuy({ ...base, monthlyRent: 4000 });
    const high = compareRentVsBuy({ ...base, monthlyRent: 12000 });
    expect(high.advantage).toBeGreaterThan(low.advantage);
  });

  it('finds the year buying moves ahead for good', () => {
    const r = compareRentVsBuy({ ...base, monthlyRent: 12000, years: 25 });
    expect(r.breakEvenYear).not.toBeNull();
    const i = r.breakEvenYear! - 1;
    expect(r.yearly[i].buyerNetWorth).toBeGreaterThan(r.yearly[i].renterNetWorth);
    if (i > 0) expect(r.yearly[i - 1].buyerNetWorth).toBeLessThanOrEqual(r.yearly[i - 1].renterNetWorth);
  });

  it('reports no break-even when renting stays ahead', () => {
    const r = compareRentVsBuy({ ...base, monthlyRent: 2000, appreciationPercent: 0, investmentReturnPercent: 10 });
    expect(r.advantage).toBeLessThan(0);
    expect(r.breakEvenYear).toBeNull();
  });
});

describe('salaryBreakdown', () => {
  const base = { annualCtc: 1200000, basicPercent: 50, annualVariable: 0, pfBasis: 'full' as const, includeGratuityInCtc: false, monthlyProfessionalTax: 200, regime: 'new' as const, oldRegimeDeductions: 0 };

  it('takes employer PF out of the CTC at 12% of full basic', () => {
    const r = salaryBreakdown(base);
    expect(r.annualBasic).toBe(600000);
    expect(r.employerPf).toBe(72000);
    expect(r.grossSalary).toBe(1128000);
  });

  it('caps PF at the 15,000 wage ceiling when chosen', () => {
    const r = salaryBreakdown({ ...base, pfBasis: 'capped' });
    expect(r.employerPf).toBe(21600);
    expect(r.employeePf).toBe(21600);
  });

  it('does not cap PF below the ceiling for low basic pay', () => {
    const r = salaryBreakdown({ ...base, annualCtc: 240000, pfBasis: 'capped' });
    expect(r.employerPf).toBe(120000 * 0.12);
  });

  it('reconciles take-home against every deduction', () => {
    const r = salaryBreakdown(base);
    expect(r.incomeTax).toBe(0); // 11,28,000 is inside the 12.75 lakh zero-tax range
    expect(r.annualTakeHome).toBeCloseTo(1128000 - 72000 - 2400, 6);
    expect(r.monthlyInHand).toBeCloseTo(r.annualTakeHome / 12, 6);
  });

  it('adds gratuity at 15/26 of a month of basic when included', () => {
    const r = salaryBreakdown({ ...base, includeGratuityInCtc: true });
    expect(r.gratuityProvision).toBeCloseTo((600000 / 12) * (15 / 26), 6);
    expect(r.grossSalary).toBeCloseTo(1128000 - r.gratuityProvision, 6);
  });

  it('holds variable pay and its tax out of the monthly figure', () => {
    const r = salaryBreakdown({ ...base, annualCtc: 2000000, annualVariable: 300000 });
    const noBonusPay = r.annualTakeHome - r.monthlyInHand * 12;
    expect(noBonusPay).toBeGreaterThan(0);
    expect(noBonusPay).toBeLessThan(300000); // the bonus, after its share of tax
  });

  it('uses old regime slabs with deductions and professional tax', () => {
    const r = salaryBreakdown({ ...base, annualCtc: 2000000, regime: 'old', oldRegimeDeductions: 150000 });
    const gross = 2000000 - 120000;
    expect(r.grossSalary).toBe(gross);
    expect(r.incomeTax).toBeCloseTo(indiaIncomeTaxOldRegime(gross, 152400).totalTaxWithCess, 6);
  });
});
