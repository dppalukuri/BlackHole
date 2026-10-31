import { useState } from 'preact/hooks';
import { compareRemittance } from '../../../lib/formulas/remittance';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

const inr = (n: number) => formatCurrency(n, 'INR');
const aed = (n: number) => formatCurrency(n, 'AED');

interface Props {
  defaultMidRate: number;
}

export default function RemittanceCalculator({ defaultMidRate }: Props) {
  const [amount, setAmount] = useState(5000);
  const [midRate, setMidRate] = useState(defaultMidRate);
  const [rates, setRates] = useState([26.05, 25.95, 25.8]);
  const [fees, setFees] = useState([22, 10, 0]);

  const update = (list: number[], i: number, v: number) => list.map((x, j) => (j === i ? v : x));
  const quotes = compareRemittance(
    amount,
    midRate,
    rates.map((rate, i) => ({ name: `Provider ${'ABC'[i]}`, rate, fee: fees[i] }))
  );
  const best = quotes.find((q) => q.isBest)!;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="rm-amount" label="Amount to Send" value={amount} min={100} max={100000} step={100} prefix="AED " scalable locale="en-AE" onChange={setAmount} />
        <SliderInput id="rm-mid" label="Today's Mid-Market Rate (₹ per AED)" value={midRate} min={15} max={40} step={0.01} onChange={setMidRate} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: `Best value: ${best.name} delivers`, value: best.received, highlight: true },
            { label: 'You pay', value: aed(best.totalPaid) },
            { label: 'Effective rate, fee included', value: `₹${best.effectiveRate.toFixed(4)}` },
            { label: 'Hidden cost against the mid-market rate', value: `${inr(best.costInr)} (${best.costPercent.toFixed(2)}%)` },
          ]}
        />
      </div>

      <div class="calc-below offer-grid">
        {quotes.map((q, i) => (
          <div class={`offer ${q.isBest ? 'is-best' : ''}`}>
            <h3>{q.name} {q.isBest && <span class="tag">Best value</span>}</h3>
            <SliderInput id={`rm-rate-${i}`} label="Rate Offered (₹ per AED)" value={rates[i]} min={15} max={40} step={0.01} onChange={(v) => setRates(update(rates, i, v))} />
            <SliderInput id={`rm-fee-${i}`} label="Fee with VAT" value={fees[i]} min={0} max={200} step={1} prefix="AED " onChange={(v) => setFees(update(fees, i, v))} />
            <div class="offer-line"><span>Rupees delivered</span><b>{inr(q.received)}</b></div>
            <div class="offer-line"><span>Hidden cost</span><b>{inr(q.costInr)} ({q.costPercent.toFixed(2)}%)</b></div>
          </div>
        ))}
      </div>
    </div>
  );
}
