import { useTranslation } from "react-i18next";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Playbook } from "@/lib/api";

const SERIES_COLORS = ["hsl(var(--primary))", "hsl(var(--signal-info))", "hsl(var(--signal-ok))"];
const METRIC_KEYS = [
  "population_coverage",
  "shelter_adequacy",
  "accessibility",
  "resource_adequacy",
];

/** Grouped bars: each metric's sub-score (0–100) across the selected playbooks. */
export function CompareChart({ playbooks }: { playbooks: Playbook[] }) {
  const { t } = useTranslation();

  const data = METRIC_KEYS.map((key) => {
    const row: Record<string, string | number> = { metric: t(`decide.metricShort.${key}`) };
    for (const pb of playbooks) {
      const m = pb.score_result?.metrics.find((x) => x.key === key);
      row[`pb-${pb.id}`] = m ? Math.round(m.score * 100) : 0;
    }
    return row;
  });

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
          <XAxis
            dataKey="metric"
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
          />
          <YAxis
            domain={[0, 100]}
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
            cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {playbooks.map((pb, i) => (
            <Bar
              key={pb.id}
              dataKey={`pb-${pb.id}`}
              name={pb.name}
              fill={SERIES_COLORS[i % SERIES_COLORS.length]}
              radius={[3, 3, 0, 0]}
              isAnimationActive={false}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
