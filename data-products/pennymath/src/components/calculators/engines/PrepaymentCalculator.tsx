import { useState } from 'preact/hooks';
import { comparePrepayment } from '../../../lib/formulas/prepayment';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

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

const formatPeriod = (months: number) => {
  if (months === 0) return '0 months';
  const y = Math.floor(months / 12);
  const m = months % 12;
  const parts = [];
  if (y > 0) parts.push(`${y} ${y === 1 ? 'yr' : 'yrs'}`);
  if (m > 0) parts.push(`${m} ${m === 1 ? 'mo' : 'mos'}`);
  return parts.join(' ');
};

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
  const Payment = paymentWord[0].toUpperCase() + paymentWord.slice(1);
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
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: '-0.6rem 0 0' }}>
            The {feeCap!.percent}% cap on this balance comes to {fmt(cap)}. Your bank may charge less, so check your contract.
          </p>
        )}
      </div>

      <div class="calc-results">
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>Option 1: Finish sooner, in {formatPeriod(r.shorterTerm.months)}</h3>
          <ResultCard
            currencyCode={currency.code}
            results={[
              { label: `Regular ${paymentWord}`, value: r.shorterTerm.payment },
              { label: 'Total interest left', value: r.shorterTerm.totalInterest },
              { label: 'Net saving after fee', value: r.shorterTerm.netSaving, highlight: true },
            ]}
          />
        </div>
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>Option 2: Pay less each month, in {formatPeriod(r.lowerPayment.months)}</h3>
          <ResultCard
            currencyCode={currency.code}
            results={[
              { label: `Regular ${paymentWord}`, value: r.lowerPayment.payment },
              { label: 'Total interest left', value: r.lowerPayment.totalInterest },
              { label: 'Net saving after fee', value: r.lowerPayment.netSaving, highlight: true },
            ]}
          />
        </div>
      </div>

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>
          {edge >= 1 ? `Finishing sooner saves ${fmt(edge)} more` : 'Both options save the same'}
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          With no prepayment, your {paymentWord} is {fmt(r.baselinePayment)} and you would pay {fmt(r.baselineInterest)}{' '}
          in interest. Option 1 cuts <strong>{formatPeriod(monthsSaved)}</strong> from your {termWord}. Option 2 lowers
          your {paymentWord} by <strong>{fmt(r.baselinePayment - r.lowerPayment.payment)}/month</strong> and leaves more
          cash free each month.
        </p>
      </div>
    </div>
  );
}
