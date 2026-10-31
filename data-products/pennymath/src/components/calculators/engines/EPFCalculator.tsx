import { useState } from 'preact/hooks';
import { epfProjection, type EpfInput } from '../../../lib/formulas/epf';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';
import ChoiceButtons from '../ui/ChoiceButtons';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function EPFCalculator() {
  const [age, setAge] = useState(30);
  const [retirementAge, setRetirementAge] = useState(58);
  const [basic, setBasic] = useState(50000);
  const [raise, setRaise] = useState(6);
  const [pfBasis, setPfBasis] = useState<EpfInput['pfBasis']>('full');
  const [existing, setExisting] = useState(0);
  const [rate, setRate] = useState(8.25);

  const r = epfProjection({
    currentAge: age,
    retirementAge: Math.max(retirementAge, age + 1),
    monthlyBasic: basic,
    annualRaisePercent: raise,
    pfBasis,
    existingBalance: existing,
    interestRatePercent: rate,
  });

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="epf-age" label="Your Age" value={age} min={18} max={59} step={1} suffix=" Yr" onChange={setAge} />
        <SliderInput id="epf-retire" label="Retirement Age" value={retirementAge} min={40} max={60} step={1} suffix=" Yr" onChange={setRetirementAge} />
        <SliderInput id="epf-basic" label="Monthly Basic Pay plus DA" value={basic} min={5000} max={500000} step={1000} prefix="₹" scalable locale="en-IN" onChange={setBasic} />
        <SliderInput id="epf-raise" label="Yearly Salary Increase" value={raise} min={0} max={20} step={0.5} suffix="%" onChange={setRaise} />
        <ChoiceButtons label="PF Is Calculated On" value={pfBasis} options={[{ value: 'full', label: 'Full basic pay' }, { value: 'capped', label: '₹15,000 wage ceiling' }]} onChange={setPfBasis} />
        <SliderInput id="epf-existing" label="Current EPF Balance" value={existing} min={0} max={10000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setExisting} />
        <SliderInput id="epf-rate" label="EPF Interest Rate (p.a.)" value={rate} min={5} max={12} step={0.05} suffix="%" onChange={setRate} />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Your contributions', value: r.totalEmployee },
            { label: 'Employer contributions', value: r.totalEmployer },
            { label: 'Interest earned', value: r.totalInterest },
            { label: 'EPF balance at retirement', value: r.finalBalance, highlight: true },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Your Contributions', value: r.totalEmployee, color: '#6366f1' },
            { label: 'Employer', value: r.totalEmployer, color: '#a5b4fc' },
            { label: 'Interest', value: r.totalInterest, color: '#22c55e' },
          ]}
        />
      </div>

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>Your first month's contributions</h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          You pay <strong>{fmt(r.firstMonthEmployee)}</strong>. Your employer matches it, sending{' '}
          <strong>{fmt(r.firstMonthEmployerEpf)}</strong> to your EPF and <strong>{fmt(r.firstMonthEps)}</strong> to the
          Employees' Pension Scheme, which pays a pension and is not part of this balance.
        </p>
      </div>

      <details style={{ marginTop: '1.25rem' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>View Year-by-Year Breakdown</summary>
        <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ textAlign: 'right', color: 'var(--color-text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '0.5rem 0.6rem', fontWeight: 600 }}>Age</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>You</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Employer</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Interest</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Balance</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: 'var(--font-mono)' }}>
              {r.yearlyBreakdown.map((row) => (
                <tr style={{ borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
                  <td style={{ textAlign: 'left', padding: '0.45rem 0.6rem', fontWeight: 600 }}>{row.age}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.employee)}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.employer)}</td>
                  <td style={{ padding: '0.45rem 0.6rem', color: '#16a34a' }}>{fmt(row.interest)}</td>
                  <td style={{ padding: '0.45rem 0.6rem', fontWeight: 600 }}>{fmt(row.closingBalance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
