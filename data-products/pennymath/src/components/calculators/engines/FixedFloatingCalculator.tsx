import { useState } from 'preact/hooks';
import { compareFixedFloating } from '../../../lib/formulas/fixed-floating';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

interface FixedFloatingCalculatorProps {
  currency: { code: string; symbol: string };
  /** Benchmark name as borrowers know it, e.g. "3-month EIBOR". */
  benchmarkName: string;
  /** Local word for the amount over the benchmark: "margin" or "spread". */
  marginWord: string;
  /** What this market calls the monthly payment: "payment" or "EMI". */
  paymentWord: string;
  /** Show the minimum-rate input, for markets where floating loans carry a floor. */
  showFloor?: boolean;
  amountRange: { min: number; max: number; step: number };
  maxTenureYears: number;
  defaults: {
    amount: number;
    tenureYears: number;
    fixedRate: number;
    fixedYears: number;
    benchmarkNow: number;
    marginAfterFix: number;
    floatingMargin: number;
  };
}

const pct = (n: number) => `${n.toFixed(2)}%`;
const capitalise = (s: string) => (/^[A-Z]/.test(s) ? s : s[0].toUpperCase() + s.slice(1));

export default function FixedFloatingCalculator({
  currency,
  benchmarkName,
  marginWord,
  paymentWord,
  showFloor = false,
  amountRange,
  maxTenureYears,
  defaults,
}: FixedFloatingCalculatorProps) {
  const [amount, setAmount] = useState(defaults.amount);
  const [years, setYears] = useState(defaults.tenureYears);
  const [fixedRate, setFixedRate] = useState(defaults.fixedRate);
  const [fixedYearsInput, setFixedYears] = useState(defaults.fixedYears);
  const [benchmarkNow, setBenchmarkNow] = useState(defaults.benchmarkNow);
  const [benchmarkAtFixEnd, setBenchmarkAtFixEnd] = useState(defaults.benchmarkNow);
  const [marginAfterFix, setMarginAfterFix] = useState(defaults.marginAfterFix);
  const [floatingMargin, setFloatingMargin] = useState(defaults.floatingMargin);
  const [floorRate, setFloorRate] = useState(0);
  const [switchCost, setSwitchCost] = useState(0);

  // The fixed period must end inside the term, or there is nothing to compare.
  const maxFixedYears = Math.min(10, years - 1);
  const fixedYears = Math.min(fixedYearsInput, maxFixedYears);

  const result = compareFixedFloating({
    principal: amount,
    tenureMonths: years * 12,
    fixedRate,
    fixedMonths: fixedYears * 12,
    benchmarkNow,
    benchmarkAtFixEnd,
    marginAfterFix,
    floatingMargin,
    floorRate: showFloor ? floorRate : 0,
    switchCost,
  });

  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);
  const Payment = capitalise(paymentWord);
  const Margin = capitalise(marginWord);
  const fixedLeg = result.fixedThenFloating;
  const floatLeg = result.floating;

  const gap = Math.abs(result.costDifference);
  const winner = result.costDifference > 0 ? 'Fixing' : 'Floating';
  const breakEven = result.breakEvens[0];
  const jump = Math.abs(result.paymentJump);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="ff-amount" label="Loan Amount or Outstanding Balance" value={amount} min={amountRange.min} max={amountRange.max} step={amountRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setAmount} />
        <SliderInput id="ff-tenure" label="Term Remaining" value={years} min={3} max={maxTenureYears} step={1} suffix=" Yr" onChange={setYears} />
        <SliderInput id="ff-fixed-rate" label="Fixed Rate (p.a.)" value={fixedRate} min={1} max={16} step={0.05} suffix="%" onChange={setFixedRate} />
        <SliderInput id="ff-fixed-years" label="Fixed Period" value={fixedYears} min={1} max={maxFixedYears} step={1} suffix=" Yr" onChange={setFixedYears} />
        <SliderInput id="ff-benchmark-now" label={`${benchmarkName} Today`} value={benchmarkNow} min={0} max={12} step={0.05} suffix="%" onChange={setBenchmarkNow} />
        <SliderInput id="ff-benchmark-end" label={`${benchmarkName} When the Fixed Period Ends (your forecast)`} value={benchmarkAtFixEnd} min={0} max={12} step={0.05} suffix="%" onChange={setBenchmarkAtFixEnd} />
        <details class="calc-more">
          <summary>{Margin}s, fees{showFloor ? ' and minimum rate' : ''}</summary>
          <div class="calc-more-grid">
            <SliderInput id="ff-margin-after" label={`${Margin} After the Fixed Period`} value={marginAfterFix} min={0} max={6} step={0.05} suffix="%" onChange={setMarginAfterFix} />
            <SliderInput id="ff-margin-floating" label={`${Margin} on a Floating Loan from Day One`} value={floatingMargin} min={0} max={6} step={0.05} suffix="%" onChange={setFloatingMargin} />
            {showFloor && <SliderInput id="ff-floor" label="Minimum Floating Rate (0 = none)" value={floorRate} min={0} max={10} step={0.05} suffix="%" onChange={setFloorRate} />}
            <SliderInput id="ff-switch-cost" label="One-Off Cost of Going Floating (0 for a new loan)" value={switchCost} min={0} max={100000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setSwitchCost} />
          </div>
        </details>
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: `Monthly ${paymentWord} from year ${fixedYears + 1}`, value: fixedLeg.paymentAtFixEnd, highlight: true },
            { label: `${Payment} today at ${pct(fixedRate)}`, value: fixedLeg.firstPayment },
            { label: 'Fixed, then floating', note: 'Total cost over the term', value: fixedLeg.totalCost, seriesKey: 1 },
            { label: 'Floating from day one', note: `Total cost, starting at ${fmt(floatLeg.firstPayment)} a month`, value: floatLeg.totalCost, seriesKey: 2 },
          ]}
        />
        <Verdict title={gap < 1 ? 'Both loans cost the same on this forecast' : `${winner} is ${fmt(gap)} cheaper on this forecast`}>
          {result.breakEvens.length > 1 ? (
            <>The cheaper loan changes more than once as {benchmarkName} moves, at {result.breakEvens.map((b) => pct(b.benchmark)).join(' and ')}. Try several forecasts.</>
          ) : breakEven ? (
            <>Break-even: {breakEven.fixingWinsAbove ? 'fixing' : 'floating'} wins if {benchmarkName} is above {pct(breakEven.benchmark)} when the fixed period ends.</>
          ) : (
            <>{winner} stays cheaper at every {benchmarkName} level from 0% to 30%.</>
          )}
          {jump >= 1 && result.paymentJump > 0 && <> Check you could afford the {fmt(jump)} rise in your monthly {paymentWord}.</>}
        </Verdict>
      </div>

      <div class="calc-below">
        <LineChart
          title={`Your ${paymentWord} over time`}
          caption={`${currency.code} a month, at the end of each year`}
          x={fixedLeg.yearlyBreakdown.map((r) => r.year)}
          series={[
            { name: 'Fixed, then floating', values: fixedLeg.yearlyBreakdown.map((r) => r.payment) },
            { name: 'Floating', values: floatLeg.yearlyBreakdown.map((r) => r.payment) },
          ]}
          format={fmt}
          formatTick={(n) => Math.round(n).toLocaleString(locale)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => `Year ${y}`}
          step
          zeroBased={false}
          marker={{ x: fixedYears, label: 'Fixed period ends' }}
          showTable={false}
        />
        <details class="year-table panel-card">
          <summary>View year-by-year figures</summary>
          <div class="table-scroll">
            <table>
              <thead>
                <tr><th scope="col">Year</th><th scope="col">Fixed first: rate</th><th scope="col">{Payment}</th><th scope="col">Balance</th><th scope="col">Floating: rate</th><th scope="col">{Payment}</th><th scope="col">Balance</th></tr>
              </thead>
              <tbody>
                {fixedLeg.yearlyBreakdown.map((row, i) => {
                  const other = floatLeg.yearlyBreakdown[i];
                  return (
                    <tr>
                      <th scope="row">{row.year}</th>
                      <td>{pct(row.rate)}</td>
                      <td>{fmt(row.payment)}</td>
                      <td>{fmt(row.closingBalance)}</td>
                      <td>{pct(other.rate)}</td>
                      <td>{fmt(other.payment)}</td>
                      <td>{fmt(other.closingBalance)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  );
}
