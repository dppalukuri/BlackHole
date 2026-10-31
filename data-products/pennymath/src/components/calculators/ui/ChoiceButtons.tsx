interface ChoiceButtonsProps<T extends string | number> {
  label: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}

/** A labelled row of mutually exclusive options. */
export default function ChoiceButtons<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: ChoiceButtonsProps<T>) {
  return (
    <div class="choice-group">
      <span class="field-label">{label}</span>
      <div class="choices" role="group" aria-label={label}>
        {options.map((o) => (
          <button
            type="button"
            class={`choice ${o.value === value ? 'is-on' : ''}`}
            aria-pressed={o.value === value}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
