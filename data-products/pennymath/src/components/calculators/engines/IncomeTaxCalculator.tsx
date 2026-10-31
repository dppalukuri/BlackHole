import { useState } from 'preact/hooks';
import { indiaIncomeTaxNewRegime } from '../../../lib/formulas/tax-slab';
import { TAX_DATA_FY } from '../../../lib/tax-year';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import Verdict from '../ui/Verdict';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function IncomeTaxCalculator() {
  const [income, setIncome] = useState(1200000);
  const result = indiaIncomeTaxNewRegime(income);
  const rebateApplies = result.taxableIncome > 0 && result.taxableIncome <= 1200000;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="annual-income" label="Annual Income (Gross)" value={income} min={0} max={10000000} step={50000} prefix="₹" scalable locale="en-IN" onChange={setIncome} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Total tax payable', value: result.totalTaxWithCess, highlight: true },
            { label: 'Taxable income', note: 'After the ₹75,000 standard deduction', value: result.taxableIncome },
            { label: 'Income tax', value: result.totalTax },
            { label: 'Health and education cess at 4%', value: result.cess },
            { label: 'Effective tax rate', value: `${result.effectiveRate.toFixed(1)}%` },
          ]}
        />
        {rebateApplies && (
          <Verdict title="No tax to pay after the Section 87A rebate" tone="good">
            The new regime rebate covers taxable income up to ₹12,00,000.
          </Verdict>
        )}
      </div>

      {result.slabBreakdown.length > 0 && (
        <div class="calc-below">
          <div class="panel-card">
            <h3>Tax by slab, new regime {TAX_DATA_FY}</h3>
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr><th scope="col">Income slab</th><th scope="col">Rate</th><th scope="col">Tax</th></tr>
                </thead>
                <tbody>
                  {result.slabBreakdown.map((s) => (
                    <tr>
                      <td>{s.slab}</td>
                      <td>{s.rate}%</td>
                      <td>{fmt(s.tax)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
