import { useEffect, useRef, useState } from 'preact/hooks';
import { formatCurrency } from '../../../lib/formatters';

export interface ResultRow {
  label: string;
  /** A number is shown as currency. A string is shown as it is, such as "5.2%". */
  value: number | string;
  /** The one answer the page is for. It is shown large, above the other rows. */
  highlight?: boolean;
  note?: string;
  /** Ties the row to a chart series by showing its colour. */
  seriesKey?: 1 | 2 | 3;
}

interface ResultCardProps {
  results: ResultRow[];
  currencyCode: string;
}

export default function ResultCard({ results, currencyCode }: ResultCardProps) {
  const show = (v: number | string) => (typeof v === 'number' ? formatCurrency(v, currencyCode) : v);
  const main = results.find((r) => r.highlight);
  const ref = useRef<HTMLDivElement>(null);
  // On a phone the inputs fill the screen, so keep the answer pinned in view
  // until the full result scrolls up from below.
  const [belowFold, setBelowFold] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || !main || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(([entry]) => {
      setBelowFold(!entry.isIntersecting && entry.boundingClientRect.top > 0);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div class="result-card" ref={ref}>
        {results.map((r) => (
          <div class={`result-item ${r.highlight ? 'result-highlight' : ''}`}>
            {r.seriesKey && <i class={`swatch-dot series-${r.seriesKey}`} />}
            <span class="result-label">
              {r.label}
              {r.note && <small>{r.note}</small>}
            </span>
            <span class="result-value">{show(r.value)}</span>
          </div>
        ))}
      </div>
      {main && (
        <div class={`pin ${belowFold ? 'is-away' : ''}`} aria-hidden="true">
          <span>{main.label}</span>
          <strong>{show(main.value)}</strong>
        </div>
      )}
    </>
  );
}
