/** Pure layout maths for LineChart, kept apart from the component so it can be tested. */

/** Evenly spaced round ticks covering `lo` to `hi`, using steps of 1, 2 or 5 × 10^k. */
export function niceTicks(lo: number, hi: number, count = 4): number[] {
  if (!(hi > lo)) {
    const pad = Math.abs(hi) * 0.05 || 1;
    lo -= pad;
    hi += pad;
  }
  const raw = (hi - lo) / count;
  const power = Math.pow(10, Math.floor(Math.log10(raw)));
  const unit = raw / power;
  const step = (unit <= 1 ? 1 : unit <= 2 ? 2 : unit <= 5 ? 5 : 10) * power;
  const first = Math.floor(lo / step + 1e-9);
  const last = Math.ceil(hi / step - 1e-9);
  const ticks: number[] = [];
  for (let i = first; i <= last; i++) ticks.push(Number((i * step).toPrecision(12)));
  return ticks;
}

/**
 * Moves label positions apart so none sit closer than `gap`, disturbing them as
 * little as possible and keeping them between `min` and `max`. Returns positions
 * in the same order as the input.
 */
export function spreadLabels(positions: number[], gap: number, min: number, max: number): number[] {
  const order = positions.map((_, i) => i).sort((a, b) => positions[a] - positions[b]);
  const placed = order.map((i) => positions[i]);
  for (let i = 1; i < placed.length; i++) {
    if (placed[i] - placed[i - 1] < gap) placed[i] = placed[i - 1] + gap;
  }
  // Pushing down can overrun the bottom, so walk back up and re-centre the group.
  const overflow = placed.length ? placed[placed.length - 1] - max : 0;
  if (overflow > 0) {
    placed[placed.length - 1] = max;
    for (let i = placed.length - 2; i >= 0; i--) {
      if (placed[i + 1] - placed[i] < gap) placed[i] = placed[i + 1] - gap;
    }
  }
  if (placed.length && placed[0] < min) {
    placed[0] = min;
    for (let i = 1; i < placed.length; i++) {
      if (placed[i] - placed[i - 1] < gap) placed[i] = placed[i - 1] + gap;
    }
  }
  const out = new Array<number>(positions.length);
  order.forEach((originalIndex, sortedIndex) => { out[originalIndex] = placed[sortedIndex]; });
  return out;
}

/** The index of the x value nearest to `value`. */
export function nearestIndex(xs: number[], value: number): number {
  let best = 0;
  for (let i = 1; i < xs.length; i++) {
    if (Math.abs(xs[i] - value) < Math.abs(xs[best] - value)) best = i;
  }
  return best;
}
