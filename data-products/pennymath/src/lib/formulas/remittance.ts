export interface RemittanceProvider {
  name: string;
  /** Rupees paid per dirham by this provider. */
  rate: number;
  /** Transfer fee in dirhams, including any VAT, paid on top of the amount sent. */
  fee: number;
}

export interface RemittanceQuote extends RemittanceProvider {
  totalPaid: number;
  received: number;
  /** Rupees received per dirham actually paid, fee included. */
  effectiveRate: number;
  /** Rupees lost against converting everything you paid at the mid-market rate. */
  costInr: number;
  /** That cost as a share of the mid-market value of what you paid. */
  costPercent: number;
  isBest: boolean;
}

/**
 * Compares transfers of the same amount by the rupees received per dirham paid,
 * since a good rate can hide a high fee, and a "zero fee" can hide a poor rate.
 */
export function compareRemittance(amount: number, midRate: number, providers: RemittanceProvider[]): RemittanceQuote[] {
  const quotes = providers.map((p) => {
    const totalPaid = amount + p.fee;
    const received = amount * p.rate;
    const fair = totalPaid * midRate;
    return {
      ...p,
      totalPaid,
      received,
      effectiveRate: totalPaid > 0 ? received / totalPaid : 0,
      costInr: fair - received,
      costPercent: fair > 0 ? ((fair - received) / fair) * 100 : 0,
      isBest: false,
    };
  });
  const best = Math.max(...quotes.map((q) => q.effectiveRate));
  return quotes.map((q) => ({ ...q, isBest: q.effectiveRate === best }));
}
