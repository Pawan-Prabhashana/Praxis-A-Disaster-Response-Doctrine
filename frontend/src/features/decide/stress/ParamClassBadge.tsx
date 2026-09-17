import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import type { ParamClass } from "@/lib/api";

const VARIANT: Record<ParamClass, "ok" | "info" | "warn"> = {
  real_uncertainty: "ok",
  assumption: "info",
  synthetic_derived: "warn",
};

/** Badge marking an uncertainty parameter's honesty class. */
export function ParamClassBadge({ paramClass }: { paramClass: ParamClass }) {
  const { t } = useTranslation();
  return <Badge variant={VARIANT[paramClass]}>{t(`decide.paramClass.${paramClass}`)}</Badge>;
}
