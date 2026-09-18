import { useTranslation } from "react-i18next";
import {
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import type { DistrictComparison } from "@/lib/api";

interface RankScatterProps {
  districts: DistrictComparison[];
}

/**
 * Predicted at-risk rank (x) vs. recorded impact rank (y) for each district with
 * recorded data. Points ON the diagonal are well-aligned; points far OFF it are
 * the misses — a district predicted low-priority but hit hard sits off-diagonal.
 * Colour marks under-prioritised districts (recorded worse than predicted).
 */
export function RankScatter({ districts }: RankScatterProps) {
  const { t } = useTranslation();
  const withData = districts.filter((d) => d.has_data);
  const n = withData.length;
  if (n < 2) return null;

  const colorFor = (d: DistrictComparison) => {
    if (d.under_prioritised) return "hsl(var(--signal-crit))";
    if (d.rank_delta <= -2) return "hsl(var(--signal-warn))";
    return "hsl(var(--signal-ok))";
  };

  const data = withData.map((d) => ({ x: d.predicted_rank, y: d.impact_rank, name: d.name }));
  const domain = [0.5, n + 0.5] as [number, number];
  const axisTick = { fontSize: 10, fill: "hsl(var(--muted-foreground))" };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 12, right: 24, bottom: 28, left: 8 }}>
          <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
          <ReferenceLine
            segment={[
              { x: 1, y: 1 },
              { x: n, y: n },
            ]}
            stroke="hsl(var(--muted-foreground))"
            strokeDasharray="4 4"
          />
          <XAxis
            type="number"
            dataKey="x"
            domain={domain}
            reversed
            allowDecimals={false}
            tick={axisTick}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
            label={{
              value: t("learn.predictedRankAxis"),
              position: "bottom",
              fontSize: 11,
              fill: "hsl(var(--muted-foreground))",
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={domain}
            reversed
            allowDecimals={false}
            tick={axisTick}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
            label={{
              value: t("learn.recordedRankAxis"),
              angle: -90,
              position: "insideLeft",
              fontSize: 11,
              fill: "hsl(var(--muted-foreground))",
            }}
          />
          <ZAxis range={[90, 90]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            contentStyle={{
              background: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
              color: "hsl(var(--popover-foreground))",
            }}
            formatter={(value: unknown, key: unknown) => [
              `#${value}`,
              key === "x" ? t("learn.predictedRankAxis") : t("learn.recordedRankAxis"),
            ]}
            labelFormatter={() => ""}
          />
          <Scatter data={data} isAnimationActive={false}>
            {withData.map((d) => (
              <Cell key={d.pcode} fill={colorFor(d)} />
            ))}
            <LabelList
              dataKey="name"
              position="top"
              style={{ fontSize: 10, fill: "hsl(var(--foreground))" }}
            />
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
