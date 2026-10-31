import { useState } from 'preact/hooks';
import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';
import { fireProjection } from '../../../lib/formulas/fire';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function FIRECalculator() {
  const [monthlyExpenses, setMonthlyExpenses] = useState(50000);
  const [currentSavings, setCurrentSavings] = useState(500000);
  const [monthlySavings, setMonthlySavings] = useState(30000);
  const [expectedReturn, setExpectedReturn] = useState(12);
  const [inflationRate, setInflationRate] = useState(6);
  const [withdrawalRate, setWithdrawalRate] = useState(3);
  const [currentAge, setCurrentAge] = useState(28);

  const { realReturn, fireNumber, yearsToFire, fireAge, canRetire, monthlyPassiveIncome, milestones } = fireProjection({
    monthlyExpenses,
    currentSavings,
    monthlySavings,
    expectedReturn,
    inflationRate,
    withdrawalRate,
    currentAge,
  });

  const ages = [currentAge, ...milestones.map((m) => currentAge + m.year)];
  const corpus = [currentSavings, ...milestones.map((m) => m.corpus)];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="current-age" label="Your Current Age" value={currentAge} min={18} max={60} step={1} suffix=" yr" onChange={setCurrentAge} />
        <SliderInput id="monthly-expenses" label="Monthly Expenses Today" value={monthlyExpenses} min={5000} max={500000} step={1000} prefix="₹" scalable locale="en-IN" onChange={setMonthlyExpenses} />
        <SliderInput id="current-savings" label="Savings and Investments Today" value={currentSavings} min={0} max={50000000} step={50000} prefix="₹" scalable locale="en-IN" onChange={setCurrentSavings} />
        <SliderInput id="monthly-savings" label="Monthly Savings" value={monthlySavings} min={0} max={500000} step={1000} prefix="₹" scalable locale="en-IN" onChange={setMonthlySavings} />
        <SliderInput id="return" label="Expected Return (p.a.)" value={expectedReturn} min={1} max={20} step={0.5} suffix="%" onChange={setExpectedReturn} />
        <SliderInput id="inflation" label="Inflation Rate" value={inflationRate} min={1} max={12} step={0.5} suffix="%" onChange={setInflationRate} />
        <SliderInput id="withdrawal" label="Safe Withdrawal Rate" value={withdrawalRate} min={2} max={5} step={0.25} suffix="%" onChange={setWithdrawalRate} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            {
              label: canRetire ? 'You could reach financial independence at age' : 'Financial independence',
              value: canRetire ? String(Math.round(fireAge)) : 'Over 50 years away',
              highlight: true,
            },
            { label: 'Your FIRE number', note: "In today's money", value: fireNumber, seriesKey: 2 },
            { label: 'Monthly income it provides', value: monthlyPassiveIncome },
            { label: 'Return after inflation', value: `${realReturn.toFixed(1)}%` },
            { label: 'Progress so far', value: `${Math.min(100, (currentSavings / fireNumber) * 100).toFixed(1)}%` },
          ]}
        />
        {canRetire ? (
          <Verdict title={`That is ${yearsToFire.toFixed(1)} years from now`} tone="good">
            Saving more, spending less or earning a higher return would all bring it closer.
          </Verdict>
        ) : (
          <Verdict title="At this savings rate, you do not get there within 50 years" tone="bad">
            Try raising your monthly savings or lowering your expenses.
          </Verdict>
        )}
      </div>

      {ages.length > 1 && (
        <div class="calc-below">
          <LineChart
            title="Your path to financial independence"
            caption="In today's money, at each birthday"
            x={ages}
            series={[
              { name: 'Your savings', values: corpus },
              { name: 'FIRE number', values: ages.map(() => fireNumber) },
            ]}
            format={fmt}
            formatTick={(n) => formatCompactCurrency(n, 'INR')}
            xTick={(a) => `Age ${a}`}
            xTitle={(a) => `Age ${a}`}
            xHeading="Age"
          />
        </div>
      )}
    </div>
  );
}
