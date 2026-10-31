import { useState } from 'preact/hooks';
import { capitalGainsTax, COST_INFLATION_INDEX, EQUITY_LTCG_EXEMPTION, type CapitalAsset } from '../../../lib/formulas/capital-gains';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';
import Verdict from '../ui/Verdict';

const fmt = (n: number) => formatCurrency(n, 'INR');
const FY_STARTS = Object.keys(COST_INFLATION_INDEX).map(Number);
const LATEST_FY = FY_STARTS[FY_STARTS.length - 1];
// The indexed option needs a purchase before 23 July 2024, which falls in FY 2024-25.
const INDEXABLE_FYS = FY_STARTS.filter((y) => y <= 2024);
const fyLabel = (y: number) => `FY ${y}-${String((y + 1) % 100).padStart(2, '0')}`;

export default function CapitalGainsCalculator() {
  const [asset, setAsset] = useState<CapitalAsset>('equity');
  const [purchase, setPurchase] = useState(500000);
  const [sale, setSale] = useState(800000);
  const [expenses, setExpenses] = useState(0);
  const [months, setMonths] = useState(24);
  const [slab, setSlab] = useState(30);
  const [exemption, setExemption] = useState(EQUITY_LTCG_EXEMPTION);
  const [oldProperty, setOldProperty] = useState<'yes' | 'no'>('no');
  const [purchaseFy, setPurchaseFy] = useState(2015);

  const r = capitalGainsTax({
    asset,
    purchaseValue: purchase,
    saleValue: sale,
    expenses,
    holdingMonths: months,
    slabRate: slab,
    exemptionAvailable: exemption,
    indexationEligible: oldProperty === 'yes',
    purchaseFyStart: purchaseFy,
    saleFyStart: LATEST_FY,
  });

  const showIndexOption = asset === 'property' && r.term === 'long';
  const termLabel = asset === 'debt-fund' ? 'taxed at your slab rate' : r.term === 'long' ? 'long-term' : 'short-term';

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <ChoiceButtons
          label="What Did You Sell?"
          value={asset}
          options={[
            { value: 'equity', label: 'Listed shares or equity funds' },
            { value: 'debt-fund', label: 'Debt funds bought from 1 Apr 2023' },
            { value: 'property', label: 'Property' },
            { value: 'other', label: 'Gold or other assets' },
          ]}
          onChange={setAsset}
        />
        <SliderInput id="cg-purchase" label="Purchase Value" value={purchase} min={1000} max={50000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setPurchase} />
        <SliderInput id="cg-sale" label="Sale Value" value={sale} min={1000} max={50000000} step={10000} prefix="₹" scalable locale="en-IN" onChange={setSale} />
        <SliderInput id="cg-expenses" label="Sale Costs and Improvements" value={expenses} min={0} max={5000000} step={5000} prefix="₹" scalable locale="en-IN" onChange={setExpenses} />
        <SliderInput id="cg-months" label="Holding Period" value={months} min={1} max={360} step={1} suffix=" mo" onChange={setMonths} />
        {asset !== 'equity' && (
          <ChoiceButtons label="Your Income Tax Slab" value={slab} options={[0, 5, 10, 15, 20, 25, 30].map((v) => ({ value: v, label: `${v}%` }))} onChange={setSlab} />
        )}
        {asset === 'equity' && r.term === 'long' && (
          <div class="span-all">
            <SliderInput id="cg-exemption" label="Unused ₹1.25 Lakh Allowance This Year" value={exemption} min={0} max={EQUITY_LTCG_EXEMPTION} step={5000} prefix="₹" locale="en-IN" onChange={setExemption} />
          </div>
        )}
        {showIndexOption && (
          <ChoiceButtons label="Are You a Resident Who Bought Before 23 July 2024?" value={oldProperty} options={[{ value: 'no', label: 'No' }, { value: 'yes', label: 'Yes' }]} onChange={setOldProperty} />
        )}
        {showIndexOption && oldProperty === 'yes' && (
          <div class="span-all">
            <label class="field-label" htmlFor="cg-fy">Year of Purchase</label>
            <select id="cg-fy" class="calc-select" value={purchaseFy} onChange={(e) => setPurchaseFy(Number((e.target as HTMLSelectElement).value))}>
              {INDEXABLE_FYS.map((y) => <option value={y}>{fyLabel(y)} (CII {COST_INFLATION_INDEX[y]})</option>)}
            </select>
          </div>
        )}
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Tax with 4% cess', value: r.totalTax, highlight: true },
            { label: r.gain < 0 ? 'Capital loss' : 'Capital gain', value: Math.abs(r.gain) },
            { label: 'Taxable gain', note: r.exemptionUsed > 0 ? `After ${fmt(r.exemptionUsed)} of allowance` : undefined, value: r.taxableGain },
            { label: 'What you keep from the sale', value: r.netProceeds },
          ]}
        />
        <Verdict title={r.gain <= 0 ? 'No tax is due on a loss' : `Your gain is ${termLabel}, at ${r.rate}%`}>
          {r.gain < 0 && 'You may be able to set this loss against other gains and carry it forward if you file on time. '}
          {r.indexation && (
            <>With indexation, your cost rises to {fmt(r.indexation.indexedCost)}. Tax before cess is {fmt(r.indexation.taxAt20)} at 20% with indexation, or {fmt(r.indexation.taxAt12Point5)} at 12.5% without. The calculator uses the lower one.</>
          )}
        </Verdict>
      </div>
    </div>
  );
}
