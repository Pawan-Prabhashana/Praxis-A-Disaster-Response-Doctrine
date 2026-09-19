import { Check, Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

const SHORT: Record<SupportedLanguage, string> = { en: "EN", si: "සිං", ta: "தமிழ்" };

/**
 * Language switcher (English / Sinhala / Tamil). The choice is persisted in the
 * UI store and applied to i18next + the document `lang` attribute. A note states
 * that data (district names, sources) stays English — only the interface is
 * localized.
 */
export function LanguageSwitcher() {
  const { t } = useTranslation();
  const language = useUiStore((s) => s.language);
  const setLanguage = useUiStore((s) => s.setLanguage);

  return (
    <DropdownMenu>
      <Tooltip>
        <TooltipTrigger asChild>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label={t("language.label")}
              className="flex items-center gap-1.5 rounded-md border border-border bg-surface-raised px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Languages className="h-4 w-4 text-muted-foreground" />
              <span>{SHORT[language]}</span>
            </button>
          </DropdownMenuTrigger>
        </TooltipTrigger>
        <TooltipContent>{t("language.label")}</TooltipContent>
      </Tooltip>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel>{t("language.label")}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {SUPPORTED_LANGUAGES.map((lng) => (
          <DropdownMenuItem
            key={lng}
            onSelect={() => setLanguage(lng)}
            className="flex items-center gap-2"
          >
            <Check
              className={cn(
                "h-4 w-4 shrink-0 text-primary",
                lng === language ? "opacity-100" : "opacity-0",
              )}
            />
            <span className="text-sm text-foreground">{t(`language.${lng}`)}</span>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <p className="px-2 py-1.5 text-2xs leading-snug text-muted-foreground">
          {t("language.dataNote")}
        </p>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
