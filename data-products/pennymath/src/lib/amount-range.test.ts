import { describe, expect, it } from 'vitest';
import { amountCeiling, shortAmount, windowFor, windowStep } from './amount-range';

describe('amount ranges', () => {
  it('caps rupees at 100 crore and other currencies at 100 million', () => {
    expect(amountCeiling('en-IN')).toBe(1_000_000_000);
    expect(amountCeiling('en-AE')).toBe(100_000_000);
    expect(amountCeiling('en-US')).toBe(100_000_000);
  });

  it('starts the slider so the value sits no more than half way', () => {
    expect(windowFor(3_000_000, 0, 1e9)).toBe(10_000_000); // ₹30 L -> up to ₹1 Cr
    expect(windowFor(1_500_000, 0, 1e8)).toBe(5_000_000); // AED 1.5M -> up to 5M
    expect(windowFor(10_000, 0, 1e9)).toBe(20_000);
    expect(windowFor(5_000_000, 0, 1e9)).toBe(10_000_000); // exactly half way is fine
  });

  it('uses the fallback for an empty value, and never goes below 10,000 or above the cap', () => {
    expect(windowFor(0, 100_000, 1e9)).toBe(100_000);
    expect(windowFor(0, 0, 1e9)).toBe(10_000);
    expect(windowFor(900_000_000, 0, 1e9)).toBe(1_000_000_000);
  });

  it('steps about a hundredth of the range', () => {
    expect(windowStep(10_000_000)).toBe(100_000);
    expect(windowStep(5_000_000)).toBe(10_000);
    expect(windowStep(10_000)).toBe(100);
  });

  it('labels the range top briefly', () => {
    expect(shortAmount(10_000_000, 'en-IN', '₹')).toBe('₹1 Cr');
    expect(shortAmount(5_000_000, 'en-IN', '₹')).toBe('₹50 L');
    expect(shortAmount(20_000, 'en-IN', '₹')).toBe('₹20K');
    expect(shortAmount(10_000_000, 'en-AE', 'AED ')).toBe('AED 10M');
  });
});
