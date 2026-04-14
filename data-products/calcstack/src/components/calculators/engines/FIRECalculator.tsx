import { useState } from 'preact/hooks';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';

export default function FIRECalculator() {
  const [monthlyExpenses, setMonthlyExpenses] = useState(50000);
  const [currentSavings, setCurrentSavings] = useState(500000);
  const [monthlySavings, setMonthlySavings] = useState(30000);
  const [expectedReturn, setExpectedReturn] = useState(12);
  const [inflationRate, setInflationRate] = useState(6);
  const [withdrawalRate, setWithdrawalRate] = useState(3);
  const [currentAge, setCurrentAge] = useState(28);

  // FIRE number = annual expenses / withdrawal rate (inflation-adjusted)
  const realReturn = ((1 + expectedReturn / 100) / (1 + inflationRate / 100) - 1) * 100;
  const annualExpenses = monthlyExpenses * 12;
  const fireNumber = annualExpenses / (withdrawalRate / 100);

  // How many years to reach FIRE number
  const monthlyRate = realReturn / 12 / 100;
  let corpus = currentSavings;
  let months = 0;
  const maxMonths = 600; // 50 years cap

  const milestones: Array<{ year: number; corpus: number; pctToFire: number }> = [];

  while (corpus < fireNumber && months < maxMonths) {
    corpus = (corpus + monthlySavings) * (1 + monthlyRate);
    months++;
    if (months % 12 === 0) {
      milestones.push({
        year: months / 12,
        corpus,
        pctToFire: Math.min(100, (corpus / fireNumber) * 100),
      });
    }
  }

  const yearsToFire = months / 12;
  const fireAge = currentAge + yearsToFire;
  const canRetire = months < maxMonths;

  // Monthly passive income at FIRE
  const monthlyPassiveIncome = fireNumber * (withdrawalRate / 100) / 12;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="current-age" label="Your Current Age" value={currentAge} min={18} max={60} step={1} suffix=" yr" onChange={setCurrentAge} />
        <SliderInput id="monthly-expenses" label="Monthly Expenses (current)" value={monthlyExpenses} min={5000} max={500000} step={1000} prefix="₹" onChange={setMonthlyExpenses} />
        <SliderInput id="current-savings" label="Current Savings & Investments" value={currentSavings} min={0} max={50000000} step={50000} prefix="₹" onChange={setCurrentSavings} />
        <SliderInput id="monthly-savings" label="Monthly Savings/Investment" value={monthlySavings} min={0} max={500000} step={1000} prefix="₹" onChange={setMonthlySavings} />
        <SliderInput id="return" label="Expected Return (p.a.)" value={expectedReturn} min={1} max={20} step={0.5} suffix="%" onChange={setExpectedReturn} />
        <SliderInput id="inflation" label="Inflation Rate" value={inflationRate} min={1} max={12} step={0.5} suffix="%" onChange={setInflationRate} />
        <SliderInput id="withdrawal" label="Safe Withdrawal Rate" value={withdrawalRate} min={2} max={5} step={0.25} suffix="%" onChange={setWithdrawalRate} />
      </div>

      {/* FIRE Verdict */}
      <div style={{
        background: canRetire ? '#f0fdf4' : '#fef2f2',
        border: `2px solid ${canRetire ? '#22c55e' : '#ef4444'}`,
        borderRadius: '12px', padding: '1.5rem', textAlign: 'center', margin: '1.5rem 0',
      }}>
        {canRetire ? (
          <>
            <div style={{ fontSize: '0.9rem', color: '#64748b' }}>You can achieve Financial Independence at age</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#16a34a' }}>{Math.round(fireAge)}</div>
            <div style={{ fontSize: '1rem', color: '#64748b' }}>
              That's <strong>{yearsToFire.toFixed(1)} years</strong> from now
            </div>
          </>
        ) : (
          <>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#dc2626' }}>
              At current savings rate, FIRE is not achievable in 50 years.
            </div>
            <div style={{ fontSize: '0.9rem', color: '#64748b', marginTop: '0.5rem' }}>
              Increase monthly savings or reduce expenses to make it work.
            </div>
          </>
        )}
      </div>

      {/* Key Numbers */}
      <div class="result-card">
        <div class="result-item result-highlight">
          <span class="result-label">Your FIRE Number</span>
          <span class="result-value">{formatCurrency(fireNumber, 'INR')}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Monthly Passive Income at FIRE</span>
          <span class="result-value">{formatCurrency(monthlyPassiveIncome, 'INR')}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Real Return (after inflation)</span>
          <span class="result-value">{realReturn.toFixed(1)}%</span>
        </div>
        <div class="result-item">
          <span class="result-label">Current Progress</span>
          <span class="result-value">{Math.min(100, (currentSavings / fireNumber) * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Progress bars by milestone */}
      {milestones.length > 0 && (
        <details style={{ marginTop: '1.5rem' }}>
          <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>
            View Year-by-Year Progress
          </summary>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
            {milestones.slice(0, 30).map((m) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.85rem' }}>
                <span style={{ width: '60px', fontWeight: 600 }}>Year {m.year}</span>
                <div style={{ flex: 1, background: '#e2e8f0', borderRadius: '4px', height: '20px', position: 'relative' }}>
                  <div style={{
                    width: `${Math.min(100, m.pctToFire)}%`,
                    background: m.pctToFire >= 100 ? '#22c55e' : '#6366f1',
                    borderRadius: '4px', height: '100%', transition: 'width 0.3s',
                  }} />
                </div>
                <span style={{ width: '120px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  {formatCurrency(m.corpus, 'INR')}
                </span>
              </div>
            ))}
          </div>
        </details>
      )}

      <div class="gratuity-breakdown" style={{ marginTop: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>What is the FIRE Movement?</h3>
        <p style={{ fontSize: '0.9rem', color: '#64748b' }}>
          FIRE (Financial Independence, Retire Early) means accumulating enough investments that the passive income
          covers your living expenses — forever. The <strong>{withdrawalRate}% withdrawal rate</strong> means you withdraw
          {withdrawalRate}% of your corpus annually, which historically sustains a portfolio indefinitely (the "Trinity Study" / "4% rule",
          adjusted to {withdrawalRate}% for Indian inflation and market conditions).
        </p>
      </div>
    </div>
  );
}
