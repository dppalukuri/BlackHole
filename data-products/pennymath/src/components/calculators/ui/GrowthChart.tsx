import { formatCompactCurrency, formatCurrency } from '../../../lib/formatters';
import LineChart from './LineChart';

interface GrowthChartProps {
  currencyCode: string;
  /** Yearly figures. Year 0 is added from the amount invested at the start. */
  rows: Array<{ year: number; invested: number; total: number }>;
  /** Amount already invested on day one. */
  start?: number;
  valueLabel?: string;
  investedLabel?: string;
  title?: string;
}

/** The standard picture for anything that grows: its value against what went in. */
export default function GrowthChart({
  currencyCode,
  rows,
  start = 0,
  valueLabel = 'Total value',
  investedLabel = 'Amount invested',
  title = 'How your money grows',
}: GrowthChartProps) {
  return (
    <LineChart
      title={title}
      caption="At the end of each year"
      x={[0, ...rows.map((r) => r.year)]}
      series={[
        { name: valueLabel, values: [start, ...rows.map((r) => r.total)] },
        { name: investedLabel, values: [start, ...rows.map((r) => r.invested)] },
      ]}
      format={(n) => formatCurrency(n, currencyCode)}
      formatTick={(n) => formatCompactCurrency(n, currencyCode)}
      xTick={(y) => `Yr ${y}`}
      xTitle={(y) => (y === 0 ? 'Today' : `Year ${y}`)}
    />
  );
}
