import { useState } from 'preact/hooks';
import { compareLoanTakeover } from '../../../lib/formulas/loan-takeover';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

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

const formatPeriod = (months: number) => {
  const y = Math.floor(months / 12);
  const m = months % 12;
  const parts = [];
  if (y > 0) parts.push(`${y} ${y === 1 ? 'year' : 'years'}`);
  if (m > 0) parts.push(`${m} ${m === 1 ? 'month' : 'months'}`);
  return parts.join(' ');
};

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
  const longer = newYears > remainingYears;
  const cap = exitFeeCap ? Math.min((balance * exitFeeCap.percent) / 100, exitFeeCap.max) : null;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="lt-balance" label="Outstanding Loan Balance" value={balance} min={amountRange.min} max={amountRange.max} step={amountRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setBalance} />
        <SliderInput id="lt-current-rate" label="Current Interest Rate (p.a.)" value={currentRate} min={1} max={16} step={0.05} suffix="%" onChange={setCurrentRate} />
        <SliderInput id="lt-remaining" label="Term Remaining" value={remainingYears} min={1} max={maxTenureYears} step={1} suffix=" Yr" onChange={setRemainingYears} />
        <SliderInput id="lt-new-rate" label="New Lender's Rate (p.a.)" value={newRate} min={1} max={16} step={0.05} suffix="%" onChange={setNewRate} />
        <SliderInput id="lt-new-years" label="New Loan Term" value={newYears} min={1} max={maxTenureYears} step={1} suffix=" Yr" onChange={setNewYears} />
        <SliderInput id="lt-exit-fee" label="Exit Fee on Current Loan" value={exitFee} min={0} max={100000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setExitFee} />
        {cap !== null && (
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: '-0.6rem 0 0' }}>
            The {exitFeeCap!.percent}% cap on this balance comes to {fmt(cap)}. Check your contract for the actual fee.
          </p>
        )}
        <SliderInput id="lt-new-costs" label="Costs of the New Loan" value={newLoanCosts} min={0} max={200000} step={500} prefix={currency.symbol} scalable locale={locale} onChange={setNewLoanCosts} />
      </div>

      <div class="calc-results">
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>Stay with current lender</h3>
          <ResultCard
            currencyCode={currency.code}
            results={[
              { label: `${Payment} at ${currentRate.toFixed(2)}%`, value: r.currentPayment },
              { label: 'Fees to pay now', value: 0 },
              { label: 'Total interest left to pay', value: r.currentInterest, highlight: true },
            ]}
          />
        </div>
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>Move to new lender</h3>
          <ResultCard
            currencyCode={currency.code}
            results={[
              { label: `${Payment} at ${newRate.toFixed(2)}%`, value: r.newPayment },
              { label: 'Fees to pay now', value: r.totalFees },
              { label: 'Total interest left to pay', value: r.newInterest, highlight: true },
            ]}
          />
        </div>
      </div>

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>
          {worthIt
            ? `Moving saves ${fmt(r.netSaving)} after fees`
            : `Moving costs ${fmt(Math.abs(r.netSaving))} more after fees`}
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: '0 0 0.5rem' }}>
          {r.breakEvenMonth !== null ? (
            <>
              You recover the fees after <strong>{formatPeriod(r.breakEvenMonth)}</strong>. If you might sell or
              repay the loan before then, staying is cheaper.
            </>
          ) : (
            <>This move never recovers its fees at these rates.</>
          )}
        </p>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          Your {paymentWord} {r.monthlySaving >= 0 ? 'falls' : 'rises'} by{' '}
          <strong>{fmt(Math.abs(r.monthlySaving))}/month</strong>.
          {longer && ' The longer term lowers the monthly amount partly by spreading repayment out, which adds interest.'}
        </p>
      </div>
    </div>
  );
}
