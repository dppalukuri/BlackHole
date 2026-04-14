export interface TaxResult {
  taxableIncome: number;
  totalTax: number;
  cess: number;
  totalTaxWithCess: number;
  effectiveRate: number;
  slabBreakdown: Array<{
    slab: string;
    rate: number;
    taxableAmount: number;
    tax: number;
  }>;
}

/** India Income Tax — New Regime FY 2025-26 (AY 2026-27) */
export function indiaIncomeTaxNewRegime(annualIncome: number): TaxResult {
  // Standard deduction of 75,000 under new regime
  const standardDeduction = 75000;
  const taxableIncome = Math.max(0, annualIncome - standardDeduction);

  const slabs = [
    { min: 0, max: 400000, rate: 0, label: 'Up to ₹4,00,000' },
    { min: 400000, max: 800000, rate: 5, label: '₹4,00,001 - ₹8,00,000' },
    { min: 800000, max: 1200000, rate: 10, label: '₹8,00,001 - ₹12,00,000' },
    { min: 1200000, max: 1600000, rate: 15, label: '₹12,00,001 - ₹16,00,000' },
    { min: 1600000, max: 2000000, rate: 20, label: '₹16,00,001 - ₹20,00,000' },
    { min: 2000000, max: 2400000, rate: 25, label: '₹20,00,001 - ₹24,00,000' },
    { min: 2400000, max: Infinity, rate: 30, label: 'Above ₹24,00,000' },
  ];

  let totalTax = 0;
  const slabBreakdown: TaxResult['slabBreakdown'] = [];

  for (const slab of slabs) {
    if (taxableIncome <= slab.min) break;
    const taxableAmount = Math.min(taxableIncome, slab.max) - slab.min;
    const tax = (taxableAmount * slab.rate) / 100;
    totalTax += tax;
    slabBreakdown.push({
      slab: slab.label,
      rate: slab.rate,
      taxableAmount,
      tax,
    });
  }

  // Section 87A rebate: no tax if taxable income <= 12,00,000 (new regime)
  if (taxableIncome <= 1200000) {
    totalTax = 0;
  }

  const cess = totalTax * 0.04; // 4% Health & Education Cess
  const totalTaxWithCess = totalTax + cess;
  const effectiveRate = annualIncome > 0 ? (totalTaxWithCess / annualIncome) * 100 : 0;

  return { taxableIncome, totalTax, cess, totalTaxWithCess, effectiveRate, slabBreakdown };
}
