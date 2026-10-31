import { useState } from 'preact/hooks';
import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';
import { stepUpSipProjection } from '../../../lib/formulas/step-up-sip';
import { sipFutureValue } from '../../../lib/formulas/compound-growth';

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function StepUpSIPCalculator() {
  const [monthly, setMonthly] = useState(10000);
  const [rate, setRate] = useState(12);
  const [years, setYears] = useState(15);
  const [stepUp, setStepUp] = useState(10);

  const stepped = stepUpSipProjection(monthly, rate, years, stepUp);
  const regular = sipFutureValue(monthly, rate, years);
  const extraWealth = stepped.totalValue - regular.totalValue;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="monthly" label="Starting Monthly SIP" value={monthly} min={500} max={500000} step={500} prefix="₹" scalable locale="en-IN" onChange={setMonthly} />
        <SliderInput id="step-up" label="Annual Step-Up" value={stepUp} min={0} max={50} step={1} suffix="%" onChange={setStepUp} />
        <SliderInput id="return-rate" label="Expected Return (p.a.)" value={rate} min={1} max={25} step={0.5} suffix="%" onChange={setRate} />
        <SliderInput id="years" label="Time Period" value={years} min={1} max={30} step={1} suffix=" Yr" onChange={setYears} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: `Value after ${years} ${years === 1 ? 'year' : 'years'}`, value: stepped.totalValue, highlight: true },
            { label: 'Regular SIP would reach', value: regular.totalValue, seriesKey: 2 },
            { label: 'Total you invest', value: stepped.totalInvested, seriesKey: 3 },
            { label: 'Estimated returns', value: stepped.totalReturns },
          ]}
        />
        <Verdict title={`Stepping up adds ${fmt(extraWealth)}`} tone="good">
          That is against keeping your SIP at {fmt(monthly)} a month for the whole period.
        </Verdict>
      </div>

      <div class="calc-below">
        <LineChart
          title="Step-up against a regular SIP"
          caption="At the end of each year"
          x={[0, ...stepped.yearlyBreakdown.map((r) => r.year)]}
          series={[
            { name: 'Step-up SIP', values: [0, ...stepped.yearlyBreakdown.map((r) => r.value)] },
            { name: 'Regular SIP', values: [0, ...regular.yearlyBreakdown.map((r) => r.total)] },
            { name: 'Amount invested', values: [0, ...stepped.yearlyBreakdown.map((r) => r.invested)] },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, 'INR')}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
          showTable={false}
        />
        <details class="year-table panel-card">
          <summary>View year-by-year figures</summary>
          <div class="table-scroll">
            <table>
              <thead>
                <tr><th scope="col">Year</th><th scope="col">Monthly SIP</th><th scope="col">Total invested</th><th scope="col">Portfolio value</th></tr>
              </thead>
              <tbody>
                {stepped.yearlyBreakdown.map((row) => (
                  <tr>
                    <th scope="row">{row.year}</th>
                    <td>{fmt(row.monthlySIP)}</td>
                    <td>{fmt(row.invested)}</td>
                    <td>{fmt(row.value)}</td>
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
