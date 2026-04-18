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
   * BCP-47 locale for number formatting. If omitted, we pick `en-IN`
   * (lakhs/crores grouping) when the prefix contains ₹, otherwise `en-US`.
   */
  locale?: string;
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
  locale,
  onChange,
}: SliderInputProps) {
  const resolvedLocale = locale ?? (prefix.includes('₹') ? 'en-IN' : 'en-US');
  const fmt = (n: number) => n.toLocaleString(resolvedLocale);

  const handleSlider = (e: Event) => {
    onChange(Number((e.target as HTMLInputElement).value));
  };

  const handleInput = (e: Event) => {
    const raw = (e.target as HTMLInputElement).value.replace(/[^0-9.]/g, '');
    const num = parseFloat(raw);
    if (!isNaN(num)) {
      onChange(Math.min(max, Math.max(min, num)));
    }
  };

  const percent = ((value - min) / (max - min)) * 100;

  return (
    <div class="slider-group">
      <div class="slider-header">
        <label htmlFor={id}>{label}</label>
        <div class="slider-value-box">
          {prefix && <span class="prefix">{prefix}</span>}
          <input
            type="text"
            id={`${id}-input`}
            value={fmt(value)}
            onInput={handleInput}
            class="value-input"
          />
          {suffix && <span class="suffix">{suffix}</span>}
        </div>
      </div>
      <input
        type="range"
        id={id}
        min={min}
        max={max}
        step={step}
        value={value}
        onInput={handleSlider}
        class="range-slider"
        style={`--fill: ${percent}%`}
      />
      <div class="slider-range">
        <span>{prefix}{fmt(min)}{suffix}</span>
        <span>{prefix}{fmt(max)}{suffix}</span>
      </div>
    </div>
  );
}
