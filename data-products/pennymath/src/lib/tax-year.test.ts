import { describe, it, expect } from 'vitest';
import {
  TAX_DATA_FY,
  TAX_DATA_FY_START_YEAR,
  indianFinancialYear,
  isTaxDataStale,
  taxDataYearsBehind,
} from './tax-year';

describe('indianFinancialYear', () => {
  it('starts a new FY on 1 April', () => {
    expect(indianFinancialYear(new Date('2026-03-31')).fy).toBe('FY 2025-26');
    expect(indianFinancialYear(new Date('2026-04-01')).fy).toBe('FY 2026-27');
  });

  it('counts Jan-Mar as the FY that began the previous calendar year', () => {
    expect(indianFinancialYear(new Date('2026-01-15')).startYear).toBe(2025);
  });

  it('derives the assessment year one year ahead', () => {
    expect(indianFinancialYear(new Date('2026-09-05')).ay).toBe('AY 2027-28');
  });

  it('pads the two-digit tail across a century boundary', () => {
    expect(indianFinancialYear(new Date('2099-06-01')).fy).toBe('FY 2099-00');
  });
});

describe('tax data staleness', () => {
  it('is current inside the financial year it encodes', () => {
    const d = new Date(`${TAX_DATA_FY_START_YEAR}-06-01`);
    expect(isTaxDataStale(d)).toBe(false);
    expect(taxDataYearsBehind(d)).toBe(0);
  });

  it('is still current on the last day of that FY', () => {
    expect(isTaxDataStale(new Date(`${TAX_DATA_FY_START_YEAR + 1}-03-31`))).toBe(false);
  });

  it('goes stale the day the next FY begins', () => {
    const d = new Date(`${TAX_DATA_FY_START_YEAR + 1}-04-01`);
    expect(isTaxDataStale(d)).toBe(true);
    expect(taxDataYearsBehind(d)).toBe(1);
  });

  it('reports how many years behind it has fallen', () => {
    expect(taxDataYearsBehind(new Date(`${TAX_DATA_FY_START_YEAR + 3}-05-01`))).toBe(3);
  });

  it('declares a label consistent with its start year', () => {
    expect(indianFinancialYear(new Date(`${TAX_DATA_FY_START_YEAR}-06-01`)).fy).toBe(TAX_DATA_FY);
  });
});
