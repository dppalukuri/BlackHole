import { useState } from 'preact/hooks';
import { capitalGainsTax, COST_INFLATION_INDEX, EQUITY_LTCG_EXEMPTION, type CapitalAsset } from '../../../lib/formulas/capital-gains';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import ChoiceButtons from '../ui/ChoiceButtons';

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

  const showSlab = asset !== 'equity';
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
        {showSlab && (
          <ChoiceButtons label="Your Income Tax Slab" value={slab} options={[0, 5, 10, 15, 20, 25, 30].map((v) => ({ value: v, label: `${v}%` }))} onChange={setSlab} />
        )}
        {asset === 'equity' && r.term === 'long' && (
          <SliderInput id="cg-exemption" label="Unused ₹1.25 Lakh Allowance This Year" value={exemption} min={0} max={EQUITY_LTCG_EXEMPTION} step={5000} prefix="₹" locale="en-IN" onChange={setExemption} />
        )}
        {showIndexOption && (
          <ChoiceButtons label="Are You a Resident Who Bought Before 23 July 2024?" value={oldProperty} options={[{ value: 'no', label: 'No' }, { value: 'yes', label: 'Yes' }]} onChange={setOldProperty} />
        )}
        {showIndexOption && oldProperty === 'yes' && (
          <div class="slider-group">
            <div class="slider-header"><label htmlFor="cg-fy">Year of Purchase</label></div>
            <select
              id="cg-fy"
              value={purchaseFy}
              onChange={(e) => setPurchaseFy(Number((e.target as HTMLSelectElement).value))}
              style={{ padding: '0.4rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.85rem', fontFamily: 'inherit' }}
            >
              {INDEXABLE_FYS.map((y) => <option value={y}>{fyLabel(y)} (CII {COST_INFLATION_INDEX[y]})</option>)}
            </select>
          </div>
        )}
      </div>

      <ResultCard
        currencyCode="INR"
        results={[
          { label: r.gain < 0 ? 'Capital loss' : 'Capital gain', value: Math.abs(r.gain) },
          { label: 'Taxable gain', value: r.taxableGain },
          { label: 'Tax with 4% cess', value: r.totalTax, highlight: true },
        ]}
      />

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>
          {r.gain <= 0 ? 'No tax is due on a loss' : `Your gain is ${termLabel}, at ${r.rate}%`}
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          {r.gain < 0 && 'You may be able to set this loss against other gains and carry it forward if you file on time. '}
          {r.exemptionUsed > 0 && <>The allowance covers {fmt(r.exemptionUsed)} of your gain. </>}
          {r.indexation && (
            <>
              With indexation, your cost rises to {fmt(r.indexation.indexedCost)}. Tax before cess is {fmt(r.indexation.taxAt20)} at
              20% with indexation, or {fmt(r.indexation.taxAt12Point5)} at 12.5% without. The calculator uses the lower one.{' '}
            </>
          )}
          After tax and costs, you keep <strong>{fmt(r.netProceeds)}</strong> from the sale.
        </p>
      </div>
    </div>
  );
}
