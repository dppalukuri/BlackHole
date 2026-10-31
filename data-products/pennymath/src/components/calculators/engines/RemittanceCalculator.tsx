import { useState } from 'preact/hooks';
import { compareRemittance } from '../../../lib/formulas/remittance';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';

const inr = (n: number) => formatCurrency(n, 'INR');
const aed = (n: number) => formatCurrency(n, 'AED');

interface Props {
  defaultMidRate: number;
}

export default function RemittanceCalculator({ defaultMidRate }: Props) {
  const [amount, setAmount] = useState(5000);
  const [midRate, setMidRate] = useState(defaultMidRate);
  const [rates, setRates] = useState([defaultMidRate - 0.15, defaultMidRate - 0.25, defaultMidRate - 0.4]);
  const [fees, setFees] = useState([22, 10, 0]);

  const update = (list: number[], i: number, v: number) => list.map((x, j) => (j === i ? v : x));
  const quotes = compareRemittance(
    amount,
    midRate,
    rates.map((rate, i) => ({ name: `Provider ${'ABC'[i]}`, rate, fee: fees[i] }))
  );

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="rm-amount" label="Amount to Send" value={amount} min={100} max={100000} step={100} prefix="AED " scalable locale="en-AE" onChange={setAmount} />
        <SliderInput id="rm-mid" label="Today's Mid-Market Rate (₹ per AED)" value={midRate} min={15} max={40} step={0.01} onChange={setMidRate} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        {quotes.map((q, i) => (
          <div style={{ border: `2px solid ${q.isBest ? '#22c55e' : '#e2e8f0'}`, borderRadius: '12px', padding: '1rem', background: q.isBest ? '#f0fdf4' : '#fff' }}>
            <h3 style={{ marginTop: 0, fontSize: '0.95rem' }}>
              {q.name}{q.isBest && <span style={{ color: '#16a34a' }}> · Best value</span>}
            </h3>
            <div class="calc-inputs" style={{ marginBottom: '0.75rem' }}>
              <SliderInput id={`rm-rate-${i}`} label="Rate Offered (₹ per AED)" value={rates[i]} min={15} max={40} step={0.01} onChange={(v) => setRates(update(rates, i, v))} />
              <SliderInput id={`rm-fee-${i}`} label="Fee with VAT" value={fees[i]} min={0} max={200} step={1} prefix="AED " onChange={(v) => setFees(update(fees, i, v))} />
            </div>
            <p style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.25rem' }}>{inr(q.received)}</p>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: 0 }}>
              You pay {aed(q.totalPaid)}. Effective rate: ₹{q.effectiveRate.toFixed(4)}. Hidden cost: {inr(q.costInr)} ({q.costPercent.toFixed(2)}%).
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
