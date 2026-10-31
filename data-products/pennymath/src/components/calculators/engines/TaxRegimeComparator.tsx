import { useState } from 'preact/hooks';
import { indiaIncomeTaxNewRegime, indiaIncomeTaxOldRegime } from '../../../lib/formulas/tax-slab';
import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

interface Deductions {
  section80C: number;
  section80D: number;
  hra: number;
  homeLoanInterest: number;
  nps80CCD: number;
  other: number;
}

const FIELDS: Array<{ key: keyof Deductions; label: string; max: number }> = [
  { key: 'section80C', label: 'Section 80C (PPF, ELSS, LIC)', max: 150000 },
  { key: 'section80D', label: 'Section 80D (Health Insurance)', max: 100000 },
  { key: 'hra', label: 'HRA Exemption', max: 500000 },
  { key: 'homeLoanInterest', label: 'Home Loan Interest (Sec 24)', max: 200000 },
  { key: 'nps80CCD', label: 'NPS 80CCD(1B)', max: 50000 },
  { key: 'other', label: 'Other Deductions', max: 500000 },
];

const fmt = (n: number) => formatCurrency(n, 'INR');
const CHART_POINTS = 40;

export default function TaxRegimeComparator() {
  const [income, setIncome] = useState(1500000);
  const [deductions, setDeductions] = useState<Deductions>({
    section80C: 150000,
    section80D: 25000,
    hra: 0,
    homeLoanInterest: 0,
    nps80CCD: 50000,
    other: 0,
  });

  const claimed = Object.values(deductions).reduce((sum, v) => sum + v, 0);
  const oldResult = indiaIncomeTaxOldRegime(income, claimed);
  const newResult = indiaIncomeTaxNewRegime(income);
  const saving = oldResult.totalTaxWithCess - newResult.totalTaxWithCess;
  const better = saving > 0 ? 'New regime' : saving < 0 ? 'Old regime' : null;

  // A range around this income shows where the cheaper regime changes.
  const top = Math.max(income * 2, 2000000);
  const incomes = Array.from({ length: CHART_POINTS + 1 }, (_, i) => (top * i) / CHART_POINTS);

  const columns = [
    { name: 'Old regime', deductionLabel: 'Deductions, with ₹50,000 standard', deduction: claimed + 50000, r: oldResult, isBest: better === 'Old regime' },
    { name: 'New regime', deductionLabel: 'Standard deduction', deduction: 75000, r: newResult, isBest: better === 'New regime' },
  ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <div class="span-all">
          <SliderInput id="gross-income" label="Gross Annual Income" value={income} min={0} max={50000000} step={50000} prefix="₹" scalable locale="en-IN" onChange={setIncome} />
        </div>
        <h3>Your deductions under the old regime</h3>
        {FIELDS.map((f) => (
          <SliderInput
            id={`deduction-${f.key}`}
            label={f.label}
            value={deductions[f.key]}
            min={0}
            max={f.max}
            step={5000}
            prefix="₹"
            locale="en-IN"
            onChange={(v) => setDeductions((prev) => ({ ...prev, [f.key]: v }))}
          />
        ))}
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: better ? `${better} saves you` : 'Tax is the same under both', value: Math.abs(saving), highlight: true },
            { label: 'Tax under the old regime', value: oldResult.totalTaxWithCess, seriesKey: 1 },
            { label: 'Tax under the new regime', value: newResult.totalTaxWithCess, seriesKey: 2 },
          ]}
        />
        {better && <Verdict title={`Choose the ${better.toLowerCase()}`} tone="good">Based on the deductions you entered. Slabs change each year, so check again before filing.</Verdict>}
      </div>

      <div class="calc-below">
        <LineChart
          title="Tax at different incomes"
          caption="With the deductions you entered"
          x={incomes}
          series={[
            { name: 'Old regime', values: incomes.map((i) => indiaIncomeTaxOldRegime(i, claimed).totalTaxWithCess) },
            { name: 'New regime', values: incomes.map((i) => indiaIncomeTaxNewRegime(i).totalTaxWithCess) },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, 'INR')}
          xTick={(i) => formatCompactCurrency(i, 'INR')}
          xTitle={(i) => `Income of ${fmt(Math.round(i))}`}
          marker={{ x: income, label: 'Your income' }}
          showTable={false}
        />
        <div class="offer-grid">
          {columns.map((c) => (
            <div class={`offer ${c.isBest ? 'is-best' : ''}`}>
              <h3>{c.name} {c.isBest && <span class="tag">Lower tax</span>}</h3>
              <div class="offer-line"><span>{c.deductionLabel}</span><b>{fmt(c.deduction)}</b></div>
              <div class="offer-line"><span>Taxable income</span><b>{fmt(c.r.taxableIncome)}</b></div>
              <div class="offer-line"><span>Income tax</span><b>{fmt(c.r.totalTax)}</b></div>
              <div class="offer-line"><span>Cess at 4%</span><b>{fmt(c.r.cess)}</b></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
