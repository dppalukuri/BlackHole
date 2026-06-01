import { useState } from 'preact/hooks';
import { indiaIncomeTaxNewRegime } from '../../../lib/formulas/tax-slab';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';

export default function IncomeTaxCalculator() {
  const [income, setIncome] = useState(1200000);
  const result = indiaIncomeTaxNewRegime(income);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="annual-income"
          label="Annual Income (Gross)"
          value={income}
          min={0}
          max={10000000}
          step={50000}
          prefix="₹"
          onChange={setIncome}
        />
      </div>

      <div class="calc-results" style="grid-template-columns: 1fr;">
        <div class="result-card">
          <div class="result-item">
            <span class="result-label">Taxable Income (after ₹75K std deduction)</span>
            <span class="result-value">{formatCurrency(result.taxableIncome, 'INR')}</span>
          </div>
          <div class="result-item">
            <span class="result-label">Income Tax</span>
            <span class="result-value">{formatCurrency(result.totalTax, 'INR')}</span>
          </div>
          <div class="result-item">
            <span class="result-label">Health & Education Cess (4%)</span>
            <span class="result-value">{formatCurrency(result.cess, 'INR')}</span>
          </div>
          <div class="result-item result-highlight">
            <span class="result-label">Total Tax Payable</span>
            <span class="result-value">{formatCurrency(result.totalTaxWithCess, 'INR')}</span>
          </div>
          <div class="result-item">
            <span class="result-label">Effective Tax Rate</span>
            <span class="result-value">{result.effectiveRate.toFixed(1)}%</span>
          </div>
        </div>

        {result.slabBreakdown.length > 0 && (
          <div class="gratuity-breakdown" style="margin-top: 1.5rem;">
            <h3>Slab-wise Breakdown (New Regime FY 2025-26)</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 0.75rem; font-size: 0.9rem;">
              <thead>
                <tr style="border-bottom: 2px solid #e2e8f0; text-align: left;">
                  <th style="padding: 0.5rem;">Income Slab</th>
                  <th style="padding: 0.5rem;">Rate</th>
                  <th style="padding: 0.5rem; text-align: right;">Tax</th>
                </tr>
              </thead>
              <tbody>
                {result.slabBreakdown.map((s) => (
                  <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 0.5rem;">{s.slab}</td>
                    <td style="padding: 0.5rem;">{s.rate}%</td>
                    <td style="padding: 0.5rem; text-align: right;">{formatCurrency(s.tax, 'INR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {result.taxableIncome <= 1200000 && result.taxableIncome > 0 && (
              <p style="margin-top: 0.75rem; color: #16a34a; font-weight: 600;">
                Section 87A rebate applied — No tax payable for income up to ₹12,00,000 under new regime.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
