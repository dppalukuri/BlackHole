import { useState } from 'preact/hooks';
import { npsProjection } from '../../../lib/formulas/nps';
import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';

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

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Estimated monthly pension', value: r.monthlyPension, highlight: true },
            { label: 'Corpus at exit', value: r.corpus, seriesKey: 1 },
            { label: 'Lump sum you can take', value: r.lumpSum },
            { label: 'Used to buy the annuity', value: r.annuityPurchase },
            { label: 'Total you invest', value: r.totalInvested, seriesKey: 2 },
          ]}
        />
      </div>

      <div class="calc-below">
        <LineChart
          title="How your NPS grows"
          caption="At each birthday, in future rupees"
          x={[age, ...r.yearlyBreakdown.map((y) => y.age)]}
          series={[
            { name: 'Corpus', values: [existing, ...r.yearlyBreakdown.map((y) => y.corpus)] },
            { name: 'Amount invested', values: [0, ...r.yearlyBreakdown.map((y) => y.invested)] },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, 'INR')}
          xTick={(a) => `Age ${a}`}
          xTitle={(a) => `Age ${a}`}
          xHeading="Age"
        />
      </div>
    </div>
  );
}
