interface ChoiceButtonsProps<T extends string | number> {
  label: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}

/** A labelled row of mutually exclusive options, matching the slider groups. */
export default function ChoiceButtons<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: ChoiceButtonsProps<T>) {
  return (
    <div class="slider-group">
      <div class="slider-header">
        <label>{label}</label>
      </div>
      <div role="group" aria-label={label} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.25rem' }}>
        {options.map((o) => {
          const active = o.value === value;
          return (
            <button
              type="button"
              aria-pressed={active}
              onClick={() => onChange(o.value)}
              style={{
                padding: '0.4rem 0.9rem',
                borderRadius: '8px',
                border: `1px solid ${active ? '#6366f1' : '#e2e8f0'}`,
                background: active ? '#6366f1' : 'white',
                color: active ? 'white' : '#64748b',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.82rem',
              }}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
