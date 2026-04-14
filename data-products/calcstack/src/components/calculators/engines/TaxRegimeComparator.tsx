import { useState } from 'preact/hooks';
import { formatCurrency } from '../../../lib/formatters';

interface Deductions {
  section80C: number;
  section80D: number;
  hra: number;
  homeLoanInterest: number;
  nps80CCD: number;
  other: number;
}

function calcOldRegime(income: number, d: Deductions) {
  const standardDeduction = 50000;
  const totalDeductions = d.section80C + d.section80D + d.hra + d.homeLoanInterest + d.nps80CCD + d.other + standardDeduction;
  const taxable = Math.max(0, income - totalDeductions);

  const slabs = [
    { max: 250000, rate: 0 },
    { max: 500000, rate: 5 },
    { max: 1000000, rate: 20 },
    { max: Infinity, rate: 30 },
  ];

  let tax = 0;
  let prev = 0;
  for (const s of slabs) {
    if (taxable <= prev) break;
    const chunk = Math.min(taxable, s.max) - prev;
    tax += (chunk * s.rate) / 100;
    prev = s.max;
  }

  // 87A rebate old regime: income <= 5L
  if (taxable <= 500000) tax = 0;
  const cess = tax * 0.04;
  return { taxable, totalDeductions, tax, cess, total: tax + cess };
}

function calcNewRegime(income: number) {
  const standardDeduction = 75000;
  const taxable = Math.max(0, income - standardDeduction);

  const slabs = [
    { max: 400000, rate: 0 },
    { max: 800000, rate: 5 },
    { max: 1200000, rate: 10 },
    { max: 1600000, rate: 15 },
    { max: 2000000, rate: 20 },
    { max: 2400000, rate: 25 },
    { max: Infinity, rate: 30 },
  ];

  let tax = 0;
  let prev = 0;
  for (const s of slabs) {
    if (taxable <= prev) break;
    const chunk = Math.min(taxable, s.max) - prev;
    tax += (chunk * s.rate) / 100;
    prev = s.max;
  }

  if (taxable <= 1200000) tax = 0;
  const cess = tax * 0.04;
  return { taxable, totalDeductions: standardDeduction, tax, cess, total: tax + cess };
}

export default function TaxRegimeComparator() {
  const [income, setIncome] = useState(1500000);
  const [deductions, setDeductions] = useState<Deductions>({
    section80C: 150000,
    section80D: 25000,
    hra: 0,
    homeLoanInterest: 0,
    nps80CCD: 50000,
    other: 0,
  });

  const oldResult = calcOldRegime(income, deductions);
  const newResult = calcNewRegime(income);
  const saving = oldResult.total - newResult.total;
  const betterRegime = saving > 0 ? 'new' : saving < 0 ? 'old' : 'same';
  const savingAmt = Math.abs(saving);

  const updateDeduction = (key: keyof Deductions, val: number) => {
    setDeductions((prev) => ({ ...prev, [key]: val }));
  };

  const deductionFields = [
    { key: 'section80C' as const, label: 'Section 80C (PPF, ELSS, LIC, etc.)', max: 150000 },
    { key: 'section80D' as const, label: 'Section 80D (Health Insurance)', max: 100000 },
    { key: 'hra' as const, label: 'HRA Exemption', max: 500000 },
    { key: 'homeLoanInterest' as const, label: 'Home Loan Interest (Sec 24)', max: 200000 },
    { key: 'nps80CCD' as const, label: 'NPS 80CCD(1B)', max: 50000 },
    { key: 'other' as const, label: 'Other Deductions', max: 500000 },
  ];

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <div class="slider-group">
          <div class="slider-header">
            <label htmlFor="gross-income">Gross Annual Income</label>
            <div class="slider-value-box">
              <span class="prefix">₹</span>
              <input
                type="text"
                class="value-input"
                value={income.toLocaleString('en-IN')}
                onInput={(e: Event) => {
                  const v = parseInt((e.target as HTMLInputElement).value.replace(/[^0-9]/g, ''));
                  if (!isNaN(v)) setIncome(Math.min(50000000, Math.max(0, v)));
                }}
              />
            </div>
          </div>
          <input
            type="range" class="range-slider" min={0} max={50000000} step={50000}
            value={income}
            onInput={(e: Event) => setIncome(Number((e.target as HTMLInputElement).value))}
            style={`--fill: ${(income / 50000000) * 100}%`}
          />
        </div>

        <h3 style="margin-top: 1rem; margin-bottom: 0.5rem;">Your Deductions (Old Regime Only)</h3>
        <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 1rem;">Enter your actual deductions to compare which regime saves you more tax.</p>

        {deductionFields.map((f) => (
          <div class="slider-group" style="margin-bottom: 0.75rem;">
            <div class="slider-header">
              <label style="font-size: 0.85rem;">{f.label}</label>
              <div class="slider-value-box" style="padding: 0.2rem 0.5rem;">
                <span class="prefix" style="font-size: 0.8rem;">₹</span>
                <input
                  type="text" class="value-input" style="width: 80px; font-size: 0.85rem;"
                  value={deductions[f.key].toLocaleString('en-IN')}
                  onInput={(e: Event) => {
                    const v = parseInt((e.target as HTMLInputElement).value.replace(/[^0-9]/g, ''));
                    if (!isNaN(v)) updateDeduction(f.key, Math.min(f.max, Math.max(0, v)));
                  }}
                />
              </div>
            </div>
            <input
              type="range" class="range-slider" min={0} max={f.max} step={5000}
              value={deductions[f.key]}
              onInput={(e: Event) => updateDeduction(f.key, Number((e.target as HTMLInputElement).value))}
              style={`--fill: ${(deductions[f.key] / f.max) * 100}%`}
            />
          </div>
        ))}
      </div>

      {/* Verdict Banner */}
      <div style={{
        background: betterRegime === 'new' ? '#f0fdf4' : betterRegime === 'old' ? '#eff6ff' : '#f8fafc',
        border: `2px solid ${betterRegime === 'new' ? '#22c55e' : betterRegime === 'old' ? '#3b82f6' : '#e2e8f0'}`,
        borderRadius: '12px',
        padding: '1.5rem',
        textAlign: 'center',
        margin: '1.5rem 0',
      }}>
        <div style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '0.25rem' }}>
          {betterRegime === 'same' ? 'Both regimes result in the same tax' : `The ${betterRegime === 'new' ? 'NEW' : 'OLD'} regime saves you`}
        </div>
        {betterRegime !== 'same' && (
          <div style={{ fontSize: '2rem', fontWeight: 800, color: betterRegime === 'new' ? '#16a34a' : '#2563eb' }}>
            {formatCurrency(savingAmt, 'INR')}
          </div>
        )}
        <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.25rem' }}>
          {betterRegime === 'same' ? '' : `Choose the ${betterRegime.toUpperCase()} Tax Regime`}
        </div>
      </div>

      {/* Side by Side Comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div style={{
          background: betterRegime === 'old' ? '#eff6ff' : '#f8fafc',
          border: `2px solid ${betterRegime === 'old' ? '#3b82f6' : '#e2e8f0'}`,
          borderRadius: '12px', padding: '1.25rem',
        }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>
            Old Regime {betterRegime === 'old' && '✓'}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Gross Income</span><strong>{formatCurrency(income, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Total Deductions</span><strong>-{formatCurrency(oldResult.totalDeductions, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Taxable Income</span><strong>{formatCurrency(oldResult.taxable, 'INR')}</strong>
            </div>
            <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Income Tax</span><strong>{formatCurrency(oldResult.tax, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Cess (4%)</span><strong>{formatCurrency(oldResult.cess, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', fontWeight: 800, paddingTop: '0.5rem', borderTop: '2px solid #e2e8f0' }}>
              <span>Total Tax</span><span>{formatCurrency(oldResult.total, 'INR')}</span>
            </div>
          </div>
        </div>

        <div style={{
          background: betterRegime === 'new' ? '#f0fdf4' : '#f8fafc',
          border: `2px solid ${betterRegime === 'new' ? '#22c55e' : '#e2e8f0'}`,
          borderRadius: '12px', padding: '1.25rem',
        }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>
            New Regime {betterRegime === 'new' && '✓'}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Gross Income</span><strong>{formatCurrency(income, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Standard Deduction</span><strong>-{formatCurrency(75000, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Taxable Income</span><strong>{formatCurrency(newResult.taxable, 'INR')}</strong>
            </div>
            <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Income Tax</span><strong>{formatCurrency(newResult.tax, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Cess (4%)</span><strong>{formatCurrency(newResult.cess, 'INR')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', fontWeight: 800, paddingTop: '0.5rem', borderTop: '2px solid #e2e8f0' }}>
              <span>Total Tax</span><span>{formatCurrency(newResult.total, 'INR')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
