import { useState } from 'preact/hooks';
import { hraExemption, type HraCityGroup, type HraYear } from '../../../lib/formulas/hra';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function HRACalculator() {
  const [salary, setSalary] = useState(60000);
  const [hra, setHra] = useState(24000);
  const [rent, setRent] = useState(25000);
  const [city, setCity] = useState<HraCityGroup>('new-metro');
  const [year, setYear] = useState<HraYear>('fy-2026-27');

  const r = hraExemption({ annualSalary: salary * 12, annualHraReceived: hra * 12, annualRentPaid: rent * 12, city, year });

  const limits = [
    { key: 'actual-hra', label: 'HRA you received', value: r.actualHra },
    { key: 'rent', label: 'Rent paid minus 10% of salary', value: r.rentMinusTenPercent },
    { key: 'salary', label: `${r.salaryPercent}% of salary`, value: r.percentOfSalary },
  ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="hra-salary" label="Monthly Basic Pay plus DA" value={salary} min={5000} max={500000} step={1000} prefix="₹" scalable locale="en-IN" onChange={setSalary} />
        <SliderInput id="hra-received" label="Monthly HRA Received" value={hra} min={0} max={300000} step={500} prefix="₹" scalable locale="en-IN" onChange={setHra} />
        <SliderInput id="hra-rent" label="Monthly Rent Paid" value={rent} min={0} max={300000} step={500} prefix="₹" scalable locale="en-IN" onChange={setRent} />
        <ChoiceButtons
          label="Where Do You Live?"
          value={city}
          options={[
            { value: 'original-metro', label: 'Delhi, Mumbai, Kolkata, Chennai' },
            { value: 'new-metro', label: 'Bengaluru, Hyderabad, Pune, Ahmedabad' },
            { value: 'other', label: 'Any other city' },
          ]}
          onChange={setCity}
        />
        <ChoiceButtons
          label="Financial Year"
          value={year}
          options={[{ value: 'fy-2026-27', label: 'FY 2026-27' }, { value: 'fy-2025-26', label: 'FY 2025-26' }]}
          onChange={setYear}
        />
      </div>

      <ResultCard
        currencyCode="INR"
        results={[
          { label: 'HRA received in the year', value: r.actualHra },
          { label: 'Taxable HRA', value: r.taxable },
          { label: 'Exempt HRA for the year', value: r.exempt, highlight: true },
        ]}
      />

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>The exemption is the lowest of these three</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <tbody>
            {limits.map((l) => {
              const isLowest = l.value === r.exempt;
              return (
                <tr style={{ borderTop: '1px solid var(--color-border)', fontWeight: isLowest ? 700 : 400 }}>
                  <td style={{ padding: '0.4rem 0' }}>{l.label}</td>
                  <td style={{ padding: '0.4rem 0', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{fmt(l.value)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: '0.6rem 0 0' }}>
          HRA exemption is only available under the old tax regime. Under the new regime, all of your HRA is taxable.
        </p>
      </div>
    </div>
  );
}
