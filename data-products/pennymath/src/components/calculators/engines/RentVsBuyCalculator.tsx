import { useState } from 'preact/hooks';
import { compareRentVsBuy } from '../../../lib/formulas/rent-vs-buy';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';

interface RentVsBuyCalculatorProps {
  currency: { code: string; symbol: string };
  paymentWord: string;
  priceRange: { min: number; max: number; step: number };
  rentRange: { min: number; max: number; step: number };
  maxTenureYears: number;
  defaults: {
    price: number;
    downPercent: number;
    annualRate: number;
    tenureYears: number;
    buyingCostPercent: number;
    sellingCostPercent: number;
    ownershipCostPercent: number;
    appreciationPercent: number;
    monthlyRent: number;
    rentGrowthPercent: number;
    investmentReturnPercent: number;
    years: number;
  };
}

export default function RentVsBuyCalculator({ currency, paymentWord, priceRange, rentRange, maxTenureYears, defaults: d }: RentVsBuyCalculatorProps) {
  const [price, setPrice] = useState(d.price);
  const [downPercent, setDownPercent] = useState(d.downPercent);
  const [annualRate, setAnnualRate] = useState(d.annualRate);
  const [tenureYears, setTenureYears] = useState(d.tenureYears);
  const [buyingCostPercent, setBuyingCost] = useState(d.buyingCostPercent);
  const [sellingCostPercent, setSellingCost] = useState(d.sellingCostPercent);
  const [ownershipCostPercent, setOwnershipCost] = useState(d.ownershipCostPercent);
  const [appreciationPercent, setAppreciation] = useState(d.appreciationPercent);
  const [monthlyRent, setRent] = useState(d.monthlyRent);
  const [rentGrowthPercent, setRentGrowth] = useState(d.rentGrowthPercent);
  const [investmentReturnPercent, setReturn] = useState(d.investmentReturnPercent);
  const [years, setYears] = useState(d.years);

  const r = compareRentVsBuy({
    price, downPercent, annualRate, tenureMonths: tenureYears * 12, buyingCostPercent, sellingCostPercent,
    ownershipCostPercent, appreciationPercent, monthlyRent, rentGrowthPercent, investmentReturnPercent, years,
  });

  const fmt = (n: number) => formatCurrency(n, currency.code);
  const locale = localeForCurrency(currency.code);
  const buyingWins = r.advantage > 0;
  const pctSlider = (id: string, label: string, value: number, max: number, step: number, onChange: (v: number) => void) => (
    <SliderInput id={id} label={label} value={value} min={0} max={max} step={step} suffix="%" onChange={onChange} />
  );

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="rb-price" label="Property Price" value={price} min={priceRange.min} max={priceRange.max} step={priceRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setPrice} />
        <SliderInput id="rb-rent" label="Monthly Rent for a Similar Home" value={monthlyRent} min={rentRange.min} max={rentRange.max} step={rentRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setRent} />
        <SliderInput id="rb-years" label="How Long You Plan to Stay" value={years} min={1} max={30} step={1} suffix=" Yr" onChange={setYears} />
        {pctSlider('rb-down', 'Down Payment', downPercent, 100, 1, setDownPercent)}
        {pctSlider('rb-rate', 'Loan Interest Rate (p.a.)', annualRate, 16, 0.05, setAnnualRate)}
        <SliderInput id="rb-tenure" label="Loan Term" value={tenureYears} min={5} max={maxTenureYears} step={1} suffix=" Yr" onChange={setTenureYears} />
        {pctSlider('rb-buying', 'Buying Costs (share of price)', buyingCostPercent, 15, 0.25, setBuyingCost)}
        {pctSlider('rb-selling', 'Selling Costs (share of sale price)', sellingCostPercent, 10, 0.25, setSellingCost)}
        {pctSlider('rb-owning', 'Yearly Ownership Costs (share of price)', ownershipCostPercent, 5, 0.1, setOwnershipCost)}
        {pctSlider('rb-growth', 'Yearly Home Price Growth', appreciationPercent, 15, 0.25, setAppreciation)}
        {pctSlider('rb-rent-growth', 'Yearly Rent Growth', rentGrowthPercent, 15, 0.25, setRentGrowth)}
        {pctSlider('rb-return', 'Yearly Return on Investments', investmentReturnPercent, 20, 0.25, setReturn)}
      </div>

      <div class="calc-results">
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>If you buy</h3>
          <ResultCard currencyCode={currency.code} results={[
            { label: 'Cash needed upfront', value: r.upfrontCash },
            { label: `Monthly ${paymentWord}`, value: r.monthlyLoanPayment },
            { label: `Net worth after ${years} ${years === 1 ? 'year' : 'years'}`, value: r.buyerNetWorth, highlight: true },
          ]} />
        </div>
        <div>
          <h3 style={{ marginTop: 0, fontSize: '0.9rem' }}>If you rent and invest</h3>
          <ResultCard currencyCode={currency.code} results={[
            { label: 'Cash invested upfront', value: r.upfrontCash },
            { label: 'Monthly rent today', value: monthlyRent },
            { label: `Net worth after ${years} ${years === 1 ? 'year' : 'years'}`, value: r.renterNetWorth, highlight: true },
          ]} />
        </div>
      </div>

      <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
        <h3 style={{ marginTop: 0 }}>{buyingWins ? 'Buying' : 'Renting'} leaves you {fmt(Math.abs(r.advantage))} better off</h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
          {r.breakEvenYear !== null
            ? <>On these assumptions, buying moves ahead for good in <strong>year {r.breakEvenYear}</strong>. If you might move before then, renting is likely to work out better.</>
            : <>On these assumptions, buying does not catch up within {years} {years === 1 ? 'year' : 'years'}. Try a longer stay or different growth rates to see what would change that.</>}
        </p>
      </div>

      <details style={{ marginTop: '1.25rem' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>View Year-by-Year Breakdown</summary>
        <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ textAlign: 'right', color: 'var(--color-text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '0.5rem 0.6rem', fontWeight: 600 }}>Year</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Buyer net worth</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Renter net worth</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Ahead</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: 'var(--font-mono)' }}>
              {r.yearly.map((y) => (
                <tr style={{ borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
                  <td style={{ textAlign: 'left', padding: '0.45rem 0.6rem', fontWeight: 600 }}>{y.year}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(y.buyerNetWorth)}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(y.renterNetWorth)}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{y.buyerNetWorth > y.renterNetWorth ? 'Buyer' : 'Renter'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
