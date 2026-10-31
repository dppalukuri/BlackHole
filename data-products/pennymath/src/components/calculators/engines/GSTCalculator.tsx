import { useState } from 'preact/hooks';
import { gstBreakdown } from '../../../lib/formulas/flat-rate';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

const RATES = [0.25, 3, 5, 12, 18, 28, 40];

export default function GSTCalculator() {
  const [amount, setAmount] = useState(10000);
  const [mode, setMode] = useState<'add' | 'remove'>('add');
  const [rate, setRate] = useState(18);
  const [supply, setSupply] = useState<'intra' | 'inter'>('intra');

  const removing = mode === 'remove';
  const r = gstBreakdown(amount, rate, removing, supply === 'inter');
  const tax = supply === 'inter'
    ? [{ label: `IGST at ${rate}%`, value: r.igst }]
    : [
        { label: `CGST at ${rate / 2}%`, value: r.cgst },
        { label: `SGST at ${rate / 2}%`, value: r.sgst },
      ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <div class="span-all">
          <SliderInput id="gst-amount" label={removing ? 'Amount Including GST' : 'Amount Before GST'} value={amount} min={1} max={1000000} step={100} prefix="₹" scalable locale="en-IN" onChange={setAmount} />
        </div>
        <ChoiceButtons label="What Do You Want to Do?" value={mode} options={[{ value: 'add', label: 'Add GST' }, { value: 'remove', label: 'Remove GST' }]} onChange={setMode} />
        <ChoiceButtons
          label="GST Rate"
          value={rate}
          options={RATES.map((v) => ({ value: v, label: v === 12 || v === 28 ? `${v}% (older bills)` : `${v}%` }))}
          onChange={setRate}
        />
        <ChoiceButtons label="Where Is the Supply?" value={supply} options={[{ value: 'intra', label: 'Within a state' }, { value: 'inter', label: 'Between states' }]} onChange={setSupply} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            removing
              ? { label: 'Amount before GST', value: r.netAmount, highlight: true }
              : { label: 'Total including GST', value: r.totalAmount, highlight: true },
            ...tax,
          ]}
        />
      </div>
    </div>
  );
}
