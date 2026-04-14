import { useState } from 'preact/hooks';
import { calculateEMI } from '../../../lib/formulas/loan-emi';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

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

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="loan-amount"
          label="Loan Amount"
          value={principal}
          min={100000}
          max={100000000}
          step={100000}
          prefix={currency.symbol}
          onChange={setPrincipal}
        />
        <SliderInput
          id="interest-rate"
          label="Interest Rate (p.a.)"
          value={rate}
          min={1}
          max={20}
          step={0.1}
          suffix="%"
          onChange={setRate}
        />
        <SliderInput
          id="loan-tenure"
          label="Loan Tenure"
          value={tenure}
          min={1}
          max={30}
          step={1}
          suffix=" Yr"
          onChange={setTenure}
        />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'Monthly EMI', value: result.emi, highlight: true },
            { label: 'Total Interest', value: result.totalInterest },
            { label: 'Total Payment', value: result.totalPayment },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Principal', value: principal, color: '#6366f1' },
            { label: 'Interest', value: result.totalInterest, color: '#f43f5e' },
          ]}
        />
      </div>
    </div>
  );
}
