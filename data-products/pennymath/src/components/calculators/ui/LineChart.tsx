import { useEffect, useRef, useState } from 'preact/hooks';
import { nearestIndex, niceTicks, spreadLabels } from '../../../lib/chart-scale';

export interface ChartSeries {
  name: string;
  /** One value for each entry in `x`. */
  values: number[];
}

interface LineChartProps {
  title: string;
  caption?: string;
  /** Shared x positions, such as years or ages. */
  x: number[];
  /** Up to three series. Colour follows position in this list. */
  series: ChartSeries[];
  /** Full value, for labels, tooltips and the table. */
  format: (n: number) => string;
  /** Short value, for the y axis. Defaults to `format`. */
  formatTick?: (n: number) => string;
  xTick?: (x: number) => string;
  /** Heading for an x value in the tooltip and the table. */
  xTitle?: (x: number) => string;
  xHeading?: string;
  /** Draw flat steps, for values that hold and then jump, such as a loan payment. */
  step?: boolean;
  /** Start the y axis at zero. Turn off when small differences are the point. */
  zeroBased?: boolean;
  /** A dashed vertical line, such as the year a fixed rate ends. */
  marker?: { x: number; label: string } | null;
  height?: number;
  /** Set false when the calculator shows its own, fuller year-by-year table. */
  showTable?: boolean;
}

const DEFAULT_WIDTH = 760;
const LABEL_NAME_LIMIT = 18;

export default function LineChart({
  title,
  caption,
  x,
  series,
  format,
  formatTick = format,
  xTick = (v) => String(v),
  xTitle = (v) => String(v),
  xHeading = 'Year',
  step = false,
  zeroBased = true,
  marker = null,
  height = 280,
  showTable = true,
}: LineChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const measure = () => { if (host.clientWidth) setWidth(host.clientWidth); };
    measure();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(measure);
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  if (x.length < 2 || !series.length) return null;

  const narrow = width < 560;
  const m = { l: 62, r: narrow ? 20 : 128, t: 26, b: 28 };
  const innerW = Math.max(40, width - m.l - m.r);
  const innerH = height - m.t - m.b;

  // A step holds its value across the period leading up to its x position.
  const xMin = step ? x[0] - (x[1] - x[0]) : x[0];
  const xMax = x[x.length - 1];
  const all = series.flatMap((s) => s.values);
  const low = Math.min(...all);
  const high = Math.max(...all);
  const yTicks = niceTicks(zeroBased ? Math.min(0, low) : low, high, 4);
  const y0 = yTicks[0];
  const y1 = yTicks[yTicks.length - 1];
  const X = (v: number) => m.l + ((v - xMin) / (xMax - xMin || 1)) * innerW;
  const Y = (v: number) => m.t + innerH - ((v - y0) / (y1 - y0 || 1)) * innerH;

  const xTicks = niceTicks(xMin, xMax, narrow ? 4 : 6).filter((t) => t >= xMin && t <= xMax);

  const pathFor = (values: number[]) => {
    if (step) {
      let d = `M${X(xMin).toFixed(1)} ${Y(values[0]).toFixed(1)}`;
      values.forEach((v, i) => {
        d += `H${X(x[i]).toFixed(1)}`;
        if (i < values.length - 1) d += `V${Y(values[i + 1]).toFixed(1)}`;
      });
      return d;
    }
    return values.map((v, i) => `${i === 0 ? 'M' : 'L'}${X(x[i]).toFixed(1)} ${Y(v).toFixed(1)}`).join('');
  };

  const last = x.length - 1;
  const endYs = series.map((s) => Y(s.values[last]));
  const labelYs = narrow ? endYs : spreadLabels(endYs, 34, m.t + 8, m.t + innerH - 18);

  const hoverX = (i: number) => (step ? X(x[i] - (x[i] - (i > 0 ? x[i - 1] : xMin)) / 2) : X(x[i]));
  const onPointer = (e: PointerEvent) => {
    const box = (e.currentTarget as SVGElement).closest('svg')!.getBoundingClientRect();
    const scale = width / box.width;
    const px = (e.clientX - box.left) * scale;
    const value = xMin + ((px - m.l) / innerW) * (xMax - xMin);
    const candidates = step ? x.map((v, i) => v - (v - (i > 0 ? x[i - 1] : xMin)) / 2) : x;
    setHover(nearestIndex(candidates, value));
  };

  const markerX = marker && marker.x >= xMin && marker.x <= xMax ? X(marker.x) : null;
  const markerFlip = markerX !== null && markerX > m.l + innerW * 0.72;

  return (
    <section class="chart-card">
      <header class="chart-head">
        <div>
          <h3>{title}</h3>
          {caption && <p class="caption">{caption}</p>}
        </div>
        <ul class="legend">
          {series.map((s, i) => (
            <li><i class={`swatch series-${i + 1}`} />{s.name}</li>
          ))}
        </ul>
      </header>
      <div class="chart" ref={hostRef}>
        <svg
          width="100%"
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          role="img"
          aria-label={`${title}. ${series.map((s) => `${s.name} ends at ${format(s.values[last])}`).join('. ')}.`}
        >
          {yTicks.map((t) => (
            <g>
              <line class="c-grid" x1={m.l} x2={width - m.r} y1={Y(t)} y2={Y(t)} />
              <text class="c-tick" x={m.l - 8} y={Y(t) + 4} text-anchor="end">{formatTick(t)}</text>
            </g>
          ))}
          {xTicks.map((t) => (
            <text class="c-tick" x={X(t)} y={height - 8} text-anchor="middle">{xTick(t)}</text>
          ))}
          {markerX !== null && (
            <g>
              <line class="c-marker" x1={markerX} x2={markerX} y1={m.t - 12} y2={m.t + innerH} />
              <text class="c-note" x={markerX + (markerFlip ? -6 : 6)} y={m.t - 4} text-anchor={markerFlip ? 'end' : 'start'}>{marker!.label}</text>
            </g>
          )}
          {series.map((s, i) => <path class={`c-line stroke-${i + 1}`} d={pathFor(s.values)} />)}
          {series.map((s, i) => <circle class={`c-dot fill-${i + 1}`} cx={X(x[last])} cy={Y(s.values[last])} r={4} />)}
          {!narrow && series.map((s, i) => {
            const lx = width - m.r + 12;
            const showName = s.name.length <= LABEL_NAME_LIMIT;
            return (
              <g>
                <circle class={`fill-${i + 1}`} cx={lx + 3} cy={labelYs[i] - 4} r={4} />
                {showName ? (
                  <>
                    <text class="c-end-name" x={lx + 12} y={labelYs[i]}>{s.name}</text>
                    <text class="c-end-val" x={lx + 12} y={labelYs[i] + 15}>{format(s.values[last])}</text>
                  </>
                ) : (
                  <text class="c-end-val" x={lx + 12} y={labelYs[i]}>{format(s.values[last])}</text>
                )}
              </g>
            );
          })}
          {hover !== null && (
            <g>
              <line class="c-cross" x1={hoverX(hover)} x2={hoverX(hover)} y1={m.t} y2={m.t + innerH} />
              {series.map((s, i) => <circle class={`c-dot fill-${i + 1}`} cx={hoverX(hover)} cy={Y(s.values[hover])} r={5} />)}
            </g>
          )}
          <rect
            class="c-hit"
            x={m.l}
            y={m.t}
            width={innerW}
            height={innerH}
            onPointerMove={onPointer}
            onPointerDown={onPointer}
            onPointerLeave={() => setHover(null)}
          />
        </svg>
        {hover !== null && (
          <div
            class="tip"
            style={
              hoverX(hover) > width * 0.58
                ? { right: `${width - hoverX(hover) + 12}px`, top: `${m.t}px` }
                : { left: `${hoverX(hover) + 12}px`, top: `${m.t}px` }
            }
          >
            <strong>{xTitle(x[hover])}</strong>
            {series.map((s, i) => (
              <span><i class={`swatch-dot series-${i + 1}`} />{s.name}: {format(s.values[hover])}</span>
            ))}
          </div>
        )}
      </div>
      {showTable && (
        <details class="year-table">
          <summary>View the figures</summary>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th scope="col">{xHeading}</th>
                  {series.map((s) => <th scope="col">{s.name}</th>)}
                </tr>
              </thead>
              <tbody>
                {x.map((v, i) => (
                  <tr>
                    <th scope="row">{xTitle(v)}</th>
                    {series.map((s) => <td>{format(s.values[i])}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  );
}
