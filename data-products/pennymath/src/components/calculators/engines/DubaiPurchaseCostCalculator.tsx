import { useState } from 'preact/hooks';
import { dubaiPurchaseCosts } from '../../../lib/formulas/dubai-purchase-costs';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

const fmt = (n: number) => formatCurrency(n, 'AED');

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
        <SliderInput id="dc-price" label="Property Price" value={price} min={200000} max={20000000} step={50000} prefix="AED " scalable locale="en-AE" onChange={setPrice} />
        <ChoiceButtons label="How Are You Paying?" value={financing} options={[{ value: 'mortgage', label: 'With a mortgage' }, { value: 'cash', label: 'Cash' }]} onChange={setFinancing} />
        {hasLoan && <SliderInput id="dc-loan" label="Mortgage as a Share of Price" value={loanPercent} min={10} max={85} step={1} suffix="%" onChange={setLoanPercent} />}
        <ChoiceButtons label="Using a Real Estate Agent?" value={agent} options={[{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }]} onChange={setAgent} />
        {agent === 'yes' && <SliderInput id="dc-agent" label="Agent Commission" value={agentPercent} min={0} max={5} step={0.25} suffix="%" onChange={setAgentPercent} />}
        {hasLoan && <SliderInput id="dc-bank" label="Bank Processing Fee" value={bankFeePercent} min={0} max={2} step={0.05} suffix="%" onChange={setBankFeePercent} />}
        {hasLoan && <SliderInput id="dc-val" label="Valuation Fee" value={valuationFee} min={0} max={10000} step={100} prefix="AED " locale="en-AE" onChange={setValuationFee} />}
        <SliderInput id="dc-other" label="Other Costs, Such as a Developer NOC" value={otherCosts} min={0} max={50000} step={250} prefix="AED " scalable locale="en-AE" onChange={setOtherCosts} />
      </div>

      <ResultCard
        currencyCode="AED"
        results={[
          { label: 'Down payment', value: r.downPayment },
          { label: `Fees and costs (${r.costsPercentOfPrice.toFixed(1)}% of price)`, value: r.totalCosts },
          { label: 'Total cash needed', value: r.cashNeeded, highlight: true },
        ]}
      />

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>Cost breakdown</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <tbody>
            {r.costs.map((c) => (
              <tr style={{ borderTop: '1px solid var(--color-border)' }}>
                <td style={{ padding: '0.4rem 0' }}>{c.label}</td>
                <td style={{ padding: '0.4rem 0', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{fmt(c.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
