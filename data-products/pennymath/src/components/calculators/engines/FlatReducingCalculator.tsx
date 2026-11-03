import { useState } from 'preact/hooks';
import { compareFlatReducing } from '../../../lib/formulas/flat-reducing';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';

interface FlatReducingCalculatorProps {
  currency: { code: string; symbol: string };
  /** Words as local lenders use them, e.g. "Monthly EMI" in India, "Monthly repayment" in the UAE. */
  labels: { term: string; payment: string; total: string };
  defaults: { amount: number; rate: number; months: number };
}

const pct = (n: number) => `${Number(n.toFixed(2))}%`;

/** Converts a flat interest rate to the reducing rate that costs the same, and compares the two. */
export default function FlatReducingCalculator({ currency, labels, defaults }: FlatReducingCalculatorProps) {
  const [amount, setAmount] = useState(defaults.amount);
  const [rate, setRate] = useState(defaults.rate);
  const [months, setMonths] = useState(defaults.months);

  const result = compareFlatReducing(amount, rate, Math.round(months));
  const fmt = (n: number) => formatCurrency(n, currency.code);
  const saving = result.flat.totalInterest - result.reducing.totalInterest;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="fr-amount" label="Loan amount" value={amount} min={1000} max={1000000} step={1000} prefix={currency.symbol} scalable locale={localeForCurrency(currency.code)} onChange={setAmount} />
        <SliderInput id="fr-rate" label="Interest rate (per year)" value={rate} min={0.5} max={30} step={0.05} suffix="%" onChange={setRate} />
        <SliderInput id="fr-term" label={labels.term} value={months} min={6} max={120} step={1} suffix=" mo" onChange={setMonths} />
      </div>

      <div class="calc-answer">
        <div class="result-card ff-compare">
          <div class="fr-convert">
            <span>A {pct(rate)} flat rate is the same as</span>
            <strong>{pct(result.equivalentReducingRate)}</strong>
            <span>reducing rate per year</span>
          </div>
          <table>
            <thead>
              <tr>
                <th scope="col"><span class="sr-only">Cost</span></th>
                <th scope="col">{pct(rate)} flat</th>
                <th scope="col">{pct(rate)} reducing</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">{labels.payment}</th>
                <td>{fmt(result.flat.emi)}</td>
                <td>{fmt(result.reducing.emi)}</td>
              </tr>
              <tr>
                <th scope="row">Total interest</th>
                <td>{fmt(result.flat.totalInterest)}</td>
                <td>{fmt(result.reducing.totalInterest)}</td>
              </tr>
              <tr>
                <th scope="row">{labels.total}</th>
                <td>{fmt(result.flat.totalAmount)}</td>
                <td>{fmt(result.reducing.totalAmount)}</td>
              </tr>
            </tbody>
          </table>
          <div class="ff-saving">
            {saving >= 1 && <strong>At the same {pct(rate)}, a reducing rate saves {fmt(saving)}</strong>}
            <p>A flat rate charges interest on the full loan for the whole term, even as you repay it. A reducing rate charges it only on what you still owe.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
