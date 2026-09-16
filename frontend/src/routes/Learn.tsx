import { GraduationCap } from "lucide-react";
import { useTranslation } from "react-i18next";

import { StagePlaceholder } from "@/components/shell/StagePlaceholder";

export default function LearnRoute() {
  const { t } = useTranslation();
  return (
    <StagePlaceholder
      ordinal="04"
      icon={GraduationCap}
      title={t("stage.learn.title")}
      summary={t("stage.learn.summary")}
      description={t("stage.learn.description")}
    />
  );
}
