import { Activity } from "lucide-react";
import { useTranslation } from "react-i18next";

import { StagePlaceholder } from "@/components/shell/StagePlaceholder";

export default function DecideRoute() {
  const { t } = useTranslation();
  return (
    <StagePlaceholder
      ordinal="02"
      icon={Activity}
      title={t("stage.decide.title")}
      summary={t("stage.decide.summary")}
      description={t("stage.decide.description")}
    />
  );
}
