import { useState } from 'preact/hooks';
import { calculateEMI } from '../../../lib/formulas/loan-emi';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import LineChart from '../ui/LineChart';
import { formatCompactCurrency, formatCurrency, localeForCurrency } from '../../../lib/formatters';

interface EMICalculatorProps {
  currency: { code: string; symbol: string };
  defaults?: {
    loanAmount?: number;
    interestRate?: number;
    loanTenure?: number;
  };
}

export default function EMICalculator({ currency, defaults }: EMICalculatorProps) {
  const [principal, setPrincipal] = useState(defaults?.loanAmount ?? 2000000);
  const [rate, setRate] = useState(defaults?.interestRate ?? 8.5);
  const [tenure, setTenure] = useState(defaults?.loanTenure ?? 20);

  const result = calculateEMI(principal, rate, tenure * 12);
  // "EMI" and "tenure" are Indian terms. This calculator also serves the UK and US.
  const isIndia = currency.code === 'INR';

  const years = Array.from({ length: tenure + 1 }, (_, y) => y);
  let interestSoFar = 0;
  const interestByYear = [0];
  result.schedule.forEach((row, i) => {
    interestSoFar += row.interest;
    if ((i + 1) % 12 === 0) interestByYear.push(interestSoFar);
  });
  const balanceByYear = years.map((y) => (y === 0 ? principal : result.schedule[y * 12 - 1].balance));

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="loan-amount" label="Loan Amount" value={principal} min={100000} max={100000000} step={100000} prefix={currency.symbol} scalable locale={localeForCurrency(currency.code)} onChange={setPrincipal} />
        <SliderInput id="interest-rate" label="Interest Rate (p.a.)" value={rate} min={1} max={20} step={0.1} suffix="%" onChange={setRate} />
        <SliderInput id="loan-tenure" label={isIndia ? 'Loan Tenure' : 'Loan Term'} value={tenure} min={1} max={30} step={1} suffix=" Yr" onChange={setTenure} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: isIndia ? 'Monthly EMI' : 'Monthly payment', value: result.emi, highlight: true },
            { label: 'Total interest', value: result.totalInterest, seriesKey: 2 },
            { label: 'Total you repay', value: result.totalPayment },
          ]}
        />
      </div>

      <div class="calc-below">
        <LineChart
          title="How your loan is paid down"
          caption="At the end of each year"
          x={years}
          series={[
            { name: 'Balance left', values: balanceByYear },
            { name: 'Interest paid so far', values: interestByYear },
          ]}
          format={(n) => formatCurrency(n, currency.code)}
          formatTick={(n) => formatCompactCurrency(n, currency.code)}
          xTick={(y) => `Yr ${y}`}
          xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
        />
      </div>
    </div>
  );
}
