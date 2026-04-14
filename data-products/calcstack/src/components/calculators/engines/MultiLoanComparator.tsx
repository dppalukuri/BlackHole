import { useState } from 'preact/hooks';
import { calculateEMI } from '../../../lib/formulas/loan-emi';
import { formatCurrency } from '../../../lib/formatters';

interface LoanInput {
  name: string;
  amount: number;
  rate: number;
  tenure: number;
}

export default function MultiLoanComparator() {
  const [loans, setLoans] = useState<LoanInput[]>([
    { name: 'Bank A', amount: 3000000, rate: 8.5, tenure: 20 },
    { name: 'Bank B', amount: 3000000, rate: 8.75, tenure: 20 },
    { name: 'Bank C', amount: 3000000, rate: 9.0, tenure: 15 },
  ]);

  const updateLoan = (idx: number, field: keyof LoanInput, value: string | number) => {
    setLoans((prev) => prev.map((l, i) => (i === idx ? { ...l, [field]: value } : l)));
  };

  const results = loans.map((l) => {
    const r = calculateEMI(l.amount, l.rate, l.tenure * 12);
    return { ...l, emi: r.emi, totalInterest: r.totalInterest, totalPayment: r.totalPayment };
  });

  const bestEMI = Math.min(...results.map((r) => r.emi));
  const bestInterest = Math.min(...results.map((r) => r.totalInterest));

  return (
    <div class="calculator-widget">
      <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1.5rem' }}>
        Compare up to 3 loan offers side-by-side. Enter each bank's terms to find the cheapest deal.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        {loans.map((loan, idx) => {
          const res = results[idx];
          const isBestEMI = res.emi === bestEMI;
          const isBestInterest = res.totalInterest === bestInterest;

          return (
            <div style={{
              border: `2px solid ${isBestInterest ? '#22c55e' : '#e2e8f0'}`,
              borderRadius: '12px', padding: '1.25rem',
              background: isBestInterest ? '#f0fdf4' : '#fff',
            }}>
              <input
                type="text" value={loan.name}
                onInput={(e: Event) => updateLoan(idx, 'name', (e.target as HTMLInputElement).value)}
                style={{
                  border: 'none', fontWeight: 700, fontSize: '1.1rem', width: '100%',
                  background: 'transparent', marginBottom: '1rem', outline: 'none',
                }}
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>
                  Loan Amount
                  <input type="number" value={loan.amount} step={100000}
                    onInput={(e: Event) => updateLoan(idx, 'amount', Number((e.target as HTMLInputElement).value))}
                    style={{ display: 'block', width: '100%', padding: '0.4rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginTop: '0.25rem', fontSize: '0.9rem' }}
                  />
                </label>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>
                  Interest Rate (%)
                  <input type="number" value={loan.rate} step={0.05}
                    onInput={(e: Event) => updateLoan(idx, 'rate', Number((e.target as HTMLInputElement).value))}
                    style={{ display: 'block', width: '100%', padding: '0.4rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginTop: '0.25rem', fontSize: '0.9rem' }}
                  />
                </label>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>
                  Tenure (years)
                  <input type="number" value={loan.tenure} step={1}
                    onInput={(e: Event) => updateLoan(idx, 'tenure', Number((e.target as HTMLInputElement).value))}
                    style={{ display: 'block', width: '100%', padding: '0.4rem', border: '1px solid #e2e8f0', borderRadius: '6px', marginTop: '0.25rem', fontSize: '0.9rem' }}
                  />
                </label>
              </div>

              <div style={{ borderTop: '2px solid #e2e8f0', paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Monthly EMI</span>
                  <strong style={{ color: isBestEMI ? '#16a34a' : '#0f172a' }}>
                    {formatCurrency(res.emi, 'INR')}
                    {isBestEMI && ' ✓'}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Total Interest</span>
                  <strong style={{ color: isBestInterest ? '#16a34a' : '#dc2626' }}>
                    {formatCurrency(res.totalInterest, 'INR')}
                    {isBestInterest && ' ✓'}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Total Payment</span>
                  <strong>{formatCurrency(res.totalPayment, 'INR')}</strong>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Savings summary */}
      {results.length > 1 && (
        <div style={{
          background: '#f0fdf4', border: '2px solid #22c55e', borderRadius: '12px',
          padding: '1.25rem', margin: '1.5rem 0', textAlign: 'center',
        }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
            {results.find((r) => r.totalInterest === bestInterest)?.name} saves you
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#16a34a' }}>
            {formatCurrency(Math.max(...results.map((r) => r.totalInterest)) - bestInterest, 'INR')}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>in total interest compared to the most expensive option</div>
        </div>
      )}
    </div>
  );
}
