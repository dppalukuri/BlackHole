/**
 * Centralized affiliate links.
 *
 * HOW TO USE: replace each `url: '#'` with your real tracking URL from the
 * partner's affiliate dashboard. Keep the `rel: 'nofollow sponsored'` attribute
 * intact — it's required by Google and by affiliate program ToS.
 *
 * The `disclosure` string is shown under every CTA for transparency / legal.
 */

export interface AffiliatePartner {
  name: string;
  url: string;
  country: 'IN' | 'UAE' | 'US' | 'GLOBAL';
  category: 'broker' | 'bank' | 'insurance' | 'wealth' | 'tax';
  blurb: string;   // 1-sentence sales angle
  cta: string;     // button label
}

/** India — brokers / mutual fund platforms */
export const GROWW: AffiliatePartner = {
  name: 'Groww',
  url: '#',  // TODO: replace with your Groww affiliate URL
  country: 'IN',
  category: 'broker',
  blurb: 'Zero-commission direct mutual funds. Free demat + trading account.',
  cta: 'Open free Groww account',
};

export const ZERODHA: AffiliatePartner = {
  name: 'Zerodha',
  url: '#',  // TODO: replace with your Zerodha affiliate URL
  country: 'IN',
  category: 'broker',
  blurb: 'India\'s largest broker. Flat ₹20/trade, free equity delivery.',
  cta: 'Open free Zerodha account',
};

export const ET_MONEY: AffiliatePartner = {
  name: 'ET Money',
  url: '#',  // TODO: replace with your ET Money affiliate URL
  country: 'IN',
  category: 'wealth',
  blurb: 'Paperless SIP, free portfolio tracker, direct funds with no commission.',
  cta: 'Start SIP on ET Money',
};

/** UAE — banks / wealth managers */
export const SARWA: AffiliatePartner = {
  name: 'Sarwa',
  url: '#',  // TODO: replace with your Sarwa affiliate URL
  country: 'UAE',
  category: 'wealth',
  blurb: 'UAE\'s regulated robo-advisor. Globally diversified portfolios, from AED 500.',
  cta: 'Get started with Sarwa',
};

/** US — retirement / investing platforms */
export const BETTERMENT: AffiliatePartner = {
  name: 'Betterment',
  url: '#',  // TODO: replace with your Betterment affiliate URL
  country: 'US',
  category: 'wealth',
  blurb: 'Automated investing for retirement. $10 minimum, low fees, tax-loss harvesting.',
  cta: 'Open a Betterment account',
};

export const FIDELITY: AffiliatePartner = {
  name: 'Fidelity',
  url: '#',  // TODO: replace with your Fidelity affiliate URL
  country: 'US',
  category: 'broker',
  blurb: 'Zero-fee index funds, $0 stock commissions, strong 401(k) rollover support.',
  cta: 'Open a Fidelity account',
};

/** Default disclosure shown under every CTA */
export const DISCLOSURE =
  'We may earn a commission if you sign up through our links — at no extra cost to you. ' +
  'This helps us keep every calculator on CalcStack free. ' +
  'Affiliate relationships never influence our rankings or calculator results.';

/**
 * Choose the best affiliate partner for a given calculator.
 * Falls back to the first-listed partner for that country if no category match.
 */
export function pickAffiliate(args: {
  country: 'IN' | 'UAE' | 'US';
  category: AffiliatePartner['category'];
}): AffiliatePartner {
  const all: AffiliatePartner[] = [GROWW, ZERODHA, ET_MONEY, SARWA, BETTERMENT, FIDELITY];
  return (
    all.find((p) => p.country === args.country && p.category === args.category) ??
    all.find((p) => p.country === args.country) ??
    GROWW
  );
}
