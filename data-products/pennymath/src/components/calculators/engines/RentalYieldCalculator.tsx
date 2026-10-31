import { useState } from 'preact/hooks';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import Verdict from '../ui/Verdict';

const DLD_FEE_PERCENT = 4; // Dubai Land Department transfer fee

export default function RentalYieldCalculator() {
  const [purchasePrice, setPurchasePrice] = useState(1500000);
  const [annualRent, setAnnualRent] = useState(80000);
  const [serviceCharge, setServiceCharge] = useState(15000);
  const [maintenanceCost, setMaintenanceCost] = useState(5000);
  const [vacancyWeeks, setVacancyWeeks] = useState(2);
  const [agentFeePercent, setAgentFeePercent] = useState(2);

  const dldFee = purchasePrice * (DLD_FEE_PERCENT / 100);
  const agentFee = purchasePrice * (agentFeePercent / 100);
  const totalAcquisitionCost = purchasePrice + dldFee + agentFee;

  const effectiveRent = annualRent * ((52 - vacancyWeeks) / 52);
  const expenses = serviceCharge + maintenanceCost;
  const netRentalIncome = effectiveRent - expenses;

  const grossYield = (annualRent / purchasePrice) * 100;
  const netYield = (netRentalIncome / totalAcquisitionCost) * 100;
  const yearsToBreakeven = totalAcquisitionCost / netRentalIncome;

  const tone = netYield >= 5 ? 'good' : netYield >= 3 ? 'warn' : 'bad';
  const standing = netYield >= 5 ? 'above' : netYield >= 3 ? 'at or just below' : 'well below';

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="purchase-price" label="Property Purchase Price" value={purchasePrice} min={200000} max={20000000} step={50000} prefix="AED " scalable locale="en-AE" onChange={setPurchasePrice} />
        <SliderInput id="annual-rent" label="Expected Annual Rent" value={annualRent} min={10000} max={2000000} step={5000} prefix="AED " scalable locale="en-AE" onChange={setAnnualRent} />
        <SliderInput id="service-charge" label="Annual Service Charge" value={serviceCharge} min={0} max={100000} step={1000} prefix="AED " scalable locale="en-AE" onChange={setServiceCharge} />
        <SliderInput id="maintenance" label="Annual Maintenance and Repairs" value={maintenanceCost} min={0} max={50000} step={1000} prefix="AED " scalable locale="en-AE" onChange={setMaintenanceCost} />
        <SliderInput id="vacancy" label="Vacancy Weeks per Year" value={vacancyWeeks} min={0} max={12} step={1} suffix=" wk" onChange={setVacancyWeeks} />
        <SliderInput id="agent-fee" label="Agent Commission" value={agentFeePercent} min={0} max={5} step={0.5} suffix="%" onChange={setAgentFeePercent} />
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="AED"
          results={[
            { label: 'Net yield after all costs', value: `${netYield.toFixed(1)}%`, highlight: true },
            { label: 'Gross yield before costs', value: `${grossYield.toFixed(1)}%` },
            { label: 'Net income a month', value: netRentalIncome / 12 },
            { label: 'Rent after vacancy', value: effectiveRent },
            { label: 'Yearly expenses', value: expenses },
            { label: `DLD fee at ${DLD_FEE_PERCENT}%`, value: dldFee },
            { label: `Agent fee at ${agentFeePercent}%`, value: agentFee },
            { label: 'Total cost to buy', value: totalAcquisitionCost },
            { label: 'Years for rent to repay the cost', value: yearsToBreakeven > 0 ? yearsToBreakeven.toFixed(1) : 'Never' },
          ]}
        />
        <Verdict title={`This is ${standing} the 5% often seen as a good net yield`} tone={tone}>
          {netYield < 3 ? 'Areas such as JVC, Discovery Gardens or International City have tended to offer higher yields.' : 'Check service charges for the actual building, since they vary widely.'}
        </Verdict>
      </div>
    </div>
  );
}
