import { useState } from 'preact/hooks';
import { swpProjection } from '../../../lib/formulas/swp';
import { formatCurrency, localeForCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

interface SWPCalculatorProps {
  currency: { code: string; symbol: string };
  defaults?: {
    totalInvestment?: number;
    monthlyWithdrawal?: number;
    expectedReturn?: number;
    timePeriod?: number;
  };
}

export default function SWPCalculator({ currency, defaults }: SWPCalculatorProps) {
  const [investment, setInvestment] = useState(defaults?.totalInvestment ?? 1000000);
  const [withdrawal, setWithdrawal] = useState(defaults?.monthlyWithdrawal ?? 8000);
  const [rate, setRate] = useState(defaults?.expectedReturn ?? 8);
  const [years, setYears] = useState(defaults?.timePeriod ?? 10);

  const result = swpProjection(investment, withdrawal, rate, years);
  const fmt = (n: number) => formatCurrency(n, currency.code);

  const totalMonths = years * 12;
  const ranOutEarly = result.depleted && result.monthsLasted < totalMonths;
  const lastedYears = Math.floor(result.monthsLasted / 12);
  const lastedMonths = result.monthsLasted % 12;

  const segments = [
    { label: 'Total Withdrawn', value: result.totalWithdrawn, color: '#6366f1' },
    ...(result.finalBalance > 0
      ? [{ label: 'Final Balance', value: result.finalBalance, color: '#22c55e' }]
      : []),
  ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="total-investment"
          label="Total Investment"
          value={investment}
          min={10000}
          max={50000000}
          step={10000}
          prefix={currency.symbol}
          scalable
          locale={localeForCurrency(currency.code)}
          onChange={setInvestment}
        />
        <SliderInput
          id="monthly-withdrawal"
          label="Monthly Withdrawal"
          value={withdrawal}
          min={500}
          max={500000}
          step={500}
          prefix={currency.symbol}
          scalable
          locale={localeForCurrency(currency.code)}
          onChange={setWithdrawal}
        />
        <SliderInput
          id="expected-return"
          label="Expected Return Rate (p.a.)"
          value={rate}
          min={1}
          max={30}
          step={0.5}
          suffix="%"
          onChange={setRate}
        />
        <SliderInput
          id="time-period"
          label="Time Period"
          value={years}
          min={1}
          max={40}
          step={1}
          suffix=" Yr"
          onChange={setYears}
        />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'Total Investment', value: result.investedAmount },
            { label: 'Total Withdrawn', value: result.totalWithdrawn },
            { label: 'Final Balance', value: result.finalBalance, highlight: true },
          ]}
        />
        <DoughnutChart segments={segments} />
      </div>

      {ranOutEarly && (
        <div
          style={{
            marginTop: '1.25rem',
            padding: '0.85rem 1rem',
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.35)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.88rem',
          }}
        >
          <strong style={{ color: '#dc2626' }}>Your corpus runs out early.</strong>{' '}
          Withdrawing {fmt(withdrawal)}/month drains this corpus after{' '}
          <strong>
            {lastedYears} {lastedYears === 1 ? 'year' : 'years'}
            {lastedMonths > 0 && ` ${lastedMonths} ${lastedMonths === 1 ? 'month' : 'months'}`}
          </strong>{' '}
          — only {result.monthsLasted} of your {totalMonths} planned withdrawals are funded. Withdraw up to{' '}
          <strong>{fmt(result.sustainableWithdrawal)}/month</strong> to live off returns alone and leave the
          capital untouched.
        </div>
      )}

      {!ranOutEarly && (
        <div class="gratuity-breakdown" style={{ marginTop: '1.25rem' }}>
          <h3 style={{ marginTop: 0 }}>Capital-preserving withdrawal</h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', margin: 0 }}>
            At {rate}% p.a., this corpus generates about{' '}
            <strong>{fmt(result.sustainableWithdrawal)}/month</strong> in returns. Withdraw less than that and
            your capital keeps growing; withdraw more and you start eating into it.
          </p>
        </div>
      )}

      <details style={{ marginTop: '1.25rem' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', padding: '0.75rem 0' }}>
          View Year-by-Year Breakdown
        </summary>
        <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ textAlign: 'right', color: 'var(--color-text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '0.5rem 0.6rem', fontWeight: 600 }}>Year</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Opening</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Withdrawn</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Returns</th>
                <th style={{ padding: '0.5rem 0.6rem', fontWeight: 600 }}>Closing</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: 'var(--font-mono)' }}>
              {result.yearlyBreakdown.map((row) => (
                <tr style={{ borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
                  <td style={{ textAlign: 'left', padding: '0.45rem 0.6rem', fontWeight: 600 }}>{row.year}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.openingBalance)}</td>
                  <td style={{ padding: '0.45rem 0.6rem' }}>{fmt(row.withdrawn)}</td>
                  <td style={{ padding: '0.45rem 0.6rem', color: '#16a34a' }}>{fmt(row.returnsEarned)}</td>
                  <td style={{ padding: '0.45rem 0.6rem', fontWeight: 600 }}>{fmt(row.closingBalance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
