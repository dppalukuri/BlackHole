import { useState, useEffect, useRef } from 'preact/hooks';
import { countrySlug } from '../lib/slug';
import { isSchengen } from '../lib/schengen';

/** What each passport needs to enter one destination. */
interface DestinationColumn { [passport: string]: string | number }
interface PermitExemption { access: string; days?: number; source: string; note?: string; }
interface ResidencePermitData {
  [permit: string]: {
    source: string; last_verified: string;
    exemptions: { [country: string]: PermitExemption };
  };
}

const SCHENGEN_VISA = {
  text: 'Schengen visa needed',
  detail: 'Apply for a Schengen short-stay visa at the embassy or visa centre of the Schengen country where you will spend the most time. One Schengen visa covers all 29 Schengen countries, for up to 90 days in any 180.',
  action: 'Apply up to six months before you travel, and at least 15 days before. A decision usually takes about 15 days.',
  color: '#EF6F6C', bg: 'rgba(239,111,108,.1)', border: '#EF6F6C', icon: '✗', priority: 5,
};

function statusInfo(code: string | number, destination: string) {
  if (code === 'vr' && isSchengen(destination)) return SCHENGEN_VISA;
  if (typeof code === 'number') return {
    text: `Visa-free entry`,
    detail: `You can enter and stay for up to ${code} days. No visa application needed — just show your passport at immigration.`,
    action: 'No action needed before travel.',
    color: '#4CC38A', bg: 'rgba(76,195,138,.1)', border: '#4CC38A', icon: '✓', priority: 1,
  };
  const map: Record<string, any> = {
    'vf':  { text: 'Visa-free entry', detail: 'No visa needed. Present your passport at immigration on arrival.', action: 'No action needed before travel.', color: '#4CC38A', bg: 'rgba(76,195,138,.1)', border: '#4CC38A', icon: '✓', priority: 1 },
    'voa': { text: 'Visa on arrival', detail: 'You can get a visa stamp at the airport when you land. Bring cash (USD) for the visa fee, a passport photo, and proof of return ticket.', action: 'No pre-application needed. Get visa at the airport on arrival.', color: '#E5B454', bg: 'rgba(229,180,84,.1)', border: '#E5B454', icon: '↓', priority: 2 },
    'eta': { text: 'Electronic Travel Authorization (ETA)', detail: 'You must apply online before traveling. It is a quick digital approval — not a full visa application.', action: 'Apply online before your flight. Usually approved in 24-72 hours.', color: '#8C9BFF', bg: 'rgba(140,155,255,.12)', border: '#8C9BFF', icon: '→', priority: 3 },
    'ev':  { text: 'e-Visa required', detail: 'You must apply for an electronic visa online before traveling. Upload documents and pay the fee on the official portal.', action: 'Apply on the official e-Visa portal before your flight. Processing: 2-5 business days.', color: '#8C9BFF', bg: 'rgba(140,155,255,.12)', border: '#8C9BFF', icon: '→', priority: 4 },
    'vr':  { text: 'Visa required (apply at embassy)', detail: 'You need to apply for a visa at the embassy or consulate before traveling. This usually requires an in-person visit or submission through a visa center.', action: 'Apply at the nearest embassy/consulate or authorized visa center. Allow 1-4 weeks for processing.', color: '#EF6F6C', bg: 'rgba(239,111,108,.1)', border: '#EF6F6C', icon: '✗', priority: 5 },
    'na':  { text: 'Entry not permitted', detail: 'Entry is not allowed with this travel document.', action: 'Contact the embassy for exceptional circumstances.', color: '#A9ABBC', bg: 'rgba(169,171,188,.12)', border: '#A9ABBC', icon: '–', priority: 6 },
  };
  return map[code] || { text: `Visa-free (${code} days)`, detail: `You can enter and stay for up to ${code} days.`, action: 'No action needed before travel.', color: '#4CC38A', bg: 'rgba(76,195,138,.1)', border: '#4CC38A', icon: '✓', priority: 1 };
}

function Autocomplete({ items, placeholder, onSelect, id }: {
  items: string[]; placeholder: string; onSelect: (v: string) => void; id: string;
}) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const filtered = query.length >= 1 ? items.filter(c => c.toLowerCase().includes(query.toLowerCase())).slice(0, 6) : [];

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const select = (item: string) => { onSelect(item); setQuery(''); setOpen(false); };

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <input id={id} type="text" value={query} placeholder={placeholder}
        onInput={(e) => { setQuery((e.target as HTMLInputElement).value); setOpen(true); }}
        onFocus={() => query.length >= 1 && setOpen(true)}
        autocomplete="off"
        style={{ width: '100%', padding: '0.7rem 1rem', border: '2px solid var(--border)', borderRadius: '10px', fontSize: '1rem', fontFamily: 'inherit', background: 'var(--input)', color: 'var(--text)' }}
      />
      {open && filtered.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--surface-2)',
          border: '1px solid var(--border)', borderRadius: '0 0 10px 10px', boxShadow: '0 16px 40px rgba(0,0,0,0.5)',
          zIndex: 50, maxHeight: '240px', overflowY: 'auto',
        }}>
          {filtered.map(item => (
            <div key={item} onClick={() => select(item)}
              style={{ padding: '0.65rem 1rem', cursor: 'pointer', fontSize: '0.95rem', borderBottom: '1px solid var(--border)' }}
              onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.background = 'var(--button)'}
              onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.background = 'transparent'}>
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const PRESETS = [
  { label: 'Indian + UAE Resident', passports: ['India'], permits: ['UAE Residence Permit'] },
  { label: 'Indian + US Visa', passports: ['India'], permits: ['Valid US Visa (B1/B2)'] },
  { label: 'Indian + Schengen Visa', passports: ['India'], permits: ['Valid Schengen Visa'] },
  { label: 'Pakistani + UAE Resident', passports: ['Pakistan'], permits: ['UAE Residence Permit'] },
  { label: 'Nigerian + US Green Card', passports: ['Nigeria'], permits: ['US Green Card (Permanent Resident)'] },
  { label: 'Filipino + UAE Resident', passports: ['Philippines'], permits: ['UAE Residence Permit'] },
];

// The country list and permits are small, so the page carries them and the checker
// is usable straight away. Visa rules are fetched for one destination once it is picked.
export default function VisaChecker({ countries, permits }: { countries: string[]; permits: ResidencePermitData }) {
  const [column, setColumn] = useState<{ destination: string; data: DestinationColumn } | null>(null);
  const columnCache = useRef(new Map<string, DestinationColumn>());
  const [passports, setPassports] = useState<string[]>([]);
  const [selectedPermits, setSelectedPermits] = useState<string[]>([]);
  const [destination, setDestination] = useState('');

  const [copyState, setCopyState] = useState<'idle' | 'copied'>('idle');
  const [reportState, setReportState] = useState<'idle' | 'copied'>('idle');

  useEffect(() => {
    if (!destination) { setColumn(null); return; }
    const cached = columnCache.current.get(destination);
    if (cached) { setColumn({ destination, data: cached }); return; }
    let current = true;
    fetch(`/data/destinations/${countrySlug(destination)}.json`)
      .then(r => (r.ok ? r.json() : {}))
      .catch(() => ({}))
      .then((data: DestinationColumn) => {
        columnCache.current.set(destination, data);
        if (current) setColumn({ destination, data });
      });
    return () => { current = false; };
  }, [destination]);

  // Hydrate state from URL query params, once data is loaded.
  // BUG-FIX: do NOT use `||=` here — it short-circuits, so if `p` was applied,
  // `perm` would be skipped silently. Each tryApply must run independently.
  // Also: if there are NO URL params at all, give a clean slate (no localStorage
  // restore) — users expect a logo-click / direct-load to be a fresh checker,
  // not the previous session.
  useEffect(() => {
    const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
    const urlP = params.get('p');
    const urlR = params.get('perm');
    const urlD = params.get('d');
    const hasAnyUrlParam = !!(urlP || urlR || urlD);

    const tryApply = (raw: string | null, set: (v: string[]) => void, valid: string[]) => {
      if (!raw) return false;
      const picks = raw.split(',').map(s => decodeURIComponent(s.trim())).filter(v => valid.includes(v));
      if (picks.length) { set(picks); return true; }
      return false;
    };

    if (hasAnyUrlParam) {
      // Apply each independently — no short-circuit.
      tryApply(urlP, setPassports, countries);
      tryApply(urlR, setSelectedPermits, Object.keys(permits));
      if (urlD && countries.includes(urlD)) setDestination(urlD);
    }
    // Clean URL (no params): leave state empty. localStorage hydration
    // intentionally removed — users expect a fresh checker on direct load.
  }, []);

  // Mirror state → URL so a manually-built selection produces a shareable link.
  // localStorage writes intentionally removed (see comment on hydration effect).
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams();
    if (passports.length) params.set('p', passports.map(encodeURIComponent).join(','));
    if (selectedPermits.length) params.set('perm', selectedPermits.map(encodeURIComponent).join(','));
    if (destination) params.set('d', destination);
    const qs = params.toString();
    const nextUrl = window.location.pathname + (qs ? '?' + qs : '');
    if (window.location.pathname + window.location.search !== nextUrl) {
      window.history.replaceState(null, '', nextUrl);
    }
  }, [passports, selectedPermits, destination]);

  const copyShareLink = async () => {
    if (typeof window === 'undefined') return;
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopyState('copied');
      setTimeout(() => setCopyState('idle'), 2000);
    } catch {
      // Fallback: select + prompt
      prompt('Copy this link to share:', window.location.href);
    }
  };

  const resetAll = () => {
    setPassports([]);
    setSelectedPermits([]);
    setDestination('');
    try {
      localStorage.removeItem('vp.passports');
      localStorage.removeItem('vp.permits');
    } catch {}
  };

  const addPassport = (p: string) => {
    if (p && countries.includes(p) && !passports.includes(p)) setPassports([...passports, p]);
  };
  const removePassport = (p: string) => setPassports(passports.filter(x => x !== p));

  const togglePermit = (p: string) => {
    if (selectedPermits.includes(p)) setSelectedPermits(selectedPermits.filter(x => x !== p));
    else setSelectedPermits([...selectedPermits, p]);
  };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setPassports(preset.passports);
    setSelectedPermits(preset.permits);
  };

  const setDest = (d: string) => { if (countries.includes(d)) setDestination(d); };

  const getResults = () => {
    if (!destination || passports.length === 0 || column?.destination !== destination) return null;
    const results: Array<{
      document: string; requirement: string | number;
      info: ReturnType<typeof statusInfo>; source?: string; note?: string;
    }> = [];

    for (const passport of passports) {
      const req = column.data[passport];
      if (req !== undefined) results.push({ document: `${passport} passport`, requirement: req, info: statusInfo(req, destination) });
    }
    if (permits) {
      for (const permit of selectedPermits) {
        const data = permits[permit];
        if (data?.exemptions?.[destination]) {
          const ex = data.exemptions[destination];
          // Use ex.days as the lookup key ONLY when access is actually visa-free.
          // For voa / ev / eta / vr, ex.access is authoritative — ex.days is just
          // the max-stay and must not be mistaken for "visa-free for N days".
          const key = ex.access === 'vf' && typeof ex.days === 'number' ? ex.days : ex.access;
          results.push({ document: permit, requirement: ex.access, info: statusInfo(key, destination), source: ex.source, note: ex.note });
        } else if (/schengen/i.test(permit) && isSchengen(destination)) {
          // A Schengen visa or residence permit is itself the entry document for the whole area.
          results.push({ document: permit, requirement: 'vf', info: {
            ...statusInfo('vf', destination),
            text: 'No other visa needed',
            detail: `Your ${/residence/i.test(permit) ? 'Schengen residence permit' : 'Schengen visa'} covers ${destination}, like every Schengen country. Short stays are limited to 90 days in any 180 days across the Schengen area.`,
            action: 'Carry your passport and your Schengen visa or residence permit.',
          } });
        }
      }
    }
    results.sort((a, b) => a.info.priority - b.info.priority);
    return results;
  };

  const results = getResults();
  const best = results?.[0];
  const checking = passports.length > 0 && !!destination && column?.destination !== destination;

  return (
    <div>
      {/* Step 1 */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.75rem', marginBottom: '1rem', boxShadow: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ background: 'var(--button)', color: 'white', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>1</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>What passports do you hold?</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Add all your citizenships. We'll check each one.</div>
          </div>
        </div>
        <Autocomplete id="passport-search" items={countries.filter(c => !passports.includes(c))} placeholder="Start typing a country name..." onSelect={addPassport} />
        {passports.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
            {passports.map(p => (
              <span key={p} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'var(--primary-soft)', color: 'var(--primary)', padding: '0.35rem 0.85rem', borderRadius: '999px', fontSize: '0.85rem', fontWeight: 600 }}>
                {p} <button onClick={() => removePassport(p)} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '1.1rem', lineHeight: 1, padding: 0 }}>&times;</button>
              </span>
            ))}
          </div>
        )}
        {passports.length === 0 && (
          <div style={{ marginTop: '1rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.5rem', fontWeight: 600 }}>Quick start — pick your profile:</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {PRESETS.map(p => (
                <button key={p.label} onClick={() => applyPreset(p)}
                  style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.4rem 0.8rem', fontSize: '0.8rem', cursor: 'pointer', color: 'var(--text-2)', fontFamily: 'inherit' }}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Step 2 */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.75rem', marginBottom: '1rem', boxShadow: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ background: 'var(--button)', color: 'white', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>2</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>Any additional visas or permits?</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>These can unlock extra countries. Tap all that apply.</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '0.5rem' }}>
          {permits && Object.keys(permits).map(p => {
            const on = selectedPermits.includes(p);
            return (
              <button key={p} onClick={() => togglePermit(p)}
                style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.65rem 0.9rem', border: `2px solid ${on ? 'var(--primary)' : 'var(--border)'}`, background: on ? 'var(--primary-soft)' : 'transparent', borderRadius: '10px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: on ? 700 : 500, color: on ? 'var(--primary)' : 'var(--text-2)', fontFamily: 'inherit', textAlign: 'left' }}>
                <span style={{ width: '20px', height: '20px', borderRadius: '4px', flexShrink: 0, border: `2px solid ${on ? 'var(--button)' : 'var(--border-strong)'}`, background: on ? 'var(--button)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.7rem', fontWeight: 700 }}>{on ? '✓' : ''}</span>
                {p}
              </button>
            );
          })}
        </div>
      </div>

      {/* Step 3 */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.75rem', marginBottom: '1.5rem', boxShadow: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ background: passports.length > 0 ? 'var(--button)' : 'var(--border-strong)', color: 'white', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>3</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>Where do you want to go?</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>We'll find the best document to use for entry.</div>
          </div>
        </div>
        <Autocomplete id="dest-search" items={countries} placeholder="Start typing a destination..." onSelect={setDest} />
        {destination && (
          <div style={{ marginTop: '0.5rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'var(--primary-soft)', color: 'var(--primary)', padding: '0.35rem 0.85rem', borderRadius: '999px', fontSize: '0.85rem', fontWeight: 600 }}>
              {destination} <button onClick={() => setDestination('')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '1.1rem', lineHeight: 1, padding: 0 }}>&times;</button>
            </span>
          </div>
        )}
      </div>

      {/* Results */}
      {best && destination && (
        <>
          <div style={{ background: best.info.bg, border: `2px solid ${best.info.border}`, borderRadius: '16px', padding: '2rem', marginBottom: '1rem', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '0.85rem', right: '0.85rem', display: 'flex', gap: '0.35rem' }}>
              <button onClick={copyShareLink} title="Copy a shareable link that reopens this query"
                style={{ padding: '0.4rem 0.7rem', border: '1px solid var(--border-strong)', background: 'transparent', borderRadius: '8px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-2)', fontFamily: 'inherit', display: 'inline-flex', alignItems: 'center', gap: '.35rem' }}>
                {copyState === 'copied' ? '✓ Copied!' : 'Share'}
              </button>
              <button onClick={resetAll} title="Clear passports, permits, and destination"
                style={{ padding: '0.4rem 0.7rem', border: '1px solid var(--border-strong)', background: 'transparent', borderRadius: '8px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: 'var(--muted)', fontFamily: 'inherit' }}>
                Reset
              </button>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.25rem' }}>{best.info.icon}</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: best.info.color }}>{best.info.text}</div>
              <div style={{ color: 'var(--text-2)', marginTop: '0.5rem', fontSize: '1.05rem' }}>
                Use your <strong>{best.document}</strong> to enter <strong>{destination}</strong>
              </div>
            </div>
            <div style={{ marginTop: '1.25rem', padding: '1rem', background: 'rgba(21,22,30,.45)', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-2)', lineHeight: 1.7 }}>{best.info.detail}</div>
              {best.note && <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '0.5rem', fontStyle: 'italic', borderLeft: '3px solid var(--border)', paddingLeft: '0.75rem' }}>{best.note}</div>}
              <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.8rem', background: 'var(--surface-2)', borderRadius: '8px', fontSize: '0.85rem' }}>
                <strong style={{ color: 'var(--text-2)' }}>What to do: </strong>
                <span style={{ color: 'var(--text-2)' }}>{best.info.action}</span>
              </div>
              {best.source && <div style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}><a href={best.source} target="_blank" rel="noopener">View official source</a></div>}
            </div>
          </div>

          {results!.length > 1 && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.5rem', marginBottom: '1rem' }}>
              <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem' }}>All your options for {destination}</h3>
              <table class="results-table">
                <thead><tr><th>Document</th><th>Access</th><th>Source</th></tr></thead>
                <tbody>
                  {results!.map((r, i) => (
                    <tr key={i} style={{ background: i === 0 ? 'rgba(76,195,138,.1)' : 'transparent' }}>
                      <td style={{ fontWeight: i === 0 ? 700 : 400 }}>{r.document} {i === 0 && <span style={{ color: 'var(--good)', fontSize: '0.75rem' }}>BEST</span>}</td>
                      <td><span style={{ color: r.info.color, fontWeight: 600 }}>{r.info.text}</span></td>
                      <td>{r.source ? <a href={r.source} target="_blank" rel="noopener" style={{ fontSize: '0.8rem' }}>Official</a> : <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Passport Index</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Report incorrect info */}
          <div style={{
            background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px',
            padding: '1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center',
            justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap',
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Is this information incorrect?</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                {reportState === 'copied'
                  ? <span style={{ color: 'var(--good)' }}>Copied to clipboard — paste into your email to <strong>palukuri.biz@gmail.com</strong></span>
                  : <>Help us improve — report wrong visa info and we'll verify and fix it.</>}
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                const subject = `[WanderWise] Incorrect visa info: ${passports.join(', ')} → ${destination}`;
                const body = `Hi,\n\nThe visa information shown for the following combination appears to be incorrect:\n\nPassports: ${passports.join(', ')}\nAdditional documents: ${selectedPermits.join(', ') || 'None'}\nDestination: ${destination}\nResult shown: ${best?.info.text} (via ${best?.document})\n\nWhat is the correct information:\n[Please describe the correct visa requirement and how you know — e.g., personal experience, embassy website, etc.]\n\nThank you!`;
                const fullText = `To: palukuri.biz@gmail.com\nSubject: ${subject}\n\n${body}`;
                // Copy to clipboard so user can always paste — this works regardless of email-client setup
                if (typeof navigator !== 'undefined' && navigator.clipboard) {
                  navigator.clipboard.writeText(fullText).then(() => {
                    setReportState('copied');
                    setTimeout(() => setReportState('idle'), 4000);
                  }).catch(() => {});
                } else {
                  setReportState('copied');
                  setTimeout(() => setReportState('idle'), 4000);
                }
                // Also try to open the user's email client (works if a default mailto handler is configured)
                const mailto = `mailto:palukuri.biz@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
                window.location.href = mailto;
              }}
              style={{
                display: 'inline-block', padding: '0.5rem 1.25rem',
                background: 'transparent',
                color: reportState === 'copied' ? 'var(--good)' : 'var(--bad)',
                border: '1px solid ' + (reportState === 'copied' ? 'var(--good)' : 'var(--border-strong)'),
                borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600,
                cursor: 'pointer', whiteSpace: 'nowrap', fontFamily: 'inherit',
                transition: 'background 0.15s, color 0.15s, border-color 0.15s',
              }}
            >
              {reportState === 'copied' ? '✓ Copied' : 'Report incorrect info'}
            </button>
          </div>

          <div class="disclaimer">
            <strong>Important:</strong> Visa requirements change frequently. This tool provides general guidance based on publicly available data.
            <strong> Always verify with the relevant embassy or consulate before traveling.</strong>
          </div>
        </>
      )}

      {checking && (
        <div role="status" style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.5rem', textAlign: 'center', color: 'var(--muted)' }}>
          Checking {destination}…
        </div>
      )}

      {passports.length > 0 && destination && !checking && !best && (
        <div style={{ background: 'rgba(239,111,108,.1)', border: '2px solid var(--bad)', borderRadius: '16px', padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--bad)' }}>No data available</div>
          <div style={{ color: 'var(--muted)', marginTop: '0.5rem' }}>We don't have visa data for this combination. Please check with the embassy of {destination}.</div>
        </div>
      )}
    </div>
  );
}
