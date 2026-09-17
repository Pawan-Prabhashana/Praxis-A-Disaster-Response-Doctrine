import { useTranslation } from "react-i18next";
import { Bar, BarChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DistributionSummary } from "@/lib/api";

interface StressHistogramProps {
  summary: DistributionSummary;
  point: number;
  target: number;
}

/**
 * Distribution of the overall score across Monte Carlo iterations, with the
 * p05–p95 band, median, deterministic point score, and target marked. The
 * downside (p05 / worst-plausible) is drawn in the critical colour.
 */
export function StressHistogram({ summary, point, target }: StressHistogramProps) {
  const { t } = useTranslation();
  const data = summary.histogram.map((b) => ({ x: (b.start + b.end) / 2, count: b.count }));

  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -22 }}>
          <XAxis
            dataKey="x"
            type="number"
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
              color: "hsl(var(--popover-foreground))",
            }}
            formatter={(value: unknown) => [`${value}`, t("decide.stress.iterations")]}
            labelFormatter={(label: unknown) =>
              `${t("decide.stress.score")} ≈ ${Math.round(Number(label))}`
            }
          />
          {/* p05–p95 band edges */}
          <ReferenceLine x={summary.p05} stroke="hsl(var(--signal-crit))" strokeWidth={1.5} />
          <ReferenceLine
            x={summary.p95}
            stroke="hsl(var(--muted-foreground))"
            strokeDasharray="3 3"
          />
          <ReferenceLine x={summary.median} stroke="hsl(var(--signal-info))" strokeWidth={2} />
          <ReferenceLine
            x={point}
            stroke="hsl(var(--foreground))"
            strokeDasharray="2 2"
            strokeOpacity={0.6}
          />
          <ReferenceLine x={target} stroke="hsl(var(--primary))" strokeDasharray="4 2" />
          <Bar
            dataKey="count"
            fill="hsl(var(--signal-info))"
            fillOpacity={0.45}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
