import { useState } from 'preact/hooks';
import { lumpSumFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

export default function CompoundInterestCalculator() {
  const [principal, setPrincipal] = useState(10000);
  const [rate, setRate] = useState(7);
  const [years, setYears] = useState(10);
  const [frequency, setFrequency] = useState(12); // monthly

  const result = lumpSumFutureValue(principal, rate, years, frequency);

  const freqOptions = [
    { label: 'Annually', value: 1 },
    { label: 'Semi-annually', value: 2 },
    { label: 'Quarterly', value: 4 },
    { label: 'Monthly', value: 12 },
    { label: 'Daily', value: 365 },
  ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="principal"
          label="Initial Investment"
          value={principal}
          min={100}
          max={1000000}
          step={100}
          prefix="$"
          onChange={setPrincipal}
        />
        <SliderInput
          id="interest-rate"
          label="Annual Interest Rate"
          value={rate}
          min={0.1}
          max={20}
          step={0.1}
          suffix="%"
          onChange={setRate}
        />
        <SliderInput
          id="time-period"
          label="Time Period"
          value={years}
          min={1}
          max={50}
          step={1}
          suffix=" Yr"
          onChange={setYears}
        />

        <div class="slider-group">
          <div class="slider-header">
            <label>Compounding Frequency</label>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.25rem;">
            {freqOptions.map((opt) => (
              <button
                onClick={() => setFrequency(opt.value)}
                style={{
                  padding: '0.4rem 0.9rem',
                  borderRadius: '6px',
                  border: `2px solid ${frequency === opt.value ? '#6366f1' : '#e2e8f0'}`,
                  background: frequency === opt.value ? '#6366f1' : 'white',
                  color: frequency === opt.value ? 'white' : '#64748b',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode="USD"
          results={[
            { label: 'Initial Investment', value: result.investedAmount },
            { label: 'Total Interest', value: result.estimatedReturns },
            { label: 'Final Amount', value: result.totalValue, highlight: true },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Principal', value: result.investedAmount, color: '#6366f1' },
            { label: 'Interest', value: result.estimatedReturns, color: '#22c55e' },
          ]}
        />
      </div>
    </div>
  );
}
