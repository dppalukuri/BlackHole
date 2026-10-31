import { useState } from 'preact/hooks';
import { hraExemption, type HraCityGroup, type HraYear } from '../../../lib/formulas/hra';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';
import Verdict from '../ui/Verdict';

export default function HRACalculator() {
  const [salary, setSalary] = useState(60000);
  const [hra, setHra] = useState(24000);
  const [rent, setRent] = useState(25000);
  const [city, setCity] = useState<HraCityGroup>('new-metro');
  const [year, setYear] = useState<HraYear>('fy-2026-27');

  const r = hraExemption({ annualSalary: salary * 12, annualHraReceived: hra * 12, annualRentPaid: rent * 12, city, year });
  const limitNames = {
    'actual-hra': 'the HRA you received',
    rent: 'your rent minus 10% of salary',
    salary: `${r.salaryPercent}% of your salary`,
  };

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

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Exempt HRA for the year', value: r.exempt, highlight: true },
            { label: 'Taxable HRA', value: r.taxable },
            { label: 'Limit 1: HRA you received', value: r.actualHra },
            { label: 'Limit 2: rent minus 10% of salary', value: r.rentMinusTenPercent },
            { label: `Limit 3: ${r.salaryPercent}% of salary`, value: r.percentOfSalary },
          ]}
        />
        <Verdict title={`Your exemption is set by ${limitNames[r.limitedBy]}`}>
          The exemption is the lowest of the three limits. It only applies under the old tax regime. Under the new regime, all of your HRA is taxable.
        </Verdict>
      </div>
    </div>
  );
}
