import { useState } from 'preact/hooks';
import { calculateEMI } from '../../../lib/formulas/loan-emi';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';

/** Where to go next depends on the currency, so a visitor lands on their own country's tool. */
const NEXT: Record<string, { label: string; path: string }> = {
  AED: { label: 'See what you can afford in the UAE', path: '/uae/mortgage-affordability-calculator/' },
  INR: { label: 'Open the EMI calculator', path: '/india/emi-calculator/' },
  GBP: { label: 'Open the UK mortgage calculator', path: '/uk/mortgage-calculator/' },
  USD: { label: 'Open the US mortgage calculator', path: '/us/mortgage-calculator/' },
};

const parse = (s: string) => parseFloat(s.replace(/[^0-9.]/g, ''));

export default function QuickLoanEstimate() {
  const [currency, setCurrency] = useState('AED');
  const [amount, setAmount] = useState('1,500,000');
  const [rate, setRate] = useState('5');
  const [years, setYears] = useState('25');

  const a = parse(amount);
  const r = parse(rate);
  const y = parse(years);
  const valid = a > 0 && r >= 0 && y >= 1 && y <= 50;
  const result = valid ? calculateEMI(a, r, Math.round(y * 12)) : null;
  const next = NEXT[currency];

  const reformat = () => { if (a > 0) setAmount(a.toLocaleString(localeForCurrency(currency))); };
  const changeCurrency = (code: string) => {
    setCurrency(code);
    if (a > 0) setAmount(a.toLocaleString(localeForCurrency(code)));
  };

  return (
    <>
      <div class="try-copy">
        <h2>What will this loan cost you each month?</h2>
        <p>Change any figure and the answer updates as you type. Every PennyMath calculator works this way.</p>
        <a class="btn" href={next.path}>{next.label}</a>
      </div>
      <form class="try-card" onSubmit={(e) => e.preventDefault()} aria-label="Quick loan estimate">
        <div>
          <label class="field-label" htmlFor="try-amount">You borrow</label>
          <div class="try-big">
            <select aria-label="Currency" value={currency} onChange={(e) => changeCurrency((e.target as HTMLSelectElement).value)}>
              {Object.keys(NEXT).map((code) => <option value={code}>{code}</option>)}
            </select>
            <input
              id="try-amount"
              type="text"
              inputMode="decimal"
              value={amount}
              onFocus={() => { if (a > 0) setAmount(String(a)); }}
              onInput={(e) => setAmount((e.target as HTMLInputElement).value)}
              onBlur={reformat}
            />
          </div>
        </div>
        <div class="try-pair">
          <div>
            <label class="field-label" htmlFor="try-rate">Interest rate</label>
            <div class="typed">
              <input id="try-rate" type="text" inputMode="decimal" value={rate} onInput={(e) => setRate((e.target as HTMLInputElement).value)} />
              <span class="unit">%</span>
            </div>
          </div>
          <div>
            <label class="field-label" htmlFor="try-years">Term</label>
            <div class="typed">
              <input id="try-years" type="text" inputMode="decimal" value={years} onInput={(e) => setYears((e.target as HTMLInputElement).value)} />
              <span class="unit">yr</span>
            </div>
          </div>
        </div>
        <div class="try-result" aria-live="polite">
          <span class="field-label">You pay each month</span>
          <output>{result ? formatCurrency(result.emi, currency) : '–'}</output>
          <small>
            {result
              ? `Total interest over the term: ${formatCurrency(result.totalInterest, currency)}`
              : 'Enter an amount, a rate and a term of 1 to 50 years.'}
          </small>
        </div>
      </form>
    </>
  );
}
