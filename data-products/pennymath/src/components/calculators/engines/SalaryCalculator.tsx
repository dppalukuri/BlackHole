import { useState } from 'preact/hooks';
import { salaryBreakdown, type SalaryInput } from '../../../lib/formulas/salary';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

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

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="sal-ctc" label="Annual CTC" value={ctc} min={200000} max={10000000} step={50000} prefix="₹" scalable locale="en-IN" onChange={setCtc} />
        <SliderInput id="sal-basic" label="Basic Pay as a Share of CTC" value={basicPercent} min={20} max={80} step={1} suffix="%" onChange={setBasicPercent} />
        <SliderInput id="sal-variable" label="Yearly Bonus or Variable Pay in CTC" value={variable} min={0} max={5000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setVariable} />
        <SliderInput id="sal-pt" label="Professional Tax per Month" value={pt} min={0} max={300} step={10} prefix="₹" locale="en-IN" onChange={setPt} />
        <ChoiceButtons label="Tax Regime" value={regime} options={[{ value: 'new', label: 'New regime' }, { value: 'old', label: 'Old regime' }]} onChange={setRegime} />
        {regime === 'old' && (
          <div class="span-all">
            <SliderInput id="sal-deductions" label="Old Regime Deductions (80C, HRA and others)" value={deductions} min={0} max={1000000} step={5000} prefix="₹" scalable locale="en-IN" onChange={setDeductions} />
          </div>
        )}
        <ChoiceButtons label="PF Is Calculated On" value={pfBasis} options={[{ value: 'full', label: 'Full basic pay' }, { value: 'capped', label: '₹15,000 wage ceiling' }]} onChange={setPfBasis} />
        <ChoiceButtons label="Is Gratuity Part of Your CTC?" value={gratuity} options={[{ value: 'no', label: 'No' }, { value: 'yes', label: 'Yes' }]} onChange={setGratuity} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Monthly in-hand salary', value: r.monthlyInHand, highlight: true },
            { label: 'Annual take-home', value: r.annualTakeHome },
            { label: 'Employer PF', note: 'Part of your CTC', value: r.employerPf },
            ...(r.gratuityProvision > 0 ? [{ label: 'Gratuity provision', note: 'Part of your CTC', value: r.gratuityProvision }] : []),
            { label: 'Gross salary', value: r.grossSalary },
            { label: 'Your PF contribution', value: r.employeePf },
            { label: 'Professional tax', value: r.professionalTax },
            { label: 'Income tax with cess', value: r.incomeTax },
          ]}
        />
      </div>
    </div>
  );
}
