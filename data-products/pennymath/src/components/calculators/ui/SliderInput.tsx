import { useRef, useState } from 'preact/hooks';
import { AMOUNT_FLOOR, MIN_WINDOW, amountCeiling, shortAmount, windowFor, windowStep } from '../../../lib/amount-range';

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
   * Set on money amounts with no real upper limit: loans, prices, income,
   * balances. The amount can then be anything from 1,000 to ₹100 crore, or to
   * 100 million in other currencies, and ×10 / ÷10 buttons move the slider's
   * range. `min` 0 keeps zero allowed, for amounts that can be "none". `max`
   * only seeds the range when the value is zero, and `step` is ignored.
   * Leave it off where a limit is real, such as the ₹1.5 lakh PPF cap.
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

  // Money amounts: the full range is fixed, and the slider shows a window of it.
  const ceiling = amountCeiling(locale);
  const floor = min === 0 ? 0 : AMOUNT_FLOOR;
  const [windowTop, setWindowTop] = useState(() => windowFor(value, max, ceiling));
  // A value set from outside, such as a preset, widens the window rather than pinning the slider.
  const top = value > windowTop ? windowFor(value, max, ceiling) : windowTop;
  const lo = scalable ? floor : min;
  const hi = scalable ? top : max;
  const sliderMin = scalable ? 0 : min;
  const sliderStep = scalable ? windowStep(top) : step;
  const canShrink = top / 10 >= MIN_WINDOW && top / 10 >= value;
  const canGrow = top < ceiling;
  const short = (n: number) => shortAmount(n, locale, prefix);

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

    if (!scalable) {
      onChange(Math.min(max, Math.max(min, num)));
      return;
    }
    const next = Math.min(ceiling, Math.max(floor, num));
    if (next > top) setWindowTop(windowFor(next, max, ceiling));
    onChange(next);
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

  const span = hi - sliderMin;
  const percent = span > 0 ? ((value - sliderMin) / span) * 100 : 0;
  const unit = (prefix + suffix).trim();

  return (
    <div class="slider-group">
      <div class="field-head">
        <label class="field-label" htmlFor={`${id}-input`}>{label}</label>
        {scalable && (
          <span class="scaler">
            <button type="button" disabled={!canShrink} onClick={() => setWindowTop(top / 10)} aria-label={`Slider range ÷10, up to ${short(top / 10)}`}>÷10</button>
            <span class="scaler-top" aria-hidden="true">up to {short(top)}</span>
            <button type="button" disabled={!canGrow} onClick={() => setWindowTop(Math.min(ceiling, top * 10))} aria-label={`Slider range ×10, up to ${short(Math.min(ceiling, top * 10))}`}>×10</button>
          </span>
        )}
      </div>
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
          min={sliderMin}
          max={hi}
          step={sliderStep}
          value={value}
          onInput={(e: Event) => onChange(Math.max(lo, Number((e.target as HTMLInputElement).value)))}
          class="range-slider"
          style={`--fill: ${Math.min(100, Math.max(0, percent))}%`}
        />
      </div>
    </div>
  );
}
