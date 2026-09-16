import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";

interface StagePlaceholderProps {
  ordinal: string;
  icon: LucideIcon;
  title: string;
  summary: string;
  description: string;
}

/**
 * A deliberately designed placeholder for a response-loop stage. It names the
 * stage, states what will live there, and presents an honest "arriving later"
 * state — a composed empty state, never a blank panel.
 */
export function StagePlaceholder({
  ordinal,
  icon: Icon,
  title,
  summary,
  description,
}: StagePlaceholderProps) {
  const { t } = useTranslation();

  return (
    <div className="relative flex h-full flex-col bg-grid">
      {/* Vignette so the grid recedes toward the edges. */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,hsl(var(--background))_78%)]"
        aria-hidden
      />

      <div className="relative mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-8 py-16">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-border bg-surface-raised shadow-e2">
              <Icon className="h-7 w-7 text-primary" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="font-mono text-2xs uppercase tracking-[0.2em] text-muted-foreground">
                Stage {ordinal}
              </span>
              <h1 className="text-3xl font-semibold tracking-tight text-foreground">{title}</h1>
            </div>
          </div>

          <p className="max-w-2xl text-balance text-lg text-surface-foreground">{summary}</p>
          <p className="mt-3 max-w-2xl text-balance text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>

          <div className="mt-8 flex items-center gap-3">
            <Badge variant="warn">
              <span className="h-1.5 w-1.5 rounded-full bg-signal-warn" />
              {t("stage.comingSoon")}
            </Badge>
            <div className="h-px flex-1 bg-border" />
          </div>
        </motion.div>
      </div>
    </div>
  );
}
