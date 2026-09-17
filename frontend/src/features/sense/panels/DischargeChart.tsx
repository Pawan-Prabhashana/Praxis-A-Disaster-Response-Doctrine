import { Area, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { RiverPointDischarge } from "@/lib/api";

interface DischargeChartProps {
  data: RiverPointDischarge;
}

/**
 * GloFAS ensemble river-discharge mini-chart: the median line inside the
 * p25–p75 band. For a historical reanalysis the ensemble collapses (band ≈
 * line) — that is the real signal, and the band widens for live forecasts,
 * which is the uncertainty Phase 5 stress-tests.
 */
export function DischargeChart({ data }: DischargeChartProps) {
  const rows = data.series.map((d) => {
    const median = d.median ?? d.mean;
    const low = d.p25 ?? median;
    const high = d.p75 ?? median;
    return {
      date: d.valid_date.slice(5), // MM-DD
      band: [low, high] as [number | null, number | null],
      median,
    };
  });

  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 6, right: 6, bottom: 0, left: -18 }}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
            interval="preserveStartEnd"
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
            width={40}
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
              color: "hsl(var(--popover-foreground))",
            }}
            labelStyle={{ color: "hsl(var(--muted-foreground))" }}
            formatter={(value: unknown, name: string) => {
              if (name === "band" && Array.isArray(value)) {
                return [`${value[0]?.toFixed?.(1)}–${value[1]?.toFixed?.(1)} m³/s`, "p25–p75"];
              }
              return [`${typeof value === "number" ? value.toFixed(1) : value} m³/s`, "median"];
            }}
          />
          <Area
            type="monotone"
            dataKey="band"
            stroke="none"
            fill="hsl(var(--signal-info))"
            fillOpacity={0.18}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="median"
            stroke="hsl(var(--signal-info))"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
