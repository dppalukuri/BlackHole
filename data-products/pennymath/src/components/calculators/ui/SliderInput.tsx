import { useRef, useState } from 'preact/hooks';

/** How many ×10 decades the user may widen or narrow an amount slider by. */
const MAX_ZOOM_OUT = 3;
const MAX_ZOOM_IN = 3;

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
   * Show ÷10 / ×10 controls that rescale the slider's ceiling and step
   * together, so one slider spans four orders of magnitude without losing
   * granularity at either end.
   *
   * Set it wherever `max` is an arbitrary UI ceiling rather than a real limit
   * of the quantity — amounts, balances, corpus. Leave it off where the
   * maximum genuinely bounds the domain, such as a rate capped at 30% or a
   * tenure capped at 40 years. This is a property of the quantity, not of how
   * it happens to be labelled.
   */
  scalable?: boolean;
  onChange: (value: number) => void;
}

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

  const canScale = scalable;

  // Range multiplier, in powers of ten. 0 is the range the calculator declared.
  const [zoom, setZoom] = useState(0);
  // While the text box has focus we hold the raw keystrokes here and leave
  // `value` alone. Committing on every keystroke made the box impossible to
  // type in: a half-typed "5" of "500000" was instantly clamped up to `min`.
  const [draft, setDraft] = useState<string | null>(null);
  // Set when Enter/Escape has already handled the edit, so the blur they
  // trigger does not commit a stale draft.
  const settledRef = useRef(false);

  const ceilingAt = (z: number) => (canScale ? max * Math.pow(10, z) : max);
  const effMax = ceilingAt(zoom);
  const effStep = canScale ? Math.max(1, step * Math.pow(10, zoom)) : step;

  const nextIn = ceilingAt(zoom - 1);
  const canZoomIn = canScale && zoom > -MAX_ZOOM_IN && value <= nextIn && min < nextIn;
  const canZoomOut = canScale && zoom < MAX_ZOOM_OUT;

  /** Smallest zoom level whose ceiling can hold `v`. */
  const fitZoomFor = (v: number) => {
    let z = zoom;
    while (v > ceilingAt(z) && z < MAX_ZOOM_OUT) z++;
    return z;
  };

  const commit = (raw: string) => {
    setDraft(null);
    const cleaned = raw.replace(/[^0-9.]/g, '');
    if (cleaned === '') return; // empty box — keep the previous value
    const num = parseFloat(cleaned);
    if (isNaN(num)) return;

    // Typing a number past the ceiling should widen the slider, not silently
    // clamp the value down to the ceiling.
    let ceiling = effMax;
    if (canScale) {
      const z = fitZoomFor(num);
      if (z !== zoom) {
        setZoom(z);
        ceiling = ceilingAt(z);
      }
    }
    onChange(Math.min(ceiling, Math.max(min, num)));
  };

  const handleSlider = (e: Event) => {
    onChange(Number((e.target as HTMLInputElement).value));
  };

  const handleFocus = (e: Event) => {
    const el = e.target as HTMLInputElement;
    setDraft(String(value)); // unformatted — easier to overwrite than "10,00,000"
    el.select();
  };

  const handleInput = (e: Event) => {
    setDraft((e.target as HTMLInputElement).value);
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

  return (
    <div class="slider-group">
      <div class="slider-header">
        <label htmlFor={id}>{label}</label>
        <div class="slider-value-box">
          {prefix && <span class="prefix">{prefix}</span>}
          <input
            type="text"
            inputMode="decimal"
            id={`${id}-input`}
            value={draft ?? fmt(value)}
            onFocus={handleFocus}
            onInput={handleInput}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            class="value-input"
          />
          {suffix && <span class="suffix">{suffix}</span>}
        </div>
      </div>
      <input
        type="range"
        id={id}
        min={min}
        max={effMax}
        step={effStep}
        value={value}
        onInput={handleSlider}
        class="range-slider"
        style={`--fill: ${Math.min(100, Math.max(0, percent))}%`}
      />
      <div class="slider-range">
        <span>{prefix}{fmt(min)}{suffix}</span>
        <span class="slider-range-max">
          <span>{prefix}{fmt(effMax)}{suffix}</span>
          {canScale && (
            <span class="slider-scale">
              <button
                type="button"
                class="slider-scale-btn"
                onClick={() => setZoom(zoom - 1)}
                disabled={!canZoomIn}
                title={`Narrow the range 10x (finer steps of ${prefix}${fmt(Math.max(1, effStep / 10))})`}
                aria-label="Narrow slider range tenfold for finer steps"
              >
                ÷10
              </button>
              <button
                type="button"
                class="slider-scale-btn"
                onClick={() => setZoom(zoom + 1)}
                disabled={!canZoomOut}
                title={`Widen the range 10x (up to ${prefix}${fmt(ceilingAt(zoom + 1))})`}
                aria-label="Widen slider range tenfold"
              >
                &times;10
              </button>
            </span>
          )}
        </span>
      </div>
    </div>
  );
}
