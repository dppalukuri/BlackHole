import { useState } from 'preact/hooks';
import { uaeGratuity } from '../../../lib/formulas/flat-rate';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

interface UAEGratuityCalculatorProps {
  currency: { code: string; symbol: string };
}

export default function UAEGratuityCalculator({ currency }: UAEGratuityCalculatorProps) {
  const [salary, setSalary] = useState(10000);
  const [years, setYears] = useState(5);

  const result = uaeGratuity(salary, years);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="basic-salary"
          label="Basic Monthly Salary"
          value={salary}
          min={1000}
          max={100000}
          step={500}
          prefix={currency.symbol}
          onChange={setSalary}
        />
        <SliderInput
          id="years-of-service"
          label="Years of Service"
          value={years}
          min={0}
          max={30}
          step={0.5}
          suffix=" Yr"
          onChange={setYears}
        />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'End-of-Service Gratuity', value: result.gratuityAmount, highlight: true },
          ]}
        />

        <div class="gratuity-breakdown">
          <h3>How it's calculated</h3>
          {years < 1 ? (
            <p class="gratuity-note">You must complete at least 1 year of service to be eligible for gratuity.</p>
          ) : (
            <div class="breakdown-table">
              {years <= 5 ? (
                <p>
                  Daily wage ({currency.symbol}{(salary / 30).toFixed(0)}) x 21 days x {years} years
                  = <strong>{currency.symbol}{result.gratuityAmount.toLocaleString()}</strong>
                </p>
              ) : (
                <>
                  <p>First 5 years: Daily wage ({currency.symbol}{(salary / 30).toFixed(0)}) x 21 days x 5 = {currency.symbol}{((salary / 30) * 21 * 5).toLocaleString()}</p>
                  <p>Remaining {(years - 5).toFixed(1)} years: Daily wage ({currency.symbol}{(salary / 30).toFixed(0)}) x 30 days x {(years - 5).toFixed(1)} = {currency.symbol}{((salary / 30) * 30 * (years - 5)).toLocaleString()}</p>
                  <p><strong>Total: {currency.symbol}{result.gratuityAmount.toLocaleString()}</strong></p>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
