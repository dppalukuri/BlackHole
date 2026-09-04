import { describe, it, expect } from 'vitest';
import { sipFutureValue, lumpSumFutureValue, ppfFutureValue } from './compound-growth';
import { calculateEMI } from './loan-emi';
import { uaeGratuity, indiaGratuity, calculateVAT } from './flat-rate';
import { indiaIncomeTaxNewRegime } from './tax-slab';
import { swpProjection } from './swp';
import { fireProjection } from './fire';
import { stepUpSipProjection } from './step-up-sip';

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
