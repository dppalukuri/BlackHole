import { useState } from 'preact/hooks';
import { lumpSumFutureValue } from '../../../lib/formulas/compound-growth';
import { localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import GrowthChart from '../ui/GrowthChart';
import ChoiceButtons from '../ui/ChoiceButtons';

interface CompoundInterestCalculatorProps {
  currency?: { code: string; symbol: string };
}

const FREQUENCIES = [
  { label: 'Annually', value: 1 },
  { label: 'Semi-annually', value: 2 },
  { label: 'Quarterly', value: 4 },
  { label: 'Monthly', value: 12 },
  { label: 'Daily', value: 365 },
];

export default function CompoundInterestCalculator({ currency = { code: 'USD', symbol: '$' } }: CompoundInterestCalculatorProps) {
  const [principal, setPrincipal] = useState(10000);
  const [rate, setRate] = useState(7);
  const [years, setYears] = useState(10);
  const [frequency, setFrequency] = useState(12);

  const result = lumpSumFutureValue(principal, rate, years, frequency);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="principal" label="Initial Amount" value={principal} min={100} max={1000000} step={100} prefix={currency.symbol} scalable locale={localeForCurrency(currency.code)} onChange={setPrincipal} />
        <SliderInput id="interest-rate" label="Annual Interest Rate" value={rate} min={0.1} max={20} step={0.1} suffix="%" onChange={setRate} />
        <SliderInput id="time-period" label="Time Period" value={years} min={1} max={50} step={1} suffix=" Yr" onChange={setYears} />
        <ChoiceButtons label="Compounding Frequency" value={frequency} options={FREQUENCIES} onChange={setFrequency} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: `Value after ${years} ${years === 1 ? 'year' : 'years'}`, value: result.totalValue, highlight: true },
            { label: 'Total interest', value: result.estimatedReturns },
          ]}
        />
      </div>

      <div class="calc-below">
        <GrowthChart currencyCode={currency.code} rows={result.yearlyBreakdown} start={principal} valueLabel="With interest" investedLabel="Amount paid in" />
      </div>
    </div>
  );
}
