import { useState } from 'preact/hooks';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import DoughnutChart from '../ui/DoughnutChart';

function calcStepUpSIP(monthly: number, annualRate: number, years: number, stepUpPct: number) {
  const monthlyRate = annualRate / 12 / 100;
  let totalInvested = 0;
  let totalValue = 0;
  let currentMonthly = monthly;
  const yearlyBreakdown = [];

  for (let y = 1; y <= years; y++) {
    // Each year, invest currentMonthly for 12 months
    for (let m = 0; m < 12; m++) {
      totalInvested += currentMonthly;
      totalValue = (totalValue + currentMonthly) * (1 + monthlyRate);
    }
    yearlyBreakdown.push({
      year: y,
      monthlySIP: currentMonthly,
      invested: totalInvested,
      value: totalValue,
    });
    // Step up at year end
    currentMonthly = Math.round(currentMonthly * (1 + stepUpPct / 100));
  }

  return { totalInvested, totalValue, totalReturns: totalValue - totalInvested, yearlyBreakdown };
}

function calcRegularSIP(monthly: number, annualRate: number, years: number) {
  const monthlyRate = annualRate / 12 / 100;
  const months = years * 12;
  if (monthlyRate === 0) return monthly * months;
  return monthly * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate) * (1 + monthlyRate);
}

export default function StepUpSIPCalculator() {
  const [monthly, setMonthly] = useState(10000);
  const [rate, setRate] = useState(12);
  const [years, setYears] = useState(15);
  const [stepUp, setStepUp] = useState(10);

  const stepUpResult = calcStepUpSIP(monthly, rate, years, stepUp);
  const regularValue = calcRegularSIP(monthly, rate, years);
  const extraWealth = stepUpResult.totalValue - regularValue;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="monthly" label="Starting Monthly SIP" value={monthly} min={500} max={500000} step={500} prefix="₹" onChange={setMonthly} />
        <SliderInput id="step-up" label="Annual Step-Up" value={stepUp} min={0} max={50} step={1} suffix="%" onChange={setStepUp} />
        <SliderInput id="return-rate" label="Expected Return (p.a.)" value={rate} min={1} max={25} step={0.5} suffix="%" onChange={setRate} />
        <SliderInput id="years" label="Time Period" value={years} min={1} max={30} step={1} suffix=" Yr" onChange={setYears} />
      </div>

      {/* Comparison Banner */}
      <div style={{
        background: '#f0fdf4', border: '2px solid #22c55e', borderRadius: '12px',
        padding: '1.25rem', margin: '1.5rem 0', textAlign: 'center',
      }}>
        <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Step-Up SIP creates</div>
        <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#16a34a' }}>
          {formatCurrency(extraWealth, 'INR')} more
        </div>
        <div style={{ fontSize: '0.85rem', color: '#64748b' }}>than a regular SIP of {formatCurrency(monthly, 'INR')}/month</div>
      </div>

      <div class="calc-results">
        <div class="result-card">
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Step-Up SIP ({stepUp}% annual increase)</div>
          <div class="result-item">
            <span class="result-label">Total Invested</span>
            <span class="result-value">{formatCurrency(stepUpResult.totalInvested, 'INR')}</span>
          </div>
          <div class="result-item">
            <span class="result-label">Est. Returns</span>
            <span class="result-value">{formatCurrency(stepUpResult.totalReturns, 'INR')}</span>
          </div>
          <div class="result-item result-highlight">
            <span class="result-label">Total Value</span>
            <span class="result-value">{formatCurrency(stepUpResult.totalValue, 'INR')}</span>
          </div>

          <div style={{ marginTop: '1.25rem', fontSize: '0.8rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Regular SIP (no increase)</div>
          <div class="result-item" style={{ opacity: 0.7 }}>
            <span class="result-label">Total Value</span>
            <span class="result-value">{formatCurrency(regularValue, 'INR')}</span>
          </div>
        </div>

        <DoughnutChart
          segments={[
            { label: 'Invested', value: stepUpResult.totalInvested, color: '#6366f1' },
            { label: 'Returns', value: stepUpResult.totalReturns, color: '#22c55e' },
          ]}
        />
      </div>

      {/* Year-by-year table */}
      <details style={{ marginTop: '1.5rem' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>
          View Year-by-Year Breakdown
        </summary>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Year</th>
                <th style={{ padding: '0.5rem' }}>Monthly SIP</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Total Invested</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Portfolio Value</th>
              </tr>
            </thead>
            <tbody>
              {stepUpResult.yearlyBreakdown.map((row) => (
                <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <td style={{ padding: '0.5rem' }}>{row.year}</td>
                  <td style={{ padding: '0.5rem' }}>{formatCurrency(row.monthlySIP, 'INR')}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{formatCurrency(row.invested, 'INR')}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right', fontWeight: 600 }}>{formatCurrency(row.value, 'INR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
