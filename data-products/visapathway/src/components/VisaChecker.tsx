import { useState, useEffect, useRef } from 'preact/hooks';

interface VisaMatrix { [passport: string]: { [destination: string]: string | number } }
interface ResidencePermitData {
  [permit: string]: {
    source: string;
    last_verified: string;
    exemptions: { [country: string]: { access: string; days?: number; source: string; note?: string } };
  };
}

function statusLabel(code: string | number): { text: string; class: string; priority: number } {
  if (typeof code === 'number') return { text: `Visa-free (${code} days)`, class: 'visa-free', priority: 1 };
  switch (code) {
    case 'vf': return { text: 'Visa-free', class: 'visa-free', priority: 1 };
    case 'voa': return { text: 'Visa on arrival', class: 'visa-on-arrival', priority: 2 };
    case 'eta': return { text: 'ETA (Electronic Travel Authorization)', class: 'e-visa', priority: 3 };
    case 'ev': return { text: 'e-Visa available', class: 'e-visa', priority: 4 };
    case 'vr': return { text: 'Visa required', class: 'visa-required', priority: 5 };
    case 'na': return { text: 'No admission', class: 'visa-required', priority: 6 };
    default: return { text: String(code), class: 'visa-free', priority: 1 };
  }
}

function CountryAutocomplete({ countries, value, onChange, placeholder, id }: {
  countries: string[]; value: string; onChange: (v: string) => void; placeholder: string; id: string;
}) {
  const [query, setQuery] = useState(value);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const filtered = query ? countries.filter(c => c.toLowerCase().includes(query.toLowerCase())).slice(0, 8) : [];

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <input
        id={id} type="text" value={query} placeholder={placeholder}
        onInput={(e) => { setQuery((e.target as HTMLInputElement).value); setOpen(true); onChange(''); }}
        onFocus={() => setOpen(true)}
        autocomplete="off"
      />
      {open && filtered.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, background: 'white', border: '1px solid #e2e8f0',
          borderRadius: '0 0 8px 8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 50, maxHeight: '200px', overflowY: 'auto',
        }}>
          {filtered.map(c => (
            <div
              key={c}
              onClick={() => { setQuery(c); onChange(c); setOpen(false); }}
              style={{ padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.9rem' }}
              onMouseEnter={(e) => (e.target as HTMLDivElement).style.background = '#f1f5f9'}
              onMouseLeave={(e) => (e.target as HTMLDivElement).style.background = 'white'}
            >
              {c}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function VisaChecker() {
  const [matrix, setMatrix] = useState<VisaMatrix | null>(null);
  const [countries, setCountries] = useState<string[]>([]);
  const [permits, setPermits] = useState<ResidencePermitData | null>(null);
  const [passports, setPassports] = useState<string[]>([]);
  const [residencePermits, setResidencePermits] = useState<string[]>([]);
  const [destination, setDestination] = useState('');
  const [newPassport, setNewPassport] = useState('');
  const [newPermit, setNewPermit] = useState('');

  useEffect(() => {
    Promise.all([
      fetch('/data/visa-matrix.json').then(r => r.json()),
      fetch('/data/countries.json').then(r => r.json()),
      fetch('/data/residence-permits.json').then(r => r.json()),
    ]).then(([m, c, p]) => { setMatrix(m); setCountries(c); setPermits(p); });
  }, []);

  const addPassport = () => {
    if (newPassport && countries.includes(newPassport) && !passports.includes(newPassport)) {
      setPassports([...passports, newPassport]);
      setNewPassport('');
    }
  };

  const addPermit = () => {
    if (newPermit && permits && newPermit in permits && !residencePermits.includes(newPermit)) {
      setResidencePermits([...residencePermits, newPermit]);
      setNewPermit('');
    }
  };

  const removePassport = (p: string) => setPassports(passports.filter(x => x !== p));
  const removePermit = (p: string) => setResidencePermits(residencePermits.filter(x => x !== p));

  // Calculate best result across all passports + residence permits
  const getResults = () => {
    if (!matrix || !destination || passports.length === 0) return null;

    const results: Array<{
      document: string; type: string; requirement: string | number;
      label: ReturnType<typeof statusLabel>; source?: string; note?: string;
    }> = [];

    // Check each passport
    for (const passport of passports) {
      const req = matrix[passport]?.[destination];
      if (req !== undefined) {
        results.push({
          document: `${passport} passport`,
          type: 'passport',
          requirement: req,
          label: statusLabel(req),
        });
      }
    }

    // Check residence permits
    if (permits) {
      for (const permit of residencePermits) {
        const permitData = permits[permit];
        if (permitData?.exemptions?.[destination]) {
          const ex = permitData.exemptions[destination];
          results.push({
            document: permit,
            type: 'residence-permit',
            requirement: ex.access,
            label: statusLabel(ex.days ? ex.days : ex.access),
            source: ex.source,
            note: ex.note,
          });
        }
      }
    }

    results.sort((a, b) => a.label.priority - b.label.priority);
    return results;
  };

  const results = getResults();
  const bestResult = results?.[0];

  if (!matrix) {
    return <div class="checker-tool"><p>Loading visa data (199 countries)...</p></div>;
  }

  return (
    <div class="checker-tool">
      {/* Passports */}
      <div class="input-group">
        <label>Your Passports / Citizenships</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ flex: 1 }}>
            <CountryAutocomplete
              id="passport-input"
              countries={countries}
              value={newPassport}
              onChange={setNewPassport}
              placeholder="Type country name..."
            />
          </div>
          <button class="add-btn" onClick={addPassport} style={{ marginTop: 0 }}>Add</button>
        </div>
        <div class="tag-list">
          {passports.map(p => (
            <span class="tag" key={p}>{p} <button onClick={() => removePassport(p)}>&times;</button></span>
          ))}
        </div>
      </div>

      {/* Residence Permits */}
      <div class="input-group">
        <label>Residence Permits (optional)</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select
            value={newPermit}
            onChange={(e) => setNewPermit((e.target as HTMLSelectElement).value)}
            style={{ flex: 1 }}
          >
            <option value="">Select a residence permit...</option>
            {permits && Object.keys(permits).map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <button class="add-btn" onClick={addPermit} style={{ marginTop: 0 }}>Add</button>
        </div>
        <div class="tag-list">
          {residencePermits.map(p => (
            <span class="tag" key={p}>{p} <button onClick={() => removePermit(p)}>&times;</button></span>
          ))}
        </div>
      </div>

      {/* Destination */}
      <div class="input-group">
        <label htmlFor="destination-input">Where do you want to go?</label>
        <CountryAutocomplete
          id="destination-input"
          countries={countries}
          value={destination}
          onChange={setDestination}
          placeholder="Type destination country..."
        />
      </div>

      {/* Results */}
      {bestResult && destination && (
        <>
          <div class={`result-banner ${bestResult.label.class}`}>
            <div class="result-status">{bestResult.label.text}</div>
            <div class="result-details">
              Best option: <strong>{bestResult.document}</strong> to enter <strong>{destination}</strong>
              {bestResult.note && <><br />{bestResult.note}</>}
            </div>
          </div>

          {results!.length > 1 && (
            <>
              <h3 style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>All Your Options</h3>
              <p style={{ fontSize: '0.85rem', color: '#64748b' }}>We checked all your documents and ranked them from best to worst access:</p>
              <table class="results-table">
                <thead>
                  <tr><th>Document</th><th>Access to {destination}</th><th>Source</th></tr>
                </thead>
                <tbody>
                  {results!.map((r, i) => (
                    <tr class={i === 0 ? 'best-option' : ''}>
                      <td><strong>{r.document}</strong>{i === 0 && ' (best)'}</td>
                      <td><span class={`status status-${typeof r.requirement === 'number' ? 'vf' : r.requirement}`}>{r.label.text}</span></td>
                      <td>{r.source ? <a href={r.source} target="_blank" rel="noopener" style={{ fontSize: '0.8rem' }}>Official source</a> : <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Passport Index Dataset</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          <div class="disclaimer">
            <strong>Important:</strong> Visa requirements can change without notice. This tool provides general guidance based on publicly available data.
            <strong> Always verify with the relevant embassy or consulate before traveling.</strong>
            Data sources: <a href="https://github.com/ilyankou/passport-index-dataset" target="_blank" rel="noopener">Passport Index Dataset</a> + official government immigration websites.
            Last updated: April 2026.
          </div>
        </>
      )}

      {passports.length > 0 && destination && !bestResult && (
        <div class="result-banner visa-required">
          <div class="result-status">No data available</div>
          <div class="result-details">We don't have visa data for this combination. Check with the embassy of {destination}.</div>
        </div>
      )}
    </div>
  );
}
