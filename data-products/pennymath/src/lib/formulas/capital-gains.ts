export type CapitalAsset = 'equity' | 'debt-fund' | 'property' | 'other';

/** Yearly tax-free allowance on long-term gains from listed equity and equity funds. */
export const EQUITY_LTCG_EXEMPTION = 125000;
const CESS = 0.04;

/** Cost Inflation Index by the financial year it starts in (2001 = FY 2001-02). */
export const COST_INFLATION_INDEX: Record<number, number> = {
  2001: 100, 2002: 105, 2003: 109, 2004: 113, 2005: 117, 2006: 122, 2007: 129, 2008: 137, 2009: 148,
  2010: 167, 2011: 184, 2012: 200, 2013: 220, 2014: 240, 2015: 254, 2016: 264, 2017: 272, 2018: 280,
  2019: 289, 2020: 301, 2021: 317, 2022: 331, 2023: 348, 2024: 363, 2025: 376, 2026: 384,
};

export interface CapitalGainsInput {
  asset: CapitalAsset;
  purchaseValue: number;
  saleValue: number;
  /** Brokerage, stamp duty, improvements and other allowable costs. */
  expenses: number;
  holdingMonths: number;
  /** Your income tax slab, in percent, for gains taxed at slab rates. */
  slabRate: number;
  /** Equity only: how much of the yearly allowance is still unused. */
  exemptionAvailable: number;
  /** Property only: a resident's option on land or buildings bought before 23 July 2024. */
  indexationEligible: boolean;
  purchaseFyStart: number;
  saleFyStart: number;
}

export interface CapitalGainsResult {
  term: 'short' | 'long';
  gain: number;
  exemptionUsed: number;
  taxableGain: number;
  /** The rate applied to the taxable gain, in percent. */
  rate: number;
  tax: number;
  cess: number;
  totalTax: number;
  netProceeds: number;
  /** Set when the indexed route was available, whichever one won. */
  indexation: {
    indexedCost: number;
    indexedGain: number;
    taxAt20: number;
    taxAt12Point5: number;
    used: boolean;
  } | null;
}

const LONG_TERM_MONTHS: Record<CapitalAsset, number> = { equity: 12, 'debt-fund': Infinity, property: 24, other: 24 };

/**
 * Tax on one sale, under the post-23 July 2024 rules. Covers cess but not
 * surcharge, set-off of losses or reinvestment exemptions such as Section 54.
 *
 * A sale at a loss owes no tax here. "debt-fund" means funds bought on or after 1 April 2023, taxed at slab rates
 * however long they are held.
 */
export function capitalGainsTax(input: CapitalGainsInput): CapitalGainsResult {
  const { asset, purchaseValue, saleValue, expenses, holdingMonths, slabRate } = input;
  const gain = saleValue - purchaseValue - expenses;
  const term = holdingMonths > LONG_TERM_MONTHS[asset] ? 'long' : 'short';
  const positiveGain = Math.max(0, gain);

  let exemptionUsed = 0;
  let taxableGain = positiveGain;
  let rate = slabRate;
  let tax: number;
  let indexation: CapitalGainsResult['indexation'] = null;

  if (asset === 'equity' && term === 'short') {
    rate = 20;
    tax = positiveGain * 0.2;
  } else if (asset === 'equity') {
    exemptionUsed = Math.min(positiveGain, Math.max(0, input.exemptionAvailable));
    taxableGain = positiveGain - exemptionUsed;
    rate = 12.5;
    tax = taxableGain * 0.125;
  } else if (term === 'short' || asset === 'debt-fund') {
    tax = (positiveGain * slabRate) / 100;
  } else {
    rate = 12.5;
    tax = positiveGain * 0.125;

    if (asset === 'property' && input.indexationEligible) {
      const indexedCost =
        purchaseValue * (COST_INFLATION_INDEX[input.saleFyStart] / COST_INFLATION_INDEX[input.purchaseFyStart]);
      const indexedGain = Math.max(0, saleValue - indexedCost - expenses);
      const taxAt20 = indexedGain * 0.2;
      const used = taxAt20 < tax;
      indexation = { indexedCost, indexedGain, taxAt20, taxAt12Point5: tax, used };
      if (used) {
        rate = 20;
        taxableGain = indexedGain;
        tax = taxAt20;
      }
    }
  }

  const cess = tax * CESS;
  const totalTax = tax + cess;
  return {
    term,
    gain,
    exemptionUsed,
    taxableGain,
    rate,
    tax,
    cess,
    totalTax,
    netProceeds: saleValue - expenses - totalTax,
    indexation,
  };
}
