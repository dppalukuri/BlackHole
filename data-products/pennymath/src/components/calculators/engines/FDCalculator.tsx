import { useState } from 'preact/hooks';
import { lumpSumFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

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
        <SliderInput
          id="deposit-amount"
          label="Deposit Amount"
          value={principal}
          min={1000}
          max={10000000}
          step={1000}
          prefix={currency.symbol}
          onChange={setPrincipal}
        />
        <SliderInput
          id="interest-rate"
          label="Interest Rate (p.a.)"
          value={rate}
          min={1}
          max={12}
          step={0.1}
          suffix="%"
          onChange={setRate}
        />
        <SliderInput
          id="tenure"
          label="Tenure"
          value={years}
          min={1}
          max={10}
          step={1}
          suffix=" Yr"
          onChange={setYears}
        />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'Deposit Amount', value: result.investedAmount },
            { label: 'Interest Earned', value: result.estimatedReturns },
            { label: 'Maturity Amount', value: result.totalValue, highlight: true },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Deposit', value: result.investedAmount, color: '#6366f1' },
            { label: 'Interest', value: result.estimatedReturns, color: '#f59e0b' },
          ]}
        />
      </div>
    </div>
  );
}
