import { useState } from 'preact/hooks';
import { dubaiPurchaseCosts } from '../../../lib/formulas/dubai-purchase-costs';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

export default function DubaiPurchaseCostCalculator() {
  const [price, setPrice] = useState(1500000);
  const [financing, setFinancing] = useState<'mortgage' | 'cash'>('mortgage');
  const [loanPercent, setLoanPercent] = useState(80);
  const [agent, setAgent] = useState<'yes' | 'no'>('yes');
  const [agentPercent, setAgentPercent] = useState(2);
  const [bankFeePercent, setBankFeePercent] = useState(1);
  const [valuationFee, setValuationFee] = useState(3000);
  const [otherCosts, setOtherCosts] = useState(0);

  const hasLoan = financing === 'mortgage';
  const r = dubaiPurchaseCosts({
    price,
    loanPercent: hasLoan ? loanPercent : 0,
    useAgent: agent === 'yes',
    agentPercent,
    bankFeePercent,
    valuationFee,
    otherCosts,
  });

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <div class="span-all">
          <SliderInput id="dc-price" label="Property Price" value={price} min={200000} max={20000000} step={50000} prefix="AED " scalable locale="en-AE" onChange={setPrice} />
        </div>
        <ChoiceButtons label="How Are You Paying?" value={financing} options={[{ value: 'mortgage', label: 'With a mortgage' }, { value: 'cash', label: 'Cash' }]} onChange={setFinancing} />
        {hasLoan && <SliderInput id="dc-loan" label="Mortgage as a Share of Price" value={loanPercent} min={10} max={85} step={1} suffix="%" onChange={setLoanPercent} />}
        {hasLoan && <SliderInput id="dc-bank" label="Bank Processing Fee" value={bankFeePercent} min={0} max={2} step={0.05} suffix="%" onChange={setBankFeePercent} />}
        {hasLoan && <SliderInput id="dc-val" label="Valuation Fee" value={valuationFee} min={0} max={10000} step={100} prefix="AED " locale="en-AE" onChange={setValuationFee} />}
        <SliderInput id="dc-other" label="Other Costs, Such as a Developer NOC" value={otherCosts} min={0} max={50000} step={250} prefix="AED " scalable locale="en-AE" onChange={setOtherCosts} />
        <ChoiceButtons label="Using a Real Estate Agent?" value={agent} options={[{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]} onChange={setAgent} />
        {agent === 'yes' && <SliderInput id="dc-agent" label="Agent Commission" value={agentPercent} min={0} max={5} step={0.25} suffix="%" onChange={setAgentPercent} />}
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="AED"
          results={[
            { label: 'Total cash needed', value: r.cashNeeded, highlight: true },
            { label: 'Down payment', value: r.downPayment },
            { label: `All fees and costs`, note: `${r.costsPercentOfPrice.toFixed(1)}% of the price, itemised below`, value: r.totalCosts },
            ...r.costs.map((c) => ({ label: c.label, value: c.amount })),
          ]}
        />
      </div>
    </div>
  );
}
