import { useState } from 'preact/hooks';
import { calculateVAT } from '../../../lib/formulas/flat-rate';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

const VAT_RATE = 5; // UAE standard VAT rate

export default function VATCalculator() {
  const [amount, setAmount] = useState(1000);
  const [mode, setMode] = useState<'add' | 'extract'>('add');

  const inclusive = mode === 'extract';
  const result = calculateVAT(amount, VAT_RATE, inclusive);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="amount" label={inclusive ? 'Total Including VAT' : 'Amount Before VAT'} value={amount} min={1} max={1000000} step={100} prefix="AED " scalable locale="en-AE" onChange={setAmount} />
        <ChoiceButtons label="What Do You Want to Do?" value={mode} options={[{ value: 'add', label: 'Add VAT' }, { value: 'extract', label: 'Extract VAT' }]} onChange={setMode} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="AED"
          results={[
            inclusive
              ? { label: 'Amount before VAT', value: result.netAmount, highlight: true }
              : { label: 'Total including VAT', value: result.totalAmount, highlight: true },
            { label: `VAT at ${VAT_RATE}%`, value: result.vatAmount },
          ]}
        />
      </div>
    </div>
  );
}
