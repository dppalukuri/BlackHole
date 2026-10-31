import { useState } from 'preact/hooks';
import { compareRentVsBuy } from '../../../lib/formulas/rent-vs-buy';
import { formatCompactCurrency, formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

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
  const span = `${years} ${years === 1 ? 'year' : 'years'}`;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="rb-price" label="Property Price" value={price} min={priceRange.min} max={priceRange.max} step={priceRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setPrice} />
        <SliderInput id="rb-rent" label="Monthly Rent for a Similar Home" value={monthlyRent} min={rentRange.min} max={rentRange.max} step={rentRange.step} prefix={currency.symbol} scalable locale={locale} onChange={setRent} />
        <SliderInput id="rb-years" label="How Long You Plan to Stay" value={years} min={1} max={30} step={1} suffix=" Yr" onChange={setYears} />
        <SliderInput id="rb-down" label="Down Payment" value={downPercent} min={0} max={100} step={1} suffix="%" onChange={setDownPercent} />
        <SliderInput id="rb-rate" label="Loan Interest Rate (p.a.)" value={annualRate} min={0} max={16} step={0.05} suffix="%" onChange={setAnnualRate} />
        <SliderInput id="rb-tenure" label="Loan Term" value={tenureYears} min={5} max={maxTenureYears} step={1} suffix=" Yr" onChange={setTenureYears} />
        <details class="calc-more">
          <summary>Costs and growth rates</summary>
          <div class="calc-more-grid">
            <SliderInput id="rb-buying" label="Buying Costs (share of price)" value={buyingCostPercent} min={0} max={15} step={0.25} suffix="%" onChange={setBuyingCost} />
            <SliderInput id="rb-selling" label="Selling Costs (share of sale price)" value={sellingCostPercent} min={0} max={10} step={0.25} suffix="%" onChange={setSellingCost} />
            <SliderInput id="rb-owning" label="Yearly Ownership Costs (share of price)" value={ownershipCostPercent} min={0} max={5} step={0.1} suffix="%" onChange={setOwnershipCost} />
            <SliderInput id="rb-growth" label="Yearly Home Price Growth" value={appreciationPercent} min={0} max={15} step={0.25} suffix="%" onChange={setAppreciation} />
            <SliderInput id="rb-rent-growth" label="Yearly Rent Growth" value={rentGrowthPercent} min={0} max={15} step={0.25} suffix="%" onChange={setRentGrowth} />
            <SliderInput id="rb-return" label="Yearly Return on Investments" value={investmentReturnPercent} min={0} max={20} step={0.25} suffix="%" onChange={setReturn} />
          </div>
        </details>
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: `${buyingWins ? 'Buying' : 'Renting'} leaves you better off by`, value: Math.abs(r.advantage), highlight: true },
            { label: 'Net worth if you buy', note: `After ${span}`, value: r.buyerNetWorth, seriesKey: 1 },
            { label: 'Net worth if you rent and invest', note: `After ${span}`, value: r.renterNetWorth, seriesKey: 2 },
            { label: 'Cash needed upfront to buy', value: r.upfrontCash },
            { label: `Monthly ${paymentWord}`, value: r.monthlyLoanPayment },
          ]}
        />
        {r.breakEvenYear !== null ? (
          <Verdict title={`Buying moves ahead for good in year ${r.breakEvenYear}`}>
            If you might move before then, renting is likely to work out better.
          </Verdict>
        ) : (
          <Verdict title={`Buying does not catch up within ${span}`}>
            Try a longer stay or different growth rates to see what would change that.
          </Verdict>
        )}
      </div>

      <div class="calc-below">
        <LineChart
          title="Net worth if you buy or rent"
          caption="If you sold or cashed out at the end of each year"
          x={r.yearly.map((y) => y.year)}
          series={[
            { name: 'If you buy', values: r.yearly.map((y) => y.buyerNetWorth) },
            { name: 'If you rent', values: r.yearly.map((y) => y.renterNetWorth) },
          ]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, currency.code)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => `Year ${y}`}
          marker={r.breakEvenYear !== null && r.breakEvenYear > 1 ? { x: r.breakEvenYear, label: 'Buying moves ahead' } : null}
        />
      </div>
    </div>
  );
}
