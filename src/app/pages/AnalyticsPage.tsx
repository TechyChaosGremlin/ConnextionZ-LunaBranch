// ─── ANALYTICS ───────────────────────────────────────────────────────────────
//
// Charting rules applied here: one measure per chart (never a second y-axis),
// a single hue because each chart shows a single series, thin marks with 4px
// rounded data-ends anchored to the baseline, a 2px gap between bars, recessive
// gridlines, and a tap/hover readout instead of a label on every bar.

import { useState, type ReactNode } from "react";
import { motion } from "motion/react";
import { Eye, Heart, Star, TrendingUp, Users } from "lucide-react";
import { ACCENT, Group, Row, SubPage } from "../settings-ui";
import type { Tokens } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

const VIEWS_BY_DAY = [
  { day: "Mon", value: 12400 },
  { day: "Tue", value: 18900 },
  { day: "Wed", value: 15200 },
  { day: "Thu", value: 27600 },
  { day: "Fri", value: 41300 },
  { day: "Sat", value: 38700 },
  { day: "Sun", value: 22100 },
];

const COLLAB_SOURCES = [
  { label: "Music", value: 34 },
  { label: "Brand Deal", value: 26 },
  { label: "Video", value: 18 },
  { label: "Podcast", value: 14 },
  { label: "Gaming", value: 8 },
];

const compact = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + "M" : n >= 1_000 ? (n / 1_000).toFixed(1) + "K" : String(n);

function StatTile({ icon, label, value, delta, t }: {
  icon: ReactNode; label: string; value: string; delta: string; t: Tokens;
}) {
  return (
    <div className="rounded-2xl p-4" style={{ background: t.groupBg, border: t.groupBorder }}>
      <div className="flex items-center gap-2 mb-2.5" style={{ color: t.sub }}>
        {icon}
        <span className="text-[11px] font-bold uppercase tracking-widest">{label}</span>
      </div>
      <p className="font-extrabold text-[24px] leading-none" style={{ color: t.heading }}>{value}</p>
      <p className="text-[12px] mt-1.5 font-semibold" style={{ color: "#22c55e" }}>↑ {delta}</p>
    </div>
  );
}

/** Single-series bar chart. One hue, so no legend — the heading names the series. */
function ViewsChart({ t }: { t: Tokens }) {
  const [active, setActive] = useState<number | null>(null);
  const peak = Math.max(...VIEWS_BY_DAY.map((d) => d.value));
  const shown = active ?? VIEWS_BY_DAY.findIndex((d) => d.value === peak);
  const total = VIEWS_BY_DAY.reduce((s, d) => s + d.value, 0);

  return (
    <div className="rounded-2xl p-4 mb-5" style={{ background: t.groupBg, border: t.groupBorder }}>
      <div className="flex items-baseline justify-between mb-1">
        <p className="text-[14px] font-bold" style={{ color: t.heading }}>Views this week</p>
        <p className="text-[13px] font-semibold" style={{ color: t.sub }}>{compact(total)} total</p>
      </div>
      {/* Readout replaces per-bar labels: one value at a time, always legible. */}
      <p className="text-[12px] mb-4" style={{ color: t.sub }}>
        <span className="font-bold" style={{ color: ACCENT }}>{compact(VIEWS_BY_DAY[shown].value)}</span>
        {" "}on {VIEWS_BY_DAY[shown].day}{active === null && " — your best day"}
      </p>

      <div className="flex items-end gap-[2px] h-32" role="img"
        aria-label={`Daily views: ${VIEWS_BY_DAY.map((d) => `${d.day} ${compact(d.value)}`).join(", ")}`}>
        {VIEWS_BY_DAY.map((d, i) => (
          <button key={d.day}
            onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)}
            onClick={() => setActive(active === i ? null : i)}
            aria-label={`${d.day}: ${compact(d.value)} views`}
            className="flex-1 h-full flex flex-col justify-end">
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${(d.value / peak) * 100}%` }}
              transition={{ duration: 0.5, delay: i * 0.05, ease: [0.2, 0.8, 0.2, 1] }}
              style={{
                background: ACCENT,
                borderRadius: "4px 4px 0 0",
                opacity: active === null || active === i ? 1 : 0.35,
              }}
            />
          </button>
        ))}
      </div>
      <div className="flex gap-[2px] mt-2" style={{ borderTop: `1px solid ${t.divider}`, paddingTop: 6 }}>
        {VIEWS_BY_DAY.map((d, i) => (
          <span key={d.day} className="flex-1 text-center text-[11px] font-semibold"
            style={{ color: shown === i ? ACCENT : t.sub }}>
            {d.day}
          </span>
        ))}
      </div>
    </div>
  );
}

/** Ranked magnitude, one hue, every row direct-labelled — no legend needed. */
function SourcesChart({ t }: { t: Tokens }) {
  const peak = Math.max(...COLLAB_SOURCES.map((s) => s.value));
  return (
    <div className="rounded-2xl p-4 mb-5" style={{ background: t.groupBg, border: t.groupBorder }}>
      <p className="text-[14px] font-bold mb-1" style={{ color: t.heading }}>Collab requests by type</p>
      <p className="text-[12px] mb-4" style={{ color: t.sub }}>Last 30 days</p>
      <div className="space-y-3">
        {COLLAB_SOURCES.map((s) => (
          <div key={s.label}>
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-[13px]" style={{ color: t.body }}>{s.label}</span>
              <span className="text-[13px] font-bold" style={{ color: t.heading }}>{s.value}</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: t.switchOff }}>
              <motion.div initial={{ width: 0 }} animate={{ width: `${(s.value / peak) * 100}%` }}
                transition={{ duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
                className="h-full rounded-full" style={{ background: ACCENT }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalyticsPage({ prefs, t, onBack, onNavigate }: PageProps) {
  const acceptedRate = 68;

  return (
    <SubPage title="Analytics" subtitle="How your work and collabs are performing" onBack={onBack} t={t}>
      <div className="grid grid-cols-2 gap-3 mb-5">
        <StatTile icon={<Eye className="w-3.5 h-3.5" />} label="Views" value="176.2K" delta="18% vs last week" t={t} />
        <StatTile icon={<Heart className="w-3.5 h-3.5" />} label="Likes" value="42.8K" delta="12% vs last week" t={t} />
        <StatTile icon={<Users className="w-3.5 h-3.5" />} label="Collabs" value="27" delta="4 this month" t={t} />
        <StatTile icon={<Star className="w-3.5 h-3.5" />} label="Collab Score" value="4.8" delta="0.2 this quarter" t={t} />
      </div>

      <ViewsChart t={t} />
      <SourcesChart t={t} />

      <Group label="Collab funnel" t={t}>
        <Row label="Requests received" right={<span className="text-[14px] font-bold" style={{ color: t.heading }}>100</span>} t={t} />
        <Row label="Accepted" right={<span className="text-[14px] font-bold" style={{ color: t.heading }}>{acceptedRate}</span>} t={t} />
        <Row label="Completed" right={<span className="text-[14px] font-bold" style={{ color: t.heading }}>54</span>} t={t} />
        <Row label="Average reply time" last
          right={<span className="text-[14px] font-bold" style={{ color: ACCENT }}>{prefs.responseTime}</span>} t={t} />
      </Group>

      <Group label="Improve your numbers" t={t}>
        <Row label="Response time" sub="Faster replies raise your Collab Score"
          onClick={() => onNavigate("responseTime")} t={t}
          right={<TrendingUp className="w-4 h-4" style={{ color: ACCENT }} />} />
        <Row label="Portfolio" sub="Profiles with 3+ pieces get more requests" last
          onClick={() => onNavigate("portfolio")} t={t}
          right={<TrendingUp className="w-4 h-4" style={{ color: ACCENT }} />} />
      </Group>

      <p className="text-[12px] leading-relaxed px-1 text-center" style={{ color: t.sub }}>
        Prototype figures — a live build reads these from your account.
      </p>
    </SubPage>
  );
}