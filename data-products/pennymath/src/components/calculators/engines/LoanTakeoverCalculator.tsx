import { useState } from 'preact/hooks';
import { compareLoanTakeover } from '../../../lib/formulas/loan-takeover';
import { formatCompactCurrency, formatCurrency, formatPeriod, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

interface LoanTakeoverCalculatorProps {
  currency: { code: string; symbol: string };
  paymentWord: string;
  /** Regulated cap on the exit fee, shown beside the input when one applies. */
  exitFeeCap?: { percent: number; max: number };
  amountRange: { min: number; max: number; step: number };
  maxTenureYears: number;
  defaults: {
    balance: number;
    currentRate: number;
    remainingYears: number;
    newRate: number;
    exitFee: number;
    newLoanCosts: number;
  };
}

export default function LoanTakeoverCalculator({
  currency,
  paymentWord,
  exitFeeCap,
  amountRange,
  maxTenureYears,
  defaults,
}: LoanTakeoverCalculatorProps) {
  const [balance, setBalance] = useState(defaults.balance);
  const [currentRate, setCurrentRate] = useState(defaults.currentRate);
  const [remainingYears, setRemainingYears] = useState(defaults.remainingYears);
  const [newRate, setNewRate] = useState(defaults.newRate);
  const [newYears, setNewYears] = useState(defaults.remainingYears);
  const [exitFee, setExitFee] = useState(defaults.exitFee);
  const [newLoanCosts, setNewLoanCosts] = useState(defaults.newLoanCosts);

  const r = compareLoanTakeover({
    balance,
    currentRate,
    remainingMonths: remainingYears * 12,
    newRate,
    newTenureMonths: newYears * 12,
    exitFee,
    newLoanCosts,
  });

  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);
  const Payment = paymentWord[0].toUpperCase() + paymentWord.slice(1);
  const worthIt = r.netSaving > 0;
  const cap = exitFeeCap ? Math.min((balance * exitFeeCap.percent) / 100, exitFeeCap.max) : null;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="lt-balance" label="Outstanding Loan Balance" value={balance} min={amountRange.min} max={amountRange.max} step={amountRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setBalance} />
        <SliderInput id="lt-remaining" label="Term Remaining" value={remainingYears} min={1} max={maxTenureYears} step={1} suffix=" Yr" onChange={setRemainingYears} />
        <SliderInput id="lt-current-rate" label="Current Interest Rate (p.a.)" value={currentRate} min={1} max={16} step={0.05} suffix="%" onChange={setCurrentRate} />
        <SliderInput id="lt-new-rate" label="New Lender's Rate (p.a.)" value={newRate} min={1} max={16} step={0.05} suffix="%" onChange={setNewRate} />
        <SliderInput id="lt-new-years" label="New Loan Term" value={newYears} min={1} max={maxTenureYears} step={1} suffix=" Yr" onChange={setNewYears} />
        <SliderInput id="lt-exit-fee" label="Exit Fee on Current Loan" value={exitFee} min={0} max={100000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setExitFee} />
        <SliderInput id="lt-new-costs" label="Costs of the New Loan" value={newLoanCosts} min={0} max={200000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setNewLoanCosts} />
        {cap !== null && (
          <div class="calc-note">The {exitFeeCap!.percent}% cap on this balance comes to {fmt(cap)}. Check your contract for the actual fee.</div>
        )}
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: worthIt ? 'Moving saves you, after fees' : 'Moving costs you, after fees', value: Math.abs(r.netSaving), highlight: true },
            { label: `${Payment} if you stay`, value: r.currentPayment },
            { label: `${Payment} if you move`, value: r.newPayment },
            { label: 'Interest left if you stay', value: r.currentInterest, seriesKey: 1 },
            { label: 'Interest and fees if you move', value: r.newInterest + r.totalFees, seriesKey: 2 },
          ]}
        />
        {r.breakEvenMonth !== null ? (
          <Verdict title={`You recover the fees after ${formatPeriod(r.breakEvenMonth)}`} tone={worthIt ? 'good' : 'warn'}>
            If you might sell or repay the loan before then, staying is cheaper.
            {newYears > remainingYears && ' The longer term lowers the monthly amount partly by spreading repayment out, which adds interest.'}
          </Verdict>
        ) : (
          <Verdict title="This move never recovers its fees at these rates" tone="bad" />
        )}
      </div>

      <div class="calc-below">
        <LineChart
          title="Staying against moving"
          caption="Interest paid so far, plus fees if you move"
          x={r.yearly.map((y) => y.year)}
          series={[
            { name: 'If you stay', values: r.yearly.map((y) => y.stay) },
            { name: 'If you move', values: r.yearly.map((y) => y.move) },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, currency.code)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
          marker={r.breakEvenMonth !== null ? { x: r.breakEvenMonth / 12, label: 'Break-even' } : null}
        />
      </div>
    </div>
  );
}
