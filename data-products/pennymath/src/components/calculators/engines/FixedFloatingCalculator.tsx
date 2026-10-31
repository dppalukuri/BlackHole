import { useState } from 'preact/hooks';
import { compareFixedFloating } from '../../../lib/formulas/fixed-floating';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

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
  const fixingWins = result.costDifference > 0;
  const paymentRises = result.paymentJump >= 0;
  const breakEven = result.breakEvens[0];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="ff-amount"
          label="Loan Amount or Outstanding Balance"
          value={amount}
          min={amountRange.min}
          max={amountRange.max}
          step={amountRange.step}
          prefix={currency.symbol}
          scalable
          locale={locale}
          onChange={setAmount}
        />
        <SliderInput
          id="ff-tenure"
          label="Term Remaining"
          value={years}
          min={3}
          max={maxTenureYears}
          step={1}
          suffix=" Yr"
          onChange={setYears}
        />
        <SliderInput
          id="ff-fixed-rate"
          label="Fixed Rate (p.a.)"
          value={fixedRate}
          min={1}
          max={16}
          step={0.05}
          suffix="%"
          onChange={setFixedRate}
        />
        <SliderInput
          id="ff-fixed-years"
          label="Fixed Period"
          value={fixedYears}
          min={1}
          max={maxFixedYears}
          step={1}
          suffix=" Yr"
          onChange={setFixedYears}
        />
        <SliderInput
          id="ff-benchmark-now"
          label={`${benchmarkName} Today`}
          value={benchmarkNow}
          min={0}
          max={12}
          step={0.05}
          suffix="%"
          onChange={setBenchmarkNow}
        />
        <SliderInput
          id="ff-benchmark-end"
          label={`${benchmarkName} When the Fixed Period Ends (your forecast)`}
          value={benchmarkAtFixEnd}
          min={0}
          max={12}
          step={0.05}
          suffix="%"
          onChange={setBenchmarkAtFixEnd}
        />
        <SliderInput
          id="ff-margin-after"
          label={`${Margin} After the Fixed Period`}
          value={marginAfterFix}
          min={0}
          max={6}
          step={0.05}
          suffix="%"
          onChange={setMarginAfterFix}
        />
        <SliderInput
          id="ff-margin-floating"
          label={`${Margin} on a Floating Loan from Day One`}
          value={floatingMargin}
          min={0}
          max={6}
          step={0.05}
          suffix="%"
          onChange={setFloatingMargin}
        />
        {showFloor && (
          <SliderInput
            id="ff-floor"
            label="Minimum Floating Rate, If Any (0 = none)"
            value={floorRate}
            min={0}
            max={10}
            step={0.05}
            suffix="%"
            onChange={setFloorRate}
          />
        )}
        <SliderInput
          id="ff-switch-cost"
          label="One-Off Cost of Going Floating (0 if taking a new loan)"
          value={switchCost}
          min={0}
          max={100000}
          step={500}
          prefix={currency.symbol}
          scalable
          locale={locale}
          onChange={setSwitchCost}
        />
      </div>

      <div class="calc-results">
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>Fixed, then floating</h3>
          <ResultCard
            currencyCode={currency.code}
            results={[
              { label: `${Payment} at ${pct(fixedRate)}`, value: fixedLeg.firstPayment },
              { label: `${Payment} from year ${fixedYears + 1} at ${pct(fixedLeg.rateAtFixEnd)}`, value: fixedLeg.paymentAtFixEnd },
              { label: 'Total cost over the term', value: fixedLeg.totalCost, highlight: true },
            ]}
          />
        </div>
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>Floating from day one</h3>
          <ResultCard
            currencyCode={currency.code}
            results={[
              { label: `${Payment} today at ${pct(floatLeg.firstRate)}`, value: floatLeg.firstPayment },
              { label: `${Payment} from year ${fixedYears + 1} at ${pct(floatLeg.rateAtFixEnd)}`, value: floatLeg.paymentAtFixEnd },
              { label: 'Total cost over the term', value: floatLeg.totalCost, highlight: true },
            ]}
          />
        </div>
      </div>

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>
          {gap < 1
            ? 'Both loans cost the same on this forecast'
            : `${fixingWins ? 'Fixing' : 'Floating'} is ${fmt(gap)} cheaper on this forecast`}
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: '0 0 0.5rem' }}>
          When the fixed period ends, your {paymentWord}{' '}
          {Math.abs(result.paymentJump) < 1 ? (
            'stays about the same'
          ) : (
            <>
              {paymentRises ? 'rises' : 'falls'} by{' '}
              <strong>
                {fmt(Math.abs(result.paymentJump))}/month ({Math.abs(result.paymentJumpPercent).toFixed(1)}%)
              </strong>
            </>
          )}
          .{result.paymentJump >= 1 && ' Check that you could afford the higher amount before you rely on the lower fixed rate.'}
        </p>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          {result.breakEvens.length > 1 ? (
            <>
              The cheaper loan changes more than once as {benchmarkName} moves, at{' '}
              <strong>{result.breakEvens.map((b) => pct(b.benchmark)).join(' and ')}</strong>, so try several
              forecasts before you decide.
            </>
          ) : breakEven ? (
            <>
              Break-even: {breakEven.fixingWinsAbove ? 'fixing' : 'floating'} wins if {benchmarkName} is above{' '}
              <strong>{pct(breakEven.benchmark)}</strong> when the fixed period ends, and{' '}
              {breakEven.fixingWinsAbove ? 'floating' : 'fixing'} wins if it is below that.
            </>
          ) : (
            <>
              {fixingWins ? 'Fixing' : 'Floating'} stays cheaper at every {benchmarkName} level from 0% to 30%, so
              your rate forecast does not change the answer here.
            </>
          )}
        </p>
      </div>

      <details style={{ marginTop: '1.25rem' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>
          View Year-by-Year Breakdown
        </summary>
        <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ textAlign: 'right', color: 'var(--color-text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '0.5rem 0.6rem', fontWeight: 600 }}>Year</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Fixed loan rate</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>{Payment}</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Balance</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Floating loan rate</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>{Payment}</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Balance</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: 'var(--font-mono)' }}>
              {fixedLeg.yearlyBreakdown.map((row, i) => {
                const other = floatLeg.yearlyBreakdown[i];
                return (
                  <tr style={{ borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
                    <td style={{ textAlign: 'left', padding: '0.45rem 0.6rem', fontWeight: 600 }}>{row.year}</td>
                    <td style={{ padding: '0.45rem 0.6rem' }}>{pct(row.rate)}</td>
                    <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.payment)}</td>
                    <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.closingBalance)}</td>
                    <td style={{ padding: '0.45rem 0.6rem' }}>{pct(other.rate)}</td>
                    <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(other.payment)}</td>
                    <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(other.closingBalance)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
