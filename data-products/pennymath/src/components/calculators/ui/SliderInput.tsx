import { useRef, useState } from 'preact/hooks';

interface SliderInputProps {
  id: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  prefix?: string;
  suffix?: string;
  /**
   * BCP-47 locale for number formatting. Callers derive this from their own
   * currency (see `localeForCurrency`) — this component holds no currency
   * knowledge, and `prefix` is a display string with no behaviour attached.
   */
  locale?: string;
  /**
   * Set where `max` is an arbitrary UI ceiling rather than a real limit of the
   * quantity: amounts, balances, corpus. Typing a larger number then widens the
   * slider instead of clamping the value. Leave it off where the maximum truly
   * bounds the domain, such as a rate capped at 30%.
   */
  scalable?: boolean;
  onChange: (value: number) => void;
}

/** Typing sets an exact value. The slider along the box's lower edge nudges it. */
export default function SliderInput({
  id,
  label,
  value,
  min,
  max,
  step,
  prefix = '',
  suffix = '',
  locale = 'en-US',
  scalable = false,
  onChange,
}: SliderInputProps) {
  const fmt = (n: number) => n.toLocaleString(locale);

  // Ceiling after any widening caused by typing a larger number.
  const [ceiling, setCeiling] = useState(max);
  const effMax = scalable ? Math.max(ceiling, max) : max;
  const effStep = scalable ? Math.max(step, step * Math.pow(10, Math.round(Math.log10(effMax / max)))) : step;

  // While the box has focus we hold the raw keystrokes here and leave `value`
  // alone. Committing on every keystroke made the box impossible to type in: a
  // half-typed "5" of "500000" was instantly clamped up to `min`.
  const [draft, setDraft] = useState<string | null>(null);
  // Set when Enter/Escape has already handled the edit, so the blur they
  // trigger does not commit a stale draft.
  const settledRef = useRef(false);
  const justFocusedRef = useRef(false);

  const commit = (raw: string) => {
    setDraft(null);
    const cleaned = raw.replace(/[^0-9.]/g, '');
    if (cleaned === '') return; // empty box — keep the previous value
    const num = parseFloat(cleaned);
    if (isNaN(num)) return;

    let top = effMax;
    if (scalable && num > effMax) {
      top = num;
      setCeiling(num);
    }
    onChange(Math.min(top, Math.max(min, num)));
  };

  const handleFocus = (e: Event) => {
    const el = e.target as HTMLInputElement;
    // Show the unformatted number, which is easier to overwrite than "10,00,000".
    // Set it here rather than leaving it to the re-render: writing the value
    // later would drop the selection, and typing would then add to the old number.
    const raw = String(value);
    el.value = raw;
    el.select();
    justFocusedRef.current = true;
    setDraft(raw);
  };

  // A click's mouse-up would otherwise replace the selection with a caret.
  const handleMouseUp = (e: MouseEvent) => {
    if (justFocusedRef.current) {
      e.preventDefault();
      justFocusedRef.current = false;
    }
  };

  const handleBlur = () => {
    // Enter/Escape already settled this edit and then blurred the field. State
    // updates are async, so `draft` here is still the pre-keypress value —
    // committing it again would re-apply a cancelled edit.
    if (settledRef.current) {
      settledRef.current = false;
      return;
    }
    if (draft !== null) commit(draft);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (draft !== null) commit(draft);
      settledRef.current = true;
      (e.target as HTMLInputElement).blur();
    } else if (e.key === 'Escape') {
      setDraft(null);
      settledRef.current = true;
      (e.target as HTMLInputElement).blur();
    }
  };

  const span = effMax - min;
  const percent = span > 0 ? ((value - min) / span) * 100 : 0;
  const unit = (prefix + suffix).trim();

  return (
    <div class="slider-group">
      <label class="field-label" htmlFor={`${id}-input`}>{label}</label>
      <div class="slider-field">
        <input
          type="text"
          inputMode="decimal"
          id={`${id}-input`}
          value={draft ?? fmt(value)}
          onFocus={handleFocus}
          onMouseUp={handleMouseUp}
          onInput={(e: Event) => setDraft((e.target as HTMLInputElement).value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          class="value-input"
        />
        {unit && <span class="unit">{unit}</span>}
        <input
          type="range"
          id={id}
          aria-label={`${label} slider`}
          min={min}
          max={effMax}
          step={effStep}
          value={value}
          onInput={(e: Event) => onChange(Number((e.target as HTMLInputElement).value))}
          class="range-slider"
          style={`--fill: ${Math.min(100, Math.max(0, percent))}%`}
        />
      </div>
    </div>
  );
}
