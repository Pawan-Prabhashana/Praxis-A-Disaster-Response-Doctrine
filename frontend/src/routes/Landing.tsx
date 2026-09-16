import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { LogoMark } from "@/components/shell/Logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LOOP_ITEMS } from "@/config/nav";
import { cn } from "@/lib/utils";

const STAGE_SUMMARY_KEYS: Record<string, string> = {
  "/sense": "stage.sense.summary",
  "/decide": "stage.decide.summary",
  "/act": "stage.act.summary",
  "/learn": "stage.learn.summary",
};

export default function LandingRoute() {
  const { t } = useTranslation();

  return (
    <div className="relative min-h-full bg-grid">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,transparent_0%,hsl(var(--background))_70%)]"
        aria-hidden
      />

      <div className="relative mx-auto w-full max-w-6xl px-8 py-16">
        {/* Hero */}
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-3xl"
        >
          <div className="mb-6 flex items-center gap-3">
            <LogoMark className="h-9 w-9" />
            <Badge variant="outline">{t("landing.kicker")}</Badge>
          </div>
          <h1 className="text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            {t("landing.title")}
          </h1>
          <p className="mt-5 max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            {t("landing.subtitle")}
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link to="/sense">
                {t("landing.enter")}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Sri Lanka · DMC
            </span>
          </div>
        </motion.section>

        {/* The response loop */}
        <section className="mt-16">
          <div className="mb-5 flex items-center gap-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {t("landing.loopTitle")}
            </h2>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {LOOP_ITEMS.map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.path}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.4,
                    delay: 0.1 + index * 0.08,
                    ease: [0.22, 1, 0.36, 1],
                  }}
                >
                  <Link
                    to={item.path}
                    className={cn(
                      "group relative flex h-full flex-col rounded-lg border border-border bg-card p-5 shadow-e2 transition-all",
                      "hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-e3",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    )}
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-surface-raised text-primary">
                        <Icon className="h-5 w-5" />
                      </span>
                      <span className="font-mono text-2xs text-muted-foreground/60">
                        {item.ordinal}
                      </span>
                    </div>
                    <h3 className="text-base font-semibold text-foreground">{t(item.labelKey)}</h3>
                    <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">
                      {t(STAGE_SUMMARY_KEYS[item.path] ?? "")}
                    </p>
                    <span className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
                      Open
                      <ArrowRight className="h-3.5 w-3.5" />
                    </span>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
