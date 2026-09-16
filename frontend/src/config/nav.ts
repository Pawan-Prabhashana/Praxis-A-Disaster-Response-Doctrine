/**
 * Primary navigation model. The four stages of the response loop plus the
 * overview landing. Keeping this declarative lets the sidebar, routes, and any
 * future breadcrumb share one source of truth.
 */

import { Activity, ClipboardCheck, GraduationCap, LayoutDashboard, Radar } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  /** Route path. */
  path: string;
  /** i18n key for the visible label. */
  labelKey: string;
  /** Short ordinal shown in the rail (e.g. loop position). */
  ordinal: string | null;
  icon: LucideIcon;
}

export const OVERVIEW_ITEM: NavItem = {
  path: "/",
  labelKey: "nav.overview",
  ordinal: null,
  icon: LayoutDashboard,
};

/** The Sense → Decide → Act → Learn loop, in order. */
export const LOOP_ITEMS: readonly NavItem[] = [
  { path: "/sense", labelKey: "nav.sense", ordinal: "01", icon: Radar },
  { path: "/decide", labelKey: "nav.decide", ordinal: "02", icon: Activity },
  { path: "/act", labelKey: "nav.act", ordinal: "03", icon: ClipboardCheck },
  { path: "/learn", labelKey: "nav.learn", ordinal: "04", icon: GraduationCap },
] as const;
