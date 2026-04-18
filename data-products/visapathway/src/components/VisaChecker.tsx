import { useState, useEffect, useRef } from 'preact/hooks';

interface VisaMatrix { [passport: string]: { [destination: string]: string | number } }
interface PermitExemption { access: string; days?: number; source: string; note?: string; }
interface ResidencePermitData {
  [permit: string]: {
    source: string; last_verified: string;
    exemptions: { [country: string]: PermitExemption };
  };
}

function statusInfo(code: string | number) {
  if (typeof code === 'number') return {
    text: `Visa-free entry`,
    detail: `You can enter and stay for up to ${code} days. No visa application needed — just show your passport at immigration.`,
    action: 'No action needed before travel.',
    color: '#16a34a', bg: '#f0fdf4', border: '#22c55e', icon: '✓', priority: 1,
  };
  const map: Record<string, any> = {
    'vf':  { text: 'Visa-free entry', detail: 'No visa needed. Present your passport at immigration on arrival.', action: 'No action needed before travel.', color: '#16a34a', bg: '#f0fdf4', border: '#22c55e', icon: '✓', priority: 1 },
    'voa': { text: 'Visa on arrival', detail: 'You can get a visa stamp at the airport when you land. Bring cash (USD) for the visa fee, a passport photo, and proof of return ticket.', action: 'No pre-application needed. Get visa at the airport on arrival.', color: '#d97706', bg: '#fffbeb', border: '#f59e0b', icon: '⬇', priority: 2 },
    'eta': { text: 'Electronic Travel Authorization (ETA)', detail: 'You must apply online before traveling. It is a quick digital approval — not a full visa application.', action: 'Apply online before your flight. Usually approved in 24-72 hours.', color: '#2563eb', bg: '#eff6ff', border: '#3b82f6', icon: '⚡', priority: 3 },
    'ev':  { text: 'e-Visa required', detail: 'You must apply for an electronic visa online before traveling. Upload documents and pay the fee on the official portal.', action: 'Apply on the official e-Visa portal before your flight. Processing: 2-5 business days.', color: '#2563eb', bg: '#eff6ff', border: '#3b82f6', icon: '📋', priority: 4 },
    'vr':  { text: 'Visa required (apply at embassy)', detail: 'You need to apply for a visa at the embassy or consulate before traveling. This usually requires an in-person visit or submission through a visa center.', action: 'Apply at the nearest embassy/consulate or authorized visa center. Allow 1-4 weeks for processing.', color: '#dc2626', bg: '#fef2f2', border: '#ef4444', icon: '✗', priority: 5 },
    'na':  { text: 'Entry not permitted', detail: 'Entry is not allowed with this travel document.', action: 'Contact the embassy for exceptional circumstances.', color: '#6b7280', bg: '#f3f4f6', border: '#9ca3af', icon: '⊘', priority: 6 },
  };
  return map[code] || { text: `Visa-free (${code} days)`, detail: `You can enter and stay for up to ${code} days.`, action: 'No action needed before travel.', color: '#16a34a', bg: '#f0fdf4', border: '#22c55e', icon: '✓', priority: 1 };
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
        style={{ width: '100%', padding: '0.7rem 1rem', border: '2px solid #e2e8f0', borderRadius: '10px', fontSize: '1rem', fontFamily: 'inherit', background: '#f9fafb' }}
      />
      {open && filtered.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, background: 'white',
          border: '1px solid #e2e8f0', borderRadius: '0 0 10px 10px', boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          zIndex: 50, maxHeight: '240px', overflowY: 'auto',
        }}>
          {filtered.map(item => (
            <div key={item} onClick={() => select(item)}
              style={{ padding: '0.65rem 1rem', cursor: 'pointer', fontSize: '0.95rem', borderBottom: '1px solid #f1f5f9' }}
              onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.background = '#f0f0ff'}
              onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.background = 'white'}>
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

export default function VisaChecker() {
  const [matrix, setMatrix] = useState<VisaMatrix | null>(null);
  const [countries, setCountries] = useState<string[]>([]);
  const [permits, setPermits] = useState<ResidencePermitData | null>(null);
  const [passports, setPassports] = useState<string[]>([]);
  const [selectedPermits, setSelectedPermits] = useState<string[]>([]);
  const [destination, setDestination] = useState('');

  useEffect(() => {
    Promise.all([
      fetch('/data/visa-matrix.json').then(r => r.json()),
      fetch('/data/countries.json').then(r => r.json()),
      fetch('/data/residence-permits.json').then(r => r.json()),
    ]).then(([m, c, p]) => { setMatrix(m); setCountries(c); setPermits(p); });
  }, []);

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
    if (!matrix || !destination || passports.length === 0) return null;
    const results: Array<{
      document: string; requirement: string | number;
      info: ReturnType<typeof statusInfo>; source?: string; note?: string;
    }> = [];

    for (const passport of passports) {
      const req = matrix[passport]?.[destination];
      if (req !== undefined) results.push({ document: `${passport} passport`, requirement: req, info: statusInfo(req) });
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
          results.push({ document: permit, requirement: ex.access, info: statusInfo(key), source: ex.source, note: ex.note });
        }
      }
    }
    results.sort((a, b) => a.info.priority - b.info.priority);
    return results;
  };

  const results = getResults();
  const best = results?.[0];

  if (!matrix) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading visa data for 199 countries...</div>;

  return (
    <div>
      {/* Step 1 */}
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.75rem', marginBottom: '1rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ background: '#7c3aed', color: 'white', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>1</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>What passports do you hold?</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Add all your citizenships. We'll check each one.</div>
          </div>
        </div>
        <Autocomplete id="passport-search" items={countries.filter(c => !passports.includes(c))} placeholder="Start typing a country name..." onSelect={addPassport} />
        {passports.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
            {passports.map(p => (
              <span key={p} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: '#ede9fe', color: '#7c3aed', padding: '0.35rem 0.85rem', borderRadius: '999px', fontSize: '0.85rem', fontWeight: 600 }}>
                {p} <button onClick={() => removePassport(p)} style={{ background: 'none', border: 'none', color: '#7c3aed', cursor: 'pointer', fontSize: '1.1rem', lineHeight: 1, padding: 0 }}>&times;</button>
              </span>
            ))}
          </div>
        )}
        {passports.length === 0 && (
          <div style={{ marginTop: '1rem' }}>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.5rem', fontWeight: 600 }}>Quick start — pick your profile:</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {PRESETS.map(p => (
                <button key={p.label} onClick={() => applyPreset(p)}
                  style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.4rem 0.8rem', fontSize: '0.8rem', cursor: 'pointer', color: '#475569', fontFamily: 'inherit' }}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Step 2 */}
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.75rem', marginBottom: '1rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ background: '#7c3aed', color: 'white', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>2</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>Any additional visas or permits?</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>These can unlock extra countries. Tap all that apply.</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '0.5rem' }}>
          {permits && Object.keys(permits).map(p => {
            const on = selectedPermits.includes(p);
            return (
              <button key={p} onClick={() => togglePermit(p)}
                style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.65rem 0.9rem', border: `2px solid ${on ? '#7c3aed' : '#e2e8f0'}`, background: on ? '#f5f3ff' : 'white', borderRadius: '10px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: on ? 700 : 500, color: on ? '#7c3aed' : '#475569', fontFamily: 'inherit', textAlign: 'left' }}>
                <span style={{ width: '20px', height: '20px', borderRadius: '4px', flexShrink: 0, border: `2px solid ${on ? '#7c3aed' : '#cbd5e1'}`, background: on ? '#7c3aed' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.7rem', fontWeight: 700 }}>{on ? '✓' : ''}</span>
                {p}
              </button>
            );
          })}
        </div>
      </div>

      {/* Step 3 */}
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.75rem', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <span style={{ background: passports.length > 0 ? '#7c3aed' : '#cbd5e1', color: 'white', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flexShrink: 0 }}>3</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>Where do you want to go?</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>We'll find the best document to use for entry.</div>
          </div>
        </div>
        <Autocomplete id="dest-search" items={countries} placeholder="Start typing a destination..." onSelect={setDest} />
        {destination && (
          <div style={{ marginTop: '0.5rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: '#dbeafe', color: '#1d4ed8', padding: '0.35rem 0.85rem', borderRadius: '999px', fontSize: '0.85rem', fontWeight: 600 }}>
              {destination} <button onClick={() => setDestination('')} style={{ background: 'none', border: 'none', color: '#1d4ed8', cursor: 'pointer', fontSize: '1.1rem', lineHeight: 1, padding: 0 }}>&times;</button>
            </span>
          </div>
        )}
      </div>

      {/* Results */}
      {best && destination && (
        <>
          <div style={{ background: best.info.bg, border: `2px solid ${best.info.border}`, borderRadius: '16px', padding: '2rem', marginBottom: '1rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.25rem' }}>{best.info.icon}</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: best.info.color }}>{best.info.text}</div>
              <div style={{ color: '#475569', marginTop: '0.5rem', fontSize: '1.05rem' }}>
                Use your <strong>{best.document}</strong> to enter <strong>{destination}</strong>
              </div>
            </div>
            <div style={{ marginTop: '1.25rem', padding: '1rem', background: 'rgba(255,255,255,0.7)', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.7 }}>{best.info.detail}</div>
              {best.note && <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.5rem', fontStyle: 'italic', borderLeft: '3px solid #e2e8f0', paddingLeft: '0.75rem' }}>{best.note}</div>}
              <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.8rem', background: '#f8fafc', borderRadius: '8px', fontSize: '0.85rem' }}>
                <strong style={{ color: '#334155' }}>What to do: </strong>
                <span style={{ color: '#475569' }}>{best.info.action}</span>
              </div>
              {best.source && <div style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}><a href={best.source} target="_blank" rel="noopener">View official source</a></div>}
            </div>
          </div>

          {results!.length > 1 && (
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.5rem', marginBottom: '1rem' }}>
              <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem' }}>All your options for {destination}</h3>
              <table class="results-table">
                <thead><tr><th>Document</th><th>Access</th><th>Source</th></tr></thead>
                <tbody>
                  {results!.map((r, i) => (
                    <tr key={i} style={{ background: i === 0 ? '#f0fdf4' : 'transparent' }}>
                      <td style={{ fontWeight: i === 0 ? 700 : 400 }}>{r.document} {i === 0 && <span style={{ color: '#16a34a', fontSize: '0.75rem' }}>BEST</span>}</td>
                      <td><span style={{ color: r.info.color, fontWeight: 600 }}>{r.info.text}</span></td>
                      <td>{r.source ? <a href={r.source} target="_blank" rel="noopener" style={{ fontSize: '0.8rem' }}>Official</a> : <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Passport Index</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Report incorrect info */}
          <div style={{
            background: 'white', border: '1px solid #e2e8f0', borderRadius: '16px',
            padding: '1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center',
            justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap',
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Is this information incorrect?</div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Help us improve — report wrong visa info and we'll verify and fix it.</div>
            </div>
            <a
              href={`mailto:contact@techtools365.com?subject=${encodeURIComponent(`[VisaPathway] Incorrect visa info: ${passports.join(', ')} → ${destination}`)}&body=${encodeURIComponent(`Hi,\n\nThe visa information shown for the following combination appears to be incorrect:\n\nPassports: ${passports.join(', ')}\nAdditional documents: ${selectedPermits.join(', ') || 'None'}\nDestination: ${destination}\nResult shown: ${best?.info.text} (via ${best?.document})\n\nWhat is the correct information:\n[Please describe the correct visa requirement and how you know — e.g., personal experience, embassy website, etc.]\n\nThank you!`)}`}
              style={{
                display: 'inline-block', padding: '0.5rem 1.25rem', background: '#fef2f2',
                color: '#dc2626', border: '1px solid #fecaca', borderRadius: '8px',
                fontSize: '0.85rem', fontWeight: 600, textDecoration: 'none', whiteSpace: 'nowrap',
              }}
            >
              Report incorrect info
            </a>
          </div>

          <div class="disclaimer">
            <strong>Important:</strong> Visa requirements change frequently. This tool provides general guidance based on publicly available data.
            <strong> Always verify with the relevant embassy or consulate before traveling.</strong>
          </div>
        </>
      )}

      {passports.length > 0 && destination && !best && (
        <div style={{ background: '#fef2f2', border: '2px solid #ef4444', borderRadius: '16px', padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#dc2626' }}>No data available</div>
          <div style={{ color: '#64748b', marginTop: '0.5rem' }}>We don't have visa data for this combination. Please check with the embassy of {destination}.</div>
        </div>
      )}
    </div>
  );
}
