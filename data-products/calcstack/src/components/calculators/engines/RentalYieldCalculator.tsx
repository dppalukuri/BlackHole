import { useState } from 'preact/hooks';
import { formatCurrency } from '../../../lib/formatters';
import SliderInput from '../ui/SliderInput';

export default function RentalYieldCalculator() {
  const [purchasePrice, setPurchasePrice] = useState(1500000);
  const [annualRent, setAnnualRent] = useState(80000);
  const [serviceCharge, setServiceCharge] = useState(15000);
  const [maintenanceCost, setMaintenanceCost] = useState(5000);
  const [vacancyWeeks, setVacancyWeeks] = useState(2);
  const [dldFeePercent] = useState(4); // Dubai Land Department fee
  const [agentFeePercent, setAgentFeePercent] = useState(2);

  // Costs
  const dldFee = purchasePrice * (dldFeePercent / 100);
  const agentFee = purchasePrice * (agentFeePercent / 100);
  const totalAcquisitionCost = purchasePrice + dldFee + agentFee;

  const effectiveRent = annualRent * ((52 - vacancyWeeks) / 52);
  const netRentalIncome = effectiveRent - serviceCharge - maintenanceCost;

  const grossYield = (annualRent / purchasePrice) * 100;
  const netYield = (netRentalIncome / totalAcquisitionCost) * 100;

  const monthlyIncome = netRentalIncome / 12;
  const yearsToBreakeven = totalAcquisitionCost / netRentalIncome;

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="purchase-price" label="Property Purchase Price" value={purchasePrice} min={200000} max={20000000} step={50000} prefix="AED " onChange={setPurchasePrice} />
        <SliderInput id="annual-rent" label="Expected Annual Rent" value={annualRent} min={10000} max={2000000} step={5000} prefix="AED " onChange={setAnnualRent} />
        <SliderInput id="service-charge" label="Annual Service Charge" value={serviceCharge} min={0} max={100000} step={1000} prefix="AED " onChange={setServiceCharge} />
        <SliderInput id="maintenance" label="Annual Maintenance/Repairs" value={maintenanceCost} min={0} max={50000} step={1000} prefix="AED " onChange={setMaintenanceCost} />
        <SliderInput id="vacancy" label="Vacancy Weeks per Year" value={vacancyWeeks} min={0} max={12} step={1} suffix=" wk" onChange={setVacancyWeeks} />
        <SliderInput id="agent-fee" label="Agent Commission" value={agentFeePercent} min={0} max={5} step={0.5} suffix="%" onChange={setAgentFeePercent} />
      </div>

      {/* Yield Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', margin: '1.5rem 0' }}>
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Gross Yield</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6366f1' }}>{grossYield.toFixed(1)}%</div>
          <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Before expenses</div>
        </div>
        <div style={{ background: netYield >= 5 ? '#f0fdf4' : netYield >= 3 ? '#fffbeb' : '#fef2f2', border: `2px solid ${netYield >= 5 ? '#22c55e' : netYield >= 3 ? '#f59e0b' : '#ef4444'}`, borderRadius: '12px', padding: '1.25rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Net Yield</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: netYield >= 5 ? '#16a34a' : netYield >= 3 ? '#d97706' : '#dc2626' }}>{netYield.toFixed(1)}%</div>
          <div style={{ fontSize: '0.8rem', color: '#64748b' }}>After all costs</div>
        </div>
      </div>

      {/* Detailed Breakdown */}
      <div class="result-card">
        <div class="result-item">
          <span class="result-label">Property Price</span>
          <span class="result-value">{formatCurrency(purchasePrice, 'AED')}</span>
        </div>
        <div class="result-item">
          <span class="result-label">DLD Fee (4%)</span>
          <span class="result-value">+{formatCurrency(dldFee, 'AED')}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Agent Fee ({agentFeePercent}%)</span>
          <span class="result-value">+{formatCurrency(agentFee, 'AED')}</span>
        </div>
        <div class="result-item" style={{ fontWeight: 700 }}>
          <span class="result-label">Total Acquisition Cost</span>
          <span class="result-value">{formatCurrency(totalAcquisitionCost, 'AED')}</span>
        </div>
        <div style={{ height: '0.5rem' }} />
        <div class="result-item">
          <span class="result-label">Effective Annual Rent (adj. for vacancy)</span>
          <span class="result-value">{formatCurrency(effectiveRent, 'AED')}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Annual Expenses (service + maintenance)</span>
          <span class="result-value">-{formatCurrency(serviceCharge + maintenanceCost, 'AED')}</span>
        </div>
        <div class="result-item result-highlight">
          <span class="result-label">Net Monthly Income</span>
          <span class="result-value">{formatCurrency(monthlyIncome, 'AED')}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Breakeven Period</span>
          <span class="result-value">{yearsToBreakeven.toFixed(1)} years</span>
        </div>
      </div>

      {/* Yield Rating */}
      <div class="gratuity-breakdown" style={{ marginTop: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>Dubai Rental Yield Benchmarks</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem', marginTop: '0.5rem' }}>
          <tbody>
            <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={{ padding: '0.5rem' }}>Below 3%</td>
              <td style={{ padding: '0.5rem', color: '#dc2626', fontWeight: 600 }}>Poor — consider other investments</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={{ padding: '0.5rem' }}>3% - 5%</td>
              <td style={{ padding: '0.5rem', color: '#d97706', fontWeight: 600 }}>Average — typical for prime areas</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={{ padding: '0.5rem' }}>5% - 8%</td>
              <td style={{ padding: '0.5rem', color: '#16a34a', fontWeight: 600 }}>Good — above market average</td>
            </tr>
            <tr>
              <td style={{ padding: '0.5rem' }}>8%+</td>
              <td style={{ padding: '0.5rem', color: '#16a34a', fontWeight: 800 }}>Excellent — verify the numbers</td>
            </tr>
          </tbody>
        </table>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.75rem' }}>
          Your net yield of <strong>{netYield.toFixed(1)}%</strong> is {netYield >= 5 ? 'above' : netYield >= 3 ? 'at' : 'below'} the Dubai average of 5-7%.
          {netYield < 3 && ' Consider areas like JVC, Discovery Gardens, or International City for higher yields.'}
        </p>
      </div>
    </div>
  );
}
