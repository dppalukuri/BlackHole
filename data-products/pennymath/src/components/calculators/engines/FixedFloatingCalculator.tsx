import { useState } from 'preact/hooks';
import { compareFixedFloating } from '../../../lib/formulas/fixed-floating';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import LineChart from '../ui/LineChart';

interface FixedFloatingCalculatorProps {
  currency: { code: string; symbol: string };
  /** What this market calls the monthly payment: "payment" or "EMI". */
  paymentWord: string;
  amountRange: { min: number; max: number; step: number };
  maxTenureYears: number;
  defaults: {
    amount: number;
    tenureYears: number;
    fixedRate: number;
    fixedYears: number;
    floatingRate: number;
  };
}

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;

/** A fixed rate for a few years, then floating, against floating from day one. Five inputs, one table. */
export default function FixedFloatingCalculator({ currency, paymentWord, amountRange, maxTenureYears, defaults }: FixedFloatingCalculatorProps) {
  const [amount, setAmount] = useState(defaults.amount);
  const [years, setYears] = useState(defaults.tenureYears);
  const [fixedRate, setFixedRate] = useState(defaults.fixedRate);
  const [fixedYearsInput, setFixedYears] = useState(defaults.fixedYears);
  const [floatingRate, setFloatingRate] = useState(defaults.floatingRate);

  // The fixed years must end inside the tenure, or there is nothing to compare.
  const maxFixedYears = Math.min(10, years - 1);
  const fixedYears = Math.min(fixedYearsInput, maxFixedYears);

  // One floating rate for both loans: the floating loan pays it from day one,
  // the other once its fixed years end.
  const result = compareFixedFloating({
    principal: amount,
    tenureMonths: years * 12,
    fixedRate,
    fixedMonths: fixedYears * 12,
    benchmarkNow: floatingRate,
    benchmarkAtFixEnd: floatingRate,
    marginAfterFix: 0,
    floatingMargin: 0,
  });

  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);
  const fixedLeg = result.fixedThenFloating;
  const floatLeg = result.floating;
  const saving = floatLeg.totalInterest - fixedLeg.totalInterest;
  const fixedName = `Fixed for ${plural(fixedYears, 'year')}, then floating`;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="ff-amount" label="Loan amount" value={amount} min={amountRange.min} max={amountRange.max} step={amountRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setAmount} />
        <SliderInput id="ff-tenure" label="Loan tenure" value={years} min={3} max={maxTenureYears} step={1} suffix=" Yr" onChange={setYears} />
        <SliderInput id="ff-fixed-rate" label="Fixed rate (per year)" value={fixedRate} min={1} max={16} step={0.05} suffix="%" onChange={setFixedRate} />
        <SliderInput id="ff-fixed-years" label="Fixed for" value={fixedYears} min={1} max={maxFixedYears} step={1} suffix=" Yr" onChange={setFixedYears} />
        <SliderInput id="ff-floating-rate" label="Floating rate (per year)" value={floatingRate} min={1} max={16} step={0.05} suffix="%" onChange={setFloatingRate} />
      </div>

      <div class="calc-answer">
        <div class="result-card ff-compare">
          <table>
            <thead>
              <tr>
                <th scope="col"><span class="sr-only">Cost</span></th>
                <th scope="col"><i class="swatch-dot series-1" aria-hidden="true"></i>{fixedName}</th>
                <th scope="col"><i class="swatch-dot series-2" aria-hidden="true"></i>Floating throughout</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Monthly {paymentWord}</th>
                <td>
                  {fmt(fixedLeg.firstPayment)}
                  {Math.abs(fixedLeg.paymentAtFixEnd - fixedLeg.firstPayment) >= 1 && <small>{fmt(fixedLeg.paymentAtFixEnd)} from year {fixedYears + 1}</small>}
                </td>
                <td>{fmt(floatLeg.firstPayment)}</td>
              </tr>
              <tr>
                <th scope="row">Total interest</th>
                <td>{fmt(fixedLeg.totalInterest)}</td>
                <td>{fmt(floatLeg.totalInterest)}</td>
              </tr>
              <tr>
                <th scope="row">Total amount</th>
                <td>{fmt(amount + fixedLeg.totalInterest)}</td>
                <td>{fmt(amount + floatLeg.totalInterest)}</td>
              </tr>
            </tbody>
          </table>
          <div class="ff-saving">
            <strong>{Math.abs(saving) < 1 ? 'Both cost the same' : `${saving > 0 ? 'Fixing first' : 'Floating'} saves ${fmt(Math.abs(saving))}`}</strong>
            <p>Assumes the floating rate stays at {floatingRate}% for the whole loan. Try a higher and a lower rate to see how the answer changes.</p>
          </div>
        </div>
      </div>

      <div class="calc-below">
        <LineChart
          title={`Your monthly ${paymentWord}`}
          caption={`${currency.code} a month, at the end of each year`}
          x={fixedLeg.yearlyBreakdown.map((r) => r.year)}
          series={[
            { name: fixedName, values: fixedLeg.yearlyBreakdown.map((r) => r.payment) },
            { name: 'Floating throughout', values: floatLeg.yearlyBreakdown.map((r) => r.payment) },
          ]}
          format={fmt}
          formatTick={(n) => Math.round(n).toLocaleString(locale)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => `Year ${y}`}
          step
          zeroBased={false}
          marker={{ x: fixedYears, label: 'Fixed rate ends' }}
          showTable={false}
        />
      </div>
    </div>
  );
}
