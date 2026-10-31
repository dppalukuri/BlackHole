import { useState } from 'preact/hooks';
import { salaryBreakdown, type SalaryInput } from '../../../lib/formulas/salary';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function SalaryCalculator() {
  const [ctc, setCtc] = useState(1500000);
  const [basicPercent, setBasicPercent] = useState(50);
  const [variable, setVariable] = useState(0);
  const [pfBasis, setPfBasis] = useState<SalaryInput['pfBasis']>('full');
  const [gratuity, setGratuity] = useState<'yes' | 'no'>('no');
  const [pt, setPt] = useState(200);
  const [regime, setRegime] = useState<SalaryInput['regime']>('new');
  const [deductions, setDeductions] = useState(150000);

  const r = salaryBreakdown({
    annualCtc: ctc,
    basicPercent,
    annualVariable: Math.min(variable, ctc),
    pfBasis,
    includeGratuityInCtc: gratuity === 'yes',
    monthlyProfessionalTax: pt,
    regime,
    oldRegimeDeductions: deductions,
  });

  const rows = [
    { label: 'Annual CTC', value: ctc },
    { label: 'Employer PF', value: -r.employerPf },
    ...(r.gratuityProvision > 0 ? [{ label: 'Gratuity provision', value: -r.gratuityProvision }] : []),
    { label: 'Gross salary', value: r.grossSalary, bold: true },
    { label: 'Your PF contribution', value: -r.employeePf },
    { label: 'Professional tax', value: -r.professionalTax },
    { label: 'Income tax with cess', value: -r.incomeTax },
    { label: 'Annual take-home', value: r.annualTakeHome, bold: true },
  ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="sal-ctc" label="Annual CTC" value={ctc} min={200000} max={10000000} step={50000} prefix="₹" scalable locale="en-IN" onChange={setCtc} />
        <SliderInput id="sal-basic" label="Basic Pay as a Share of CTC" value={basicPercent} min={20} max={80} step={1} suffix="%" onChange={setBasicPercent} />
        <SliderInput id="sal-variable" label="Yearly Bonus or Variable Pay in CTC" value={variable} min={0} max={5000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setVariable} />
        <SliderInput id="sal-pt" label="Professional Tax per Month" value={pt} min={0} max={300} step={10} prefix="₹" locale="en-IN" onChange={setPt} />
        <ChoiceButtons label="Tax Regime" value={regime} options={[{ value: 'new', label: 'New regime' }, { value: 'old', label: 'Old regime' }]} onChange={setRegime} />
        {regime === 'old' && (
          <SliderInput id="sal-deductions" label="Old Regime Deductions (80C, HRA and others)" value={deductions} min={0} max={1000000} step={5000} prefix="₹" scalable locale="en-IN" onChange={setDeductions} />
        )}
        <ChoiceButtons label="PF Is Calculated On" value={pfBasis} options={[{ value: 'full', label: 'Full basic pay' }, { value: 'capped', label: '₹15,000 wage ceiling' }]} onChange={setPfBasis} />
        <ChoiceButtons label="Is Gratuity Part of Your CTC?" value={gratuity} options={[{ value: 'no', label: 'No' }, { value: 'yes', label: 'Yes' }]} onChange={setGratuity} />
      </div>

      <ResultCard
        currencyCode="INR"
        results={[
          { label: 'Annual take-home', value: r.annualTakeHome },
          { label: 'Income tax with cess', value: r.incomeTax },
          { label: 'Monthly in-hand salary', value: r.monthlyInHand, highlight: true },
        ]}
      />

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>From CTC to take-home</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <tbody>
            {rows.map((row) => (
              <tr style={{ borderTop: '1px solid var(--color-border)', fontWeight: row.bold ? 700 : 400 }}>
                <td style={{ padding: '0.4rem 0' }}>{row.label}</td>
                <td style={{ padding: '0.4rem 0', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{fmt(row.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
