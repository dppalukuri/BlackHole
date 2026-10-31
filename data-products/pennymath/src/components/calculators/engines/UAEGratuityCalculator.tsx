import { useState } from 'preact/hooks';
import { uaeGratuity } from '../../../lib/formulas/flat-rate';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import { formatCompactCurrency, formatCurrency, localeForCurrency } from '../../../lib/formatters';

interface UAEGratuityCalculatorProps {
  currency: { code: string; symbol: string };
}

const SERVICE_YEARS = Array.from({ length: 31 }, (_, y) => y);

export default function UAEGratuityCalculator({ currency }: UAEGratuityCalculatorProps) {
  const [salary, setSalary] = useState(10000);
  const [years, setYears] = useState(5);

  const result = uaeGratuity(salary, years);
  const fmt = (n: number) => formatCurrency(n, currency.code);
  const dailyWage = salary / 30;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="basic-salary" label="Basic Monthly Salary" value={salary} min={1000} max={100000} step={500} prefix={currency.symbol} scalable locale={localeForCurrency(currency.code)} onChange={setSalary} />
        <SliderInput id="years-of-service" label="Years of Service" value={years} min={0} max={30} step={0.5} suffix=" Yr" onChange={setYears} />
        <div class="calc-note">
          {years < 1 ? (
            <p>You need at least 1 year of service to be eligible for gratuity.</p>
          ) : years <= 5 ? (
            <p>Daily wage of {fmt(dailyWage)} × 21 days × {years} {years === 1 ? 'year' : 'years'}.</p>
          ) : (
            <>
              <p>First 5 years: daily wage of {fmt(dailyWage)} × 21 days × 5 = {fmt(dailyWage * 21 * 5)}.</p>
              <p>Remaining {years - 5} years: {fmt(dailyWage)} × 30 days × {years - 5} = {fmt(dailyWage * 30 * (years - 5))}.</p>
            </>
          )}
        </div>
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[{ label: 'End-of-service gratuity', value: result.gratuityAmount, highlight: true }]}
        />
      </div>

      <div class="calc-below">
        <LineChart
          title="How gratuity builds with service"
          caption="It builds faster after 5 years, up to a cap of 2 years' salary"
          x={SERVICE_YEARS}
          series={[{ name: 'Gratuity', values: SERVICE_YEARS.map((y) => uaeGratuity(salary, y).gratuityAmount) }]}
          format={fmt}
          formatTick={(n) => formatCompactCurrency(n, currency.code)}
          xTick={(y) => `${y} yrs`}
          xTitle={(y) => `${y} ${y === 1 ? 'year' : 'years'} of service`}
          xHeading="Service"
          marker={{ x: years, label: 'Your service' }}
          showTable={false}
        />
      </div>
    </div>
  );
}
