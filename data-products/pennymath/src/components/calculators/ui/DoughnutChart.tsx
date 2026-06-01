import { useRef, useEffect } from 'preact/hooks';

interface DoughnutChartProps {
  segments: Array<{
    label: string;
    value: number;
    color: string;
  }>;
  /** BCP-47 locale for tooltip number formatting. Defaults to `en-IN`. */
  locale?: string;
}

export default function DoughnutChart({ segments, locale = 'en-IN' }: DoughnutChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    import('chart.js').then(({ Chart, ArcElement, Tooltip, Legend, DoughnutController }) => {
      Chart.register(ArcElement, Tooltip, Legend, DoughnutController);

      if (chartRef.current) {
        chartRef.current.data.labels = segments.map((s) => s.label);
        chartRef.current.data.datasets[0].data = segments.map((s) => s.value);
        chartRef.current.data.datasets[0].backgroundColor = segments.map((s) => s.color);
        chartRef.current.update();
        return;
      }

      chartRef.current = new Chart(canvasRef.current!, {
        type: 'doughnut',
        data: {
          labels: segments.map((s) => s.label),
          datasets: [
            {
              data: segments.map((s) => s.value),
              backgroundColor: segments.map((s) => s.color),
              borderWidth: 0,
              hoverOffset: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          cutout: '65%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 16,
                usePointStyle: true,
                pointStyleWidth: 12,
                font: { size: 13 },
              },
            },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const val = ctx.parsed;
                  const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0);
                  const pct = ((val / total) * 100).toFixed(1);
                  return ` ${ctx.label}: ${val.toLocaleString(locale)} (${pct}%)`;
                },
              },
            },
          },
        },
      });
    });

    return () => {
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, []);

  // Update chart data when segments change (without re-creating)
  useEffect(() => {
    if (!chartRef.current) return;
    chartRef.current.data.labels = segments.map((s) => s.label);
    chartRef.current.data.datasets[0].data = segments.map((s) => s.value);
    chartRef.current.update();
  }, [segments.map((s) => s.value).join(',')]);

  return (
    <div class="chart-container">
      <canvas ref={canvasRef} />
    </div>
  );
}
