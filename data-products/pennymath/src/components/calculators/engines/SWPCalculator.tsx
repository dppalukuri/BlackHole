import { useState } from 'preact/hooks';
import { swpProjection } from '../../../lib/formulas/swp';
import { formatCompactCurrency, formatCurrency, formatPeriod, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

interface SWPCalculatorProps {
  currency: { code: string; symbol: string };
  defaults?: {
    totalInvestment?: number;
    monthlyWithdrawal?: number;
    expectedReturn?: number;
    timePeriod?: number;
  };
}

export default function SWPCalculator({ currency, defaults }: SWPCalculatorProps) {
  const [investment, setInvestment] = useState(defaults?.totalInvestment ?? 1000000);
  const [withdrawal, setWithdrawal] = useState(defaults?.monthlyWithdrawal ?? 8000);
  const [rate, setRate] = useState(defaults?.expectedReturn ?? 8);
  const [years, setYears] = useState(defaults?.timePeriod ?? 10);

  const result = swpProjection(investment, withdrawal, rate, years);
  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);

  const totalMonths = years * 12;
  const ranOutEarly = result.depleted && result.monthsLasted < totalMonths;

  let withdrawnSoFar = 0;
  const withdrawnByYear = [0, ...result.yearlyBreakdown.map((r) => (withdrawnSoFar += r.withdrawn))];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="total-investment" label="Total Investment" value={investment} min={10000} max={50000000} step={10000} prefix={currency.symbol} scalable locale={locale} onChange={setInvestment} />
        <SliderInput id="monthly-withdrawal" label="Monthly Withdrawal" value={withdrawal} min={500} max={500000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setWithdrawal} />
        <SliderInput id="expected-return" label="Expected Return Rate (p.a.)" value={rate} min={1} max={30} step={0.5} suffix="%" onChange={setRate} />
        <SliderInput id="time-period" label="Time Period" value={years} min={1} max={40} step={1} suffix=" Yr" onChange={setYears} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: `Balance after ${years} ${years === 1 ? 'year' : 'years'}`, value: result.finalBalance, highlight: true },
            { label: 'Total withdrawn', value: result.totalWithdrawn, seriesKey: 2 },
          ]}
        />
        {ranOutEarly ? (
          <Verdict title={`Your corpus runs out after ${formatPeriod(result.monthsLasted)}`} tone="bad">
            Only {result.monthsLasted} of your {totalMonths} planned withdrawals are funded. Withdraw up to {fmt(result.sustainableWithdrawal)} a month to live off returns alone and leave the capital untouched.
          </Verdict>
        ) : (
          <Verdict title={`This corpus earns about ${fmt(result.sustainableWithdrawal)} a month`} tone="good">
            At {rate}% a year, withdraw less than that and your capital keeps growing. Withdraw more and you start eating into it.
          </Verdict>
        )}
      </div>

      <div class="calc-below">
        <LineChart
          title="Your corpus over time"
          caption="At the end of each year"
          x={[0, ...result.yearlyBreakdown.map((r) => r.year)]}
          series={[
            { name: 'Balance left', values: [investment, ...result.yearlyBreakdown.map((r) => r.closingBalance)] },
            { name: 'Withdrawn so far', values: withdrawnByYear },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, currency.code)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
          showTable={false}
        />
        <details class="year-table panel-card">
          <summary>View year-by-year figures</summary>
          <div class="table-scroll">
            <table>
              <thead>
                <tr><th scope="col">Year</th><th scope="col">Opening</th><th scope="col">Withdrawn</th><th scope="col">Returns</th><th scope="col">Closing</th></tr>
              </thead>
              <tbody>
                {result.yearlyBreakdown.map((row) => (
                  <tr>
                    <th scope="row">{row.year}</th>
                    <td>{fmt(row.openingBalance)}</td>
                    <td>{fmt(row.withdrawn)}</td>
                    <td>{fmt(row.returnsEarned)}</td>
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
