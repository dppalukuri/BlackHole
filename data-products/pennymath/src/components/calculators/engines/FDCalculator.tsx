import { useState } from 'preact/hooks';
import { lumpSumFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import GrowthChart from '../ui/GrowthChart';
import { localeForCurrency } from '../../../lib/formatters';

interface FDCalculatorProps {
  currency: { code: string; symbol: string };
}

export default function FDCalculator({ currency }: FDCalculatorProps) {
  const [principal, setPrincipal] = useState(100000);
  const [rate, setRate] = useState(7.1);
  const [years, setYears] = useState(5);

  // FDs compound quarterly in India
  const result = lumpSumFutureValue(principal, rate, years, 4);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="deposit-amount" label="Deposit Amount" value={principal} min={1000} max={10000000} step={1000} prefix={currency.symbol} scalable locale={localeForCurrency(currency.code)} onChange={setPrincipal} />
        <SliderInput id="interest-rate" label="Interest Rate (p.a.)" value={rate} min={1} max={12} step={0.1} suffix="%" onChange={setRate} />
        <SliderInput id="tenure" label="Tenure" value={years} min={1} max={10} step={1} suffix=" Yr" onChange={setYears} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'Maturity amount', value: result.totalValue, highlight: true },
            { label: 'Interest earned', value: result.estimatedReturns },
          ]}
        />
      </div>

      <div class="calc-below">
        <GrowthChart currencyCode={currency.code} rows={result.yearlyBreakdown} start={principal} title="How your deposit grows" valueLabel="Deposit value" investedLabel="Amount deposited" />
      </div>
    </div>
  );
}
