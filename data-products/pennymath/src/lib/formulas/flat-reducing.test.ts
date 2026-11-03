import { describe, expect, it } from 'vitest';
import { compareFlatReducing, equivalentReducingRate, flatRateLoan } from './flat-reducing';
import { monthlyPayment } from './loan-emi';

describe('flat vs reducing rate', () => {
  it('charges flat interest on the full loan for the whole tenure', () => {
    // ₹1,00,000 at 10% flat for 12 years: ₹1,20,000 interest, ₹2,20,000 over 144 months.
    const flat = flatRateLoan(100000, 10, 144);
    expect(flat.totalInterest).toBeCloseTo(120000, 6);
    expect(flat.totalAmount).toBeCloseTo(220000, 6);
    expect(flat.emi).toBeCloseTo(1527.78, 2);
  });

  it('charges reducing-balance interest like a normal EMI', () => {
    const r = compareFlatReducing(100000, 10, 144);
    expect(r.reducing.emi).toBeCloseTo(monthlyPayment(100000, 10, 144), 9);
    expect(Math.round(r.reducing.emi)).toBe(1195);
    expect(r.reducing.totalInterest).toBeGreaterThan(72000);
    expect(r.reducing.totalInterest).toBeLessThan(72200);
  });

  it('finds the reducing rate whose instalment equals the flat one', () => {
    for (const [rate, months] of [[10, 144], [10, 12], [3, 60], [25, 36]]) {
      const eq = equivalentReducingRate(500000, rate, months);
      expect(monthlyPayment(500000, eq, months)).toBeCloseTo(flatRateLoan(500000, rate, months).emi, 6);
      expect(eq).toBeGreaterThan(rate);
    }
  });

  it('matches the textbook figure: 10% flat for one year is about 18% reducing', () => {
    const eq = equivalentReducingRate(100000, 10, 12);
    expect(eq).toBeGreaterThan(17.9);
    expect(eq).toBeLessThan(18.0);
  });

  it('does not depend on the loan amount, and is zero at zero', () => {
    expect(equivalentReducingRate(1000, 8, 60)).toBeCloseTo(equivalentReducingRate(10_000_000, 8, 60), 6);
    expect(equivalentReducingRate(100000, 0, 60)).toBe(0);
  });
});
