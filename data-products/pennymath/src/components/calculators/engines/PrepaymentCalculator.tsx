import { useState } from 'preact/hooks';
import { comparePrepayment } from '../../../lib/formulas/prepayment';
import { formatCompactCurrency, formatCurrency, formatPeriod, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

interface PrepaymentCalculatorProps {
  currency: { code: string; symbol: string };
  paymentWord: string;
  /** Local name for the loan period: "term" or "tenure". */
  termWord: string;
  amountRange: { min: number; max: number; step: number };
  maxTenureYears: number;
  /** Fee cap as a share of balance, shown as a prompt where one applies. */
  feeCap?: { percent: number; max: number };
  defaults: { balance: number; annualRate: number; remainingYears: number; lumpSum: number; fee: number };
}

export default function PrepaymentCalculator({
  currency,
  paymentWord,
  termWord,
  amountRange,
  maxTenureYears,
  feeCap,
  defaults,
}: PrepaymentCalculatorProps) {
  const [balance, setBalance] = useState(defaults.balance);
  const [annualRate, setAnnualRate] = useState(defaults.annualRate);
  const [years, setYears] = useState(defaults.remainingYears);
  const [lumpSum, setLumpSum] = useState(defaults.lumpSum);
  const [extraMonthly, setExtraMonthly] = useState(0);
  const [fee, setFee] = useState(defaults.fee);

  const r = comparePrepayment({ balance, annualRate, remainingMonths: years * 12, lumpSum, extraMonthly, fee });
  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);
  const Term = termWord[0].toUpperCase() + termWord.slice(1);
  const cap = feeCap ? Math.min((balance * feeCap.percent) / 100, feeCap.max) : null;
  const edge = r.shorterTerm.netSaving - r.lowerPayment.netSaving;
  const monthsSaved = years * 12 - r.shorterTerm.months;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="pp-balance" label="Outstanding Loan Balance" value={balance} min={amountRange.min} max={amountRange.max} step={amountRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setBalance} />
        <SliderInput id="pp-rate" label="Interest Rate (p.a.)" value={annualRate} min={1} max={18} step={0.05} suffix="%" onChange={setAnnualRate} />
        <SliderInput id="pp-years" label={`${Term} Remaining`} value={years} min={1} max={maxTenureYears} step={1} suffix=" Yr" onChange={setYears} />
        <SliderInput id="pp-lump" label="Lump Sum to Prepay Today" value={lumpSum} min={0} max={amountRange.max} step={amountRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setLumpSum} />
        <SliderInput id="pp-extra" label="Extra Payment Every Month" value={extraMonthly} min={0} max={100000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setExtraMonthly} />
        <SliderInput id="pp-fee" label="Prepayment Fee, If Any" value={fee} min={0} max={100000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setFee} />
        {cap !== null && (
          <div class="calc-note">The {feeCap!.percent}% cap on this balance comes to {fmt(cap)}. Your bank may charge less, so check your contract.</div>
        )}
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'Finishing sooner saves you, after fees', value: r.shorterTerm.netSaving, highlight: true },
            { label: 'Loan finishes in', note: `${formatPeriod(monthsSaved)} early, at ${fmt(r.shorterTerm.payment)} a month`, value: formatPeriod(r.shorterTerm.months), seriesKey: 2 },
            { label: `Or pay less: new ${paymentWord}`, note: `${fmt(r.baselinePayment - r.lowerPayment.payment)} a month lower`, value: r.lowerPayment.payment, seriesKey: 3 },
            { label: 'Paying less saves you, after fees', value: r.lowerPayment.netSaving },
          ]}
        />
        <Verdict title={edge >= 1 ? `Finishing sooner saves ${fmt(edge)} more` : 'Both options save the same'}>
          Paying less each month leaves more cash free, which can matter more if your income is tight.
        </Verdict>
      </div>

      <div class="calc-below">
        <LineChart
          title="Your balance on each path"
          caption="At the end of each year"
          x={r.yearly.map((y) => y.year)}
          series={[
            { name: 'No prepayment', values: r.yearly.map((y) => y.baseline) },
            { name: 'Finish sooner', values: r.yearly.map((y) => y.shorterTerm) },
            { name: 'Pay less monthly', values: r.yearly.map((y) => y.lowerPayment) },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, currency.code)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
        />
      </div>
    </div>
  );
}
