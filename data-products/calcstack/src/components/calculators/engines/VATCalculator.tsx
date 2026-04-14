import { useState } from 'preact/hooks';
import { calculateVAT } from '../../../lib/formulas/flat-rate';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';

export default function VATCalculator() {
  const [amount, setAmount] = useState(1000);
  const [inclusive, setInclusive] = useState(false);

  const vatRate = 5; // UAE standard VAT rate
  const result = calculateVAT(amount, vatRate, inclusive);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="amount"
          label={inclusive ? 'Total Amount (VAT inclusive)' : 'Amount (before VAT)'}
          value={amount}
          min={1}
          max={1000000}
          step={100}
          prefix="AED "
          onChange={setAmount}
        />

        <div class="slider-group">
          <div class="slider-header">
            <label>Calculation Mode</label>
          </div>
          <div style="display: flex; gap: 1rem; margin-top: 0.25rem;">
            <button
              onClick={() => setInclusive(false)}
              style={{
                padding: '0.5rem 1.25rem',
                borderRadius: '8px',
                border: `2px solid ${!inclusive ? '#6366f1' : '#e2e8f0'}`,
                background: !inclusive ? '#6366f1' : 'white',
                color: !inclusive ? 'white' : '#64748b',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
              }}
            >
              Add VAT
            </button>
            <button
              onClick={() => setInclusive(true)}
              style={{
                padding: '0.5rem 1.25rem',
                borderRadius: '8px',
                border: `2px solid ${inclusive ? '#6366f1' : '#e2e8f0'}`,
                background: inclusive ? '#6366f1' : 'white',
                color: inclusive ? 'white' : '#64748b',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
              }}
            >
              Extract VAT
            </button>
          </div>
        </div>
      </div>

      <div class="calc-results" style="grid-template-columns: 1fr;">
        <div class="result-card">
          <div class="result-item">
            <span class="result-label">Net Amount (excl. VAT)</span>
            <span class="result-value">{formatCurrency(result.netAmount, 'AED')}</span>
          </div>
          <div class="result-item">
            <span class="result-label">VAT Amount (5%)</span>
            <span class="result-value">{formatCurrency(result.vatAmount, 'AED')}</span>
          </div>
          <div class="result-item result-highlight">
            <span class="result-label">Total Amount (incl. VAT)</span>
            <span class="result-value">{formatCurrency(result.totalAmount, 'AED')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
