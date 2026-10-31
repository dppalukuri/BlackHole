import { useState } from 'preact/hooks';
import { npsProjection } from '../../../lib/formulas/nps';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function NPSCalculator() {
  const [age, setAge] = useState(30);
  const [retirementAge, setRetirementAge] = useState(60);
  const [monthly, setMonthly] = useState(10000);
  const [stepUp, setStepUp] = useState(5);
  const [ret, setRet] = useState(10);
  const [existing, setExisting] = useState(0);
  const [annuity, setAnnuity] = useState(20);
  const [annuityRate, setAnnuityRate] = useState(6);

  const r = npsProjection({
    currentAge: age,
    retirementAge: Math.max(retirementAge, age + 1),
    monthlyContribution: monthly,
    annualStepUpPercent: stepUp,
    expectedReturnPercent: ret,
    existingCorpus: existing,
    annuityPercent: annuity,
    annuityRatePercent: annuityRate,
  });

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="nps-age" label="Your Age" value={age} min={18} max={69} step={1} suffix=" Yr" onChange={setAge} />
        <SliderInput id="nps-retire" label="Age When You Exit NPS" value={retirementAge} min={40} max={85} step={1} suffix=" Yr" onChange={setRetirementAge} />
        <SliderInput id="nps-monthly" label="Monthly Contribution" value={monthly} min={500} max={200000} step={500} prefix="₹" scalable locale="en-IN" onChange={setMonthly} />
        <SliderInput id="nps-stepup" label="Yearly Increase in Contribution" value={stepUp} min={0} max={20} step={0.5} suffix="%" onChange={setStepUp} />
        <SliderInput id="nps-return" label="Expected Return (p.a.)" value={ret} min={1} max={16} step={0.25} suffix="%" onChange={setRet} />
        <SliderInput id="nps-existing" label="Existing NPS Balance" value={existing} min={0} max={10000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setExisting} />
        <SliderInput id="nps-annuity" label="Share Used to Buy an Annuity" value={annuity} min={0} max={100} step={1} suffix="%" onChange={setAnnuity} />
        <SliderInput id="nps-annuity-rate" label="Annuity Rate (p.a.)" value={annuityRate} min={1} max={10} step={0.1} suffix="%" onChange={setAnnuityRate} />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Total you invest', value: r.totalInvested },
            { label: 'Corpus at exit', value: r.corpus },
            { label: 'Lump sum', value: r.lumpSum },
            { label: 'Estimated monthly pension', value: r.monthlyPension, highlight: true },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Lump Sum', value: r.lumpSum, color: '#6366f1' },
            { label: 'Annuity Purchase', value: r.annuityPurchase, color: '#22c55e' },
          ]}
        />
      </div>

      <details style={{ marginTop: '1.25rem' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>View Year-by-Year Breakdown</summary>
        <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ textAlign: 'right', color: 'var(--color-text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '0.5rem 0.6rem', fontWeight: 600 }}>Age</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Total invested</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Corpus</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: 'var(--font-mono)' }}>
              {r.yearlyBreakdown.map((row) => (
                <tr style={{ borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
                  <td style={{ textAlign: 'left', padding: '0.45rem 0.6rem', fontWeight: 600 }}>{row.age}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.invested)}</td>
                  <td style={{ padding: '0.45rem 0.6rem', fontWeight: 600 }}>{fmt(row.corpus)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
