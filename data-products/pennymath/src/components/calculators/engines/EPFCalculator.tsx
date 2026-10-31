import { useState } from 'preact/hooks';
import { epfProjection, type EpfInput } from '../../../lib/formulas/epf';
import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import ChoiceButtons from '../ui/ChoiceButtons';
import Verdict from '../ui/Verdict';

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

  let paidIn = 0;
  const paidInByAge = [0, ...r.yearlyBreakdown.map((y) => (paidIn += y.employee + y.employer))];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="epf-age" label="Your Age" value={age} min={18} max={59} step={1} suffix=" Yr" onChange={setAge} />
        <SliderInput id="epf-retire" label="Retirement Age" value={retirementAge} min={40} max={60} step={1} suffix=" Yr" onChange={setRetirementAge} />
        <SliderInput id="epf-basic" label="Monthly Basic Pay plus DA" value={basic} min={5000} max={500000} step={1000} prefix="₹" scalable locale="en-IN" onChange={setBasic} />
        <SliderInput id="epf-raise" label="Yearly Salary Increase" value={raise} min={0} max={20} step={0.5} suffix="%" onChange={setRaise} />
        <SliderInput id="epf-existing" label="Current EPF Balance" value={existing} min={0} max={10000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setExisting} />
        <SliderInput id="epf-rate" label="EPF Interest Rate (p.a.)" value={rate} min={5} max={12} step={0.05} suffix="%" onChange={setRate} />
        <ChoiceButtons label="PF Is Calculated On" value={pfBasis} options={[{ value: 'full', label: 'Full basic pay' }, { value: 'capped', label: '₹15,000 wage ceiling' }]} onChange={setPfBasis} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'EPF balance at retirement', value: r.finalBalance, highlight: true },
            { label: 'Your contributions', value: r.totalEmployee },
            { label: 'Employer contributions', value: r.totalEmployer },
            { label: 'Interest earned', value: r.totalInterest },
          ]}
        />
        <Verdict title={`In your first month, you pay ${fmt(r.firstMonthEmployee)}`}>
          Your employer matches it, with {fmt(r.firstMonthEmployerEpf)} going to your EPF and {fmt(r.firstMonthEps)} to the Employees' Pension Scheme, which pays a pension and is not part of this balance.
        </Verdict>
      </div>

      <div class="calc-below">
        <LineChart
          title="How your EPF grows"
          caption="At each birthday, in future rupees"
          x={[age, ...r.yearlyBreakdown.map((y) => y.age)]}
          series={[
            { name: 'EPF balance', values: [existing, ...r.yearlyBreakdown.map((y) => y.closingBalance)] },
            { name: 'Paid in', values: paidInByAge },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, 'INR')}
          xTick={(a) => `Age ${a}`}
          xTitle={(a) => `Age ${a}`}
          xHeading="Age"
          showTable={false}
        />
        <details class="year-table panel-card">
          <summary>View year-by-year figures</summary>
          <div class="table-scroll">
            <table>
              <thead>
                <tr><th scope="col">Age</th><th scope="col">You</th><th scope="col">Employer</th><th scope="col">Interest</th><th scope="col">Balance</th></tr>
              </thead>
              <tbody>
                {r.yearlyBreakdown.map((row) => (
                  <tr>
                    <th scope="row">{row.age}</th>
                    <td>{fmt(row.employee)}</td>
                    <td>{fmt(row.employer)}</td>
                    <td>{fmt(row.interest)}</td>
                    <td>{fmt(row.closingBalance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  );
}
