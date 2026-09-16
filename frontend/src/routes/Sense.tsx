import { Radar } from "lucide-react";
import { useTranslation } from "react-i18next";

import { StagePlaceholder } from "@/components/shell/StagePlaceholder";

export default function SenseRoute() {
  const { t } = useTranslation();
  return (
    <StagePlaceholder
      ordinal="01"
      icon={Radar}
      title={t("stage.sense.title")}
      summary={t("stage.sense.summary")}
      description={t("stage.sense.description")}
    />
  );
}
