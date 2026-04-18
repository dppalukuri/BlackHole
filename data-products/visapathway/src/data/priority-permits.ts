/**
 * Residence permit pages to generate.
 * Each entry maps a URL slug to a key in residence-permits.json plus
 * per-permit copy for the hero + FAQ.
 */

export interface PriorityPermit {
  slug: string;
  permitKey: string;
  shortName: string;
  fullName: string;
  blurb: string;
  audience: string;   // who typically holds this (for SEO keyword hints)
}

export const priorityPermits: PriorityPermit[] = [
  {
    slug: 'schengen-residence-permit-benefits',
    permitKey: 'Schengen Residence Permit',
    shortName: 'Schengen residence permit',
    fullName: 'Schengen Residence Permit',
    blurb:
      'Holders of a Schengen residence permit (issued by any of the 27 Schengen-area countries) get bonus visa-free or visa-on-arrival access to destinations outside the Schengen zone.',
    audience: 'expats, students, and workers living in France, Germany, Italy, Spain, Netherlands or any other Schengen country',
  },
  {
    slug: 'uk-residence-permit-benefits',
    permitKey: 'UK Residence Permit (BRP)',
    shortName: 'UK residence permit',
    fullName: 'UK Biometric Residence Permit (BRP)',
    blurb:
      'A valid UK Biometric Residence Permit (BRP) — or the newer eVisa — unlocks easier entry to several countries outside the UK, on top of what your home passport provides.',
    audience: 'holders of skilled-worker, student, family, or settlement visas in the UK',
  },
  {
    slug: 'canada-pr-travel-benefits',
    permitKey: 'Canada Permanent Resident',
    shortName: 'Canadian permanent resident',
    fullName: 'Canada Permanent Resident Card',
    blurb:
      'A Canadian Permanent Resident (PR) card grants easier travel access to several countries beyond what your original passport offers.',
    audience: 'Canadian PR cardholders',
  },
  {
    slug: 'valid-us-visa-benefits',
    permitKey: 'Valid US Visa (B1/B2)',
    shortName: 'valid US visa',
    fullName: 'valid US B1/B2 visa',
    blurb:
      'A valid US B1/B2 visa (tourist / business) grants easier entry to several countries that respect US visa holders — even if the visa has never been used.',
    audience: 'holders of an unexpired US B1/B2 visa',
  },
  {
    slug: 'valid-schengen-visa-benefits',
    permitKey: 'Valid Schengen Visa',
    shortName: 'valid Schengen visa',
    fullName: 'valid Schengen visa',
    blurb:
      'A valid Schengen visa (C-type short-stay) grants easier entry to several non-Schengen countries like Turkey, Georgia, and several Balkan nations.',
    audience: 'holders of an unexpired Schengen C-visa',
  },
];
