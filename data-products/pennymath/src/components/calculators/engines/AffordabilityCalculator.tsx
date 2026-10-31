import { useState } from 'preact/hooks';
import { maxAffordability, type LtvTier } from '../../../lib/formulas/affordability';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

interface AffordabilityCalculatorProps {
  currency: { code: string; symbol: string };
  paymentWord: string;
  /** Local name for the debt limit, such as "DBR" or "FOIR". */
  debtRatioName: string;
  maxTenureYears: number;
  incomeRange: { min: number; max: number; step: number };
  savingsRange: { min: number; max: number; step: number };
  /** Fixed tiers for markets with a rule table. Otherwise the user sets one LTV. */
  ltvTiers?: LtvTier[];
  defaults: {
    monthlyIncome: number;
    existingDebts: number;
    debtRatio: number;
    annualRate: number;
    tenureYears: number;
    savings: number;
    buyingCostPercent: number;
    ltvPercent?: number;
  };
}

export default function AffordabilityCalculator({
  currency,
  paymentWord,
  debtRatioName,
  maxTenureYears,
  incomeRange,
  savingsRange,
  ltvTiers,
  defaults,
}: AffordabilityCalculatorProps) {
  const [income, setIncome] = useState(defaults.monthlyIncome);
  const [debts, setDebts] = useState(defaults.existingDebts);
  const [debtRatio, setDebtRatio] = useState(defaults.debtRatio);
  const [rate, setRate] = useState(defaults.annualRate);
  const [years, setYears] = useState(defaults.tenureYears);
  const [savings, setSavings] = useState(defaults.savings);
  const [costs, setCosts] = useState(defaults.buyingCostPercent);
  const [ltv, setLtv] = useState(defaults.ltvPercent ?? 80);

  const r = maxAffordability({
    monthlyIncome: income,
    existingMonthlyDebts: debts,
    debtRatioPercent: debtRatio,
    annualRate: rate,
    tenureMonths: years * 12,
    savings,
    buyingCostPercent: costs,
    ltvTiers: ltvTiers ?? [{ maxPrice: Infinity, ltvPercent: ltv }],
  });

  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="af-income" label="Monthly Income" value={income} min={incomeRange.min} max={incomeRange.max} step={incomeRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setIncome} />
        <SliderInput id="af-debts" label="Existing Monthly Debt Payments" value={debts} min={0} max={incomeRange.max} step={incomeRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setDebts} />
        <SliderInput id="af-ratio" label={`Debt Limit as a Share of Income (${debtRatioName})`} value={debtRatio} min={20} max={70} step={1} suffix="%" onChange={setDebtRatio} />
        <SliderInput id="af-rate" label="Interest Rate (p.a.)" value={rate} min={1} max={16} step={0.05} suffix="%" onChange={setRate} />
        <SliderInput id="af-years" label="Loan Term" value={years} min={5} max={maxTenureYears} step={1} suffix=" Yr" onChange={setYears} />
        <SliderInput id="af-savings" label="Savings Available" value={savings} min={savingsRange.min} max={savingsRange.max} step={savingsRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setSavings} />
        <SliderInput id="af-costs" label="Buying Costs as a Share of Price" value={costs} min={0} max={15} step={0.25} suffix="%" onChange={setCosts} />
        {!ltvTiers && <SliderInput id="af-ltv" label="Maximum Loan-to-Value (LTV)" value={ltv} min={40} max={85} step={1} suffix="%" onChange={setLtv} />}
      </div>

      <ResultCard
        currencyCode={currency.code}
        results={[
          { label: 'Maximum loan', value: r.loan },
          { label: `Monthly ${paymentWord}`, value: r.payment },
          { label: 'Down payment', value: r.downPayment },
          { label: 'Buying costs', value: r.buyingCosts },
          { label: 'Maximum property price', value: r.maxPrice, highlight: true },
        ]}
      />

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>{r.limitedBy === 'income' ? 'Your income sets the limit' : 'Your savings set the limit'}</h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          {r.limitedBy === 'income' ? (
            <>
              After your existing debts, the {debtRatio}% limit leaves {fmt(r.maxPayment)}/month for this loan, which
              supports borrowing about {fmt(r.incomeLoanLimit)}. A longer term or fewer debts would raise that.
            </>
          ) : (
            <>
              Your income could support a loan of about {fmt(r.incomeLoanLimit)}, but at {r.ltvPercent}% LTV your savings
              cannot cover the rest of a pricier home and its costs. More savings would raise your budget.
            </>
          )}
        </p>
      </div>
    </div>
  );
}
