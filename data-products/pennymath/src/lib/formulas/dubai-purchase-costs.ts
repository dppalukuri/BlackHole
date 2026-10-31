export interface DubaiPurchaseInput {
  price: number;
  /** Share of the price borrowed, in percent. 0 means a cash purchase. */
  loanPercent: number;
  useAgent: boolean;
  agentPercent: number;
  bankFeePercent: number;
  valuationFee: number;
  /** Developer NOC and anything else the buyer wants to include. */
  otherCosts: number;
}

export interface CostLine {
  label: string;
  amount: number;
}

export interface DubaiPurchaseResult {
  loan: number;
  downPayment: number;
  costs: CostLine[];
  totalCosts: number;
  /** Down payment plus every cost: the money needed before the keys. */
  cashNeeded: number;
  costsPercentOfPrice: number;
}

const VAT = 1.05;

/** Trustee office fee: lower on properties under AED 500,000, both plus 5% VAT. */
const trusteeFee = (price: number) => (price < 500000 ? 2000 : 4000) * VAT;

/**
 * Upfront costs of buying a ready property in Dubai. The DLD and mortgage
 * registration figures are published charges. Agent, bank and valuation fees
 * are market rates, so the caller passes those in.
 */
export function dubaiPurchaseCosts(input: DubaiPurchaseInput): DubaiPurchaseResult {
  const { price, loanPercent, useAgent, agentPercent, bankFeePercent, valuationFee, otherCosts } = input;
  const loan = (price * loanPercent) / 100;

  const costs: CostLine[] = [
    { label: 'DLD transfer fee (4%)', amount: price * 0.04 },
    { label: 'DLD admin fee', amount: 580 },
    { label: 'Trustee office fee, with VAT', amount: trusteeFee(price) },
  ];
  if (useAgent) {
    costs.push({ label: `Agent commission (${agentPercent}%), with VAT`, amount: ((price * agentPercent) / 100) * VAT });
  }
  if (loan > 0) {
    costs.push({ label: 'Mortgage registration (0.25% + AED 290)', amount: loan * 0.0025 + 290 });
    costs.push({ label: `Bank processing fee (${bankFeePercent}%), with VAT`, amount: ((loan * bankFeePercent) / 100) * VAT });
    costs.push({ label: 'Property valuation', amount: valuationFee });
  }
  if (otherCosts > 0) costs.push({ label: 'Other costs', amount: otherCosts });

  const totalCosts = costs.reduce((sum, c) => sum + c.amount, 0);
  const downPayment = price - loan;

  return {
    loan,
    downPayment,
    costs,
    totalCosts,
    cashNeeded: downPayment + totalCosts,
    costsPercentOfPrice: price > 0 ? (totalCosts / price) * 100 : 0,
  };
}
