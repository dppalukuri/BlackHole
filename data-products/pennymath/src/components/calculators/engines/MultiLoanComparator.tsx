import { useState } from 'preact/hooks';
import { calculateEMI } from '../../../lib/formulas/loan-emi';
import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import LineChart from '../ui/LineChart';
import Verdict from '../ui/Verdict';

interface LoanInput {
  name: string;
  amount: number;
  rate: number;
  tenure: number;
}

const fmt = (n: number) => formatCurrency(n, 'INR');

export default function MultiLoanComparator() {
  const [loans, setLoans] = useState<LoanInput[]>([
    { name: 'Bank A', amount: 3000000, rate: 8.5, tenure: 20 },
    { name: 'Bank B', amount: 3000000, rate: 8.75, tenure: 20 },
    { name: 'Bank C', amount: 3000000, rate: 9.0, tenure: 15 },
  ]);

  const update = (idx: number, field: keyof LoanInput, value: string | number) => {
    setLoans((prev) => prev.map((l, i) => (i === idx ? { ...l, [field]: value } : l)));
  };

  const results = loans.map((l) => {
    const months = Math.max(1, Math.round(l.tenure * 12));
    return { ...l, ...calculateEMI(Math.max(0, l.amount), Math.max(0, l.rate), months) };
  });

  const bestInterest = Math.min(...results.map((r) => r.totalInterest));
  const worstInterest = Math.max(...results.map((r) => r.totalInterest));
  const bestEMI = Math.min(...results.map((r) => r.emi));
  const best = results.find((r) => r.totalInterest === bestInterest)!;

  const longest = Math.max(...results.map((r) => Math.ceil(r.schedule.length / 12)));
  const years = Array.from({ length: longest + 1 }, (_, y) => y);
  const balanceAt = (r: (typeof results)[number], y: number) => {
    if (y === 0) return r.amount;
    return y * 12 <= r.schedule.length ? r.schedule[y * 12 - 1].balance : 0;
  };

  const field = (idx: number, key: 'amount' | 'rate' | 'tenure', label: string, unit: string, value: number) => (
    <div>
      <label class="field-label" htmlFor={`loan-${idx}-${key}`}>{label}</label>
      <div class="typed">
        <input
          id={`loan-${idx}-${key}`}
          type="number"
          step="any"
          min="0"
          value={value}
          onInput={(e) => {
            const v = parseFloat((e.target as HTMLInputElement).value);
            if (!isNaN(v)) update(idx, key, v);
          }}
        />
        <span class="unit">{unit}</span>
      </div>
    </div>
  );

  return (
    <div class="calculator-widget calc-wide">
      <div class="offer-grid">
        {results.map((res, idx) => {
          const isBest = res.totalInterest === bestInterest;
          return (
            <div class={`offer ${isBest ? 'is-best' : ''}`}>
              <h3>
                <input class="offer-name" type="text" aria-label={`Name of loan ${idx + 1}`} value={res.name} onInput={(e) => update(idx, 'name', (e.target as HTMLInputElement).value)} />
                {isBest && <span class="tag">Lowest interest</span>}
              </h3>
              {field(idx, 'amount', 'Loan amount', '₹', res.amount)}
              {field(idx, 'rate', 'Interest rate', '%', res.rate)}
              {field(idx, 'tenure', 'Tenure', 'yr', res.tenure)}
              <div class="offer-line"><span>Monthly EMI{res.emi === bestEMI ? ' (lowest)' : ''}</span><b>{fmt(res.emi)}</b></div>
              <div class="offer-line"><span>Total interest</span><b>{fmt(res.totalInterest)}</b></div>
              <div class="offer-line"><span>Total you repay</span><b>{fmt(res.totalPayment)}</b></div>
            </div>
          );
        })}
      </div>

      <div class="calc-answer">
        <Verdict title={`${best.name} saves ${fmt(worstInterest - bestInterest)} in interest`} tone="good">
          That is against the most expensive of the three. A shorter tenure lowers interest but raises the EMI, so compare both.
        </Verdict>
      </div>

      <LineChart
        title="How each loan is paid down"
        caption="Balance left at the end of each year"
        x={years}
        series={results.map((r) => ({ name: r.name, values: years.map((y) => balanceAt(r, y)) }))}
        format={fmt}
        formatTick={(n) => formatCompactCurrency(n, 'INR')}
        xTick={(y) => `Yr ${y}`}
        xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
      />
    </div>
  );
}
