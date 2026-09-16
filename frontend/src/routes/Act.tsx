import { ClipboardCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import { StagePlaceholder } from "@/components/shell/StagePlaceholder";

export default function ActRoute() {
  const { t } = useTranslation();
  return (
    <StagePlaceholder
      ordinal="03"
      icon={ClipboardCheck}
      title={t("stage.act.title")}
      summary={t("stage.act.summary")}
      description={t("stage.act.description")}
    />
  );
}
