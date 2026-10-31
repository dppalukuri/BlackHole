import { useState } from 'preact/hooks';
import { lumpSumFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import GrowthChart from '../ui/GrowthChart';
import { localeForCurrency } from '../../../lib/formatters';

interface LumpSumCalculatorProps {
  currency: { code: string; symbol: string };
  defaults?: {
    principal?: number;
    expectedReturn?: number;
    timePeriod?: number;
  };
}

export default function LumpSumCalculator({ currency, defaults }: LumpSumCalculatorProps) {
  const [principal, setPrincipal] = useState(defaults?.principal ?? 100000);
  const [rate, setRate] = useState(defaults?.expectedReturn ?? 12);
  const [years, setYears] = useState(defaults?.timePeriod ?? 10);

  const result = lumpSumFutureValue(principal, rate, years);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="principal" label="Investment Amount" value={principal} min={1000} max={10000000} step={1000} prefix={currency.symbol} scalable locale={localeForCurrency(currency.code)} onChange={setPrincipal} />
        <SliderInput id="expected-return" label="Expected Return Rate (p.a.)" value={rate} min={1} max={30} step={0.5} suffix="%" onChange={setRate} />
        <SliderInput id="time-period" label="Time Period" value={years} min={1} max={40} step={1} suffix=" Yr" onChange={setYears} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: `Value after ${years} ${years === 1 ? 'year' : 'years'}`, value: result.totalValue, highlight: true },
            { label: 'Estimated returns', value: result.estimatedReturns },
          ]}
        />
      </div>

      <div class="calc-below">
        <GrowthChart currencyCode={currency.code} rows={result.yearlyBreakdown} start={principal} />
      </div>
    </div>
  );
}
