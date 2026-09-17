import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import type { Provenance } from "@/lib/api";

const VARIANT: Record<Provenance, "ok" | "warn" | "info"> = {
  real: "ok",
  synthetic: "warn",
  assumption: "info",
};

/** A small badge marking a metric's data provenance (real / sample / assumption). */
export function ProvenanceBadge({ provenance }: { provenance: Provenance }) {
  const { t } = useTranslation();
  return <Badge variant={VARIANT[provenance]}>{t(`decide.provenance.${provenance}`)}</Badge>;
}
