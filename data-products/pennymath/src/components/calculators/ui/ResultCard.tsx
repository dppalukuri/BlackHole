import { formatCurrency } from '../../../lib/formatters';

interface ResultCardProps {
  results: Array<{
    label: string;
    value: number;
    highlight?: boolean;
  }>;
  currencyCode: string;
}

export default function ResultCard({ results, currencyCode }: ResultCardProps) {
  return (
    <div class="result-card">
      {results.map((r) => (
        <div class={`result-item ${r.highlight ? 'result-highlight' : ''}`}>
          <span class="result-label">{r.label}</span>
          <span class="result-value">{formatCurrency(r.value, currencyCode)}</span>
        </div>
      ))}
    </div>
  );
}
