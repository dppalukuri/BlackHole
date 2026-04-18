/**
 * Build-time loader for the visa data JSON files.
 * Files live in public/data/ (shipped as static assets AND readable from disk
 * at build). We use node fs to pull them in for Astro SSG pages.
 */
import fs from 'node:fs';
import path from 'node:path';

const dataDir = path.resolve(process.cwd(), 'public', 'data');

function loadJson<T>(file: string): T {
  const full = path.join(dataDir, file);
  return JSON.parse(fs.readFileSync(full, 'utf-8')) as T;
}

/** Per-passport visa requirement to every destination country. */
export type VisaStatus = 'vf' | 'voa' | 'ev' | 'eta' | 'vr' | 'na' | number;
export type VisaMatrix = Record<string, Record<string, VisaStatus>>;

export interface ResidencePermit {
  source: string;
  last_verified: string;
  exemptions: Record<string, {
    access: 'vf' | 'voa' | 'ev' | 'eta';
    days: number | string;
    source: string;
    note?: string;
  }>;
}

export const countries: string[] = loadJson<string[]>('countries.json');
export const visaMatrix: VisaMatrix = loadJson<VisaMatrix>('visa-matrix.json');
export const residencePermits: Record<string, ResidencePermit> = loadJson('residence-permits.json');

/**
 * Curated, government-sourced visa data produced by the visa-verifier agent.
 * Optional — if the file is missing, we fall back to the bulk matrix alone.
 */
export interface VerifiedEntry {
  status: 'vf' | 'voa' | 'ev' | 'eta' | 'vr' | 'unknown';
  days: number | null;
  source: string | null;
  notes: string;
  confidence: 'high' | 'medium' | 'low' | 'unknown';
  verified_at: string;
  model: string;
}
export interface VerifiedData {
  meta?: Record<string, unknown>;
  data: Record<string, Record<string, VerifiedEntry>>;
}

function loadVerified(): VerifiedData {
  const fp = path.join(dataDir, 'verified-visas.json');
  if (!fs.existsSync(fp)) return { data: {} };
  try {
    return JSON.parse(fs.readFileSync(fp, 'utf-8')) as VerifiedData;
  } catch {
    return { data: {} };
  }
}
export const verifiedData: VerifiedData = loadVerified();

/** Look up a single verified entry, or null if absent/unknown. */
export function getVerified(passport: string, destination: string): VerifiedEntry | null {
  const e = verifiedData.data?.[passport]?.[destination];
  if (!e) return null;
  if (e.status === 'unknown' || e.confidence === 'unknown') return null;
  return e;
}

/** Human-readable label for a visa status code or day-count. */
export function statusLabel(s: VisaStatus): string {
  if (typeof s === 'number') return `Visa-free (${s} days)`;
  switch (s) {
    case 'vf': return 'Visa-free';
    case 'voa': return 'Visa on arrival';
    case 'ev': return 'e-Visa';
    case 'eta': return 'ETA required';
    case 'vr': return 'Visa required';
    case 'na': return 'Not applicable / travel banned';
    default: return String(s);
  }
}

/** CSS class (maps to existing .status-vf / .status-voa etc. rules). */
export function statusClass(s: VisaStatus): string {
  if (typeof s === 'number') return 'status-vf';
  switch (s) {
    case 'vf': return 'status-vf';
    case 'voa': return 'status-voa';
    case 'ev':
    case 'eta': return 'status-ev';
    case 'vr': return 'status-vr';
    default: return '';
  }
}

/** Broad categorisation for grouping. */
export function statusBucket(s: VisaStatus): 'visa-free' | 'voa-eta' | 'evisa' | 'required' | 'other' {
  if (typeof s === 'number') return 'visa-free';
  if (s === 'vf') return 'visa-free';
  if (s === 'voa' || s === 'eta') return 'voa-eta';
  if (s === 'ev') return 'evisa';
  if (s === 'vr') return 'required';
  return 'other';
}

export interface PassportSummary {
  passport: string;
  total: number;
  visaFree: string[];
  voaEta: string[];
  eVisa: string[];
  visaRequired: string[];
  daysByCountry: Record<string, number | undefined>;
}

/** Aggregate visa access for a passport. */
export function summarizePassport(passport: string): PassportSummary {
  const row = visaMatrix[passport] ?? {};
  const out: PassportSummary = {
    passport,
    total: 0,
    visaFree: [],
    voaEta: [],
    eVisa: [],
    visaRequired: [],
    daysByCountry: {},
  };
  for (const [dest, st] of Object.entries(row)) {
    out.total++;
    if (typeof st === 'number') {
      out.visaFree.push(dest);
      out.daysByCountry[dest] = st;
    } else if (st === 'vf') {
      out.visaFree.push(dest);
    } else if (st === 'voa' || st === 'eta') {
      out.voaEta.push(dest);
    } else if (st === 'ev') {
      out.eVisa.push(dest);
    } else if (st === 'vr') {
      out.visaRequired.push(dest);
    }
  }
  [out.visaFree, out.voaEta, out.eVisa, out.visaRequired].forEach(arr => arr.sort());
  return out;
}

/** Safer slug → passport-name resolver. */
export function passportFromSlug(slug: string): string | null {
  const normalized = slug.toLowerCase().replace(/-passport$/, '').replace(/-/g, ' ');
  // Try exact match (case-insensitive) against known passports
  for (const p of Object.keys(visaMatrix)) {
    if (p.toLowerCase() === normalized) return p;
  }
  // Try common aliases
  const aliases: Record<string, string> = {
    'uk': 'United Kingdom',
    'british': 'United Kingdom',
    'us': 'United States',
    'american': 'United States',
    'uae': 'United Arab Emirates',
    'emirati': 'United Arab Emirates',
    'indian': 'India',
    'canadian': 'Canada',
    'australian': 'Australia',
    'japanese': 'Japan',
    'singaporean': 'Singapore',
    'german': 'Germany',
    'french': 'France',
  };
  return aliases[normalized] ?? null;
}
