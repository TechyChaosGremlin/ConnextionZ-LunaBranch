// ─── ANALYTICS ───────────────────────────────────────────────────────────────
//
// Charting rules applied here: one measure per chart (never a second y-axis),
// a single hue because each chart shows a single series, thin marks with 4px
// rounded data-ends anchored to the baseline, a 2px gap between bars, recessive
// gridlines, and a tap/hover readout instead of a label on every bar.

import type { PageProps } from "./settingsPages.types";
import { DashboardScreen } from "../Dashboard";

export function AnalyticsPage({ onBack }: PageProps) {
  return <DashboardScreen onBack={onBack} />;
}