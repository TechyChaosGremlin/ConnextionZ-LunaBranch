// ─── COLLAB PREFERENCES ──────────────────────────────────────────────────────

import { Check } from "lucide-react";
import { BUDGET_OPTIONS } from "../settings-store";
import { ACCENT, Chip, Group, Row, SubPage, ToggleRow } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

const COLLAB_TYPE_OPTIONS = [
  { label: "Paid Collaboration", sub: "Compensated for your time and reach" },
  { label: "Free / Creative Collab", sub: "Purely for the content" },
  { label: "Duet / Remix", sub: "Respond to or remix another creator's post" },
  { label: "Podcast / Interview", sub: "Guest on shows, or host others" },
  { label: "Brand Deal", sub: "Sponsored content with brand partners" },
];

const CATEGORY_OPTIONS = [
  "Music", "Fitness", "Travel", "Cooking", "Art", "Tech", "Gaming", "Fashion", "Business",
];

export function CollabPreferencesPage({ prefs, t, onBack, onPatch, onNavigate }: PageProps) {
  const c = prefs.collab;
  const set = (patch: Partial<typeof c>) => onPatch({ collab: { ...c, ...patch } });

  const toggleType = (label: string) =>
    set({ types: c.types.includes(label) ? c.types.filter((x) => x !== label) : [...c.types, label] });

  const toggleCategory = (label: string) =>
    onPatch({
      categories: prefs.categories.includes(label)
        ? prefs.categories.filter((x) => x !== label)
        : [...prefs.categories, label],
    });

  return (
    <SubPage title="Collab Preferences" subtitle="What you're open to, and from whom" onBack={onBack} t={t}>
      <Group label="Availability" t={t}>
        <ToggleRow label="Open to collaborations" sub="Shows the ✦ Open to Collab badge on your posts" last
          value={c.openToCollab} onChange={(v) => set({ openToCollab: v })} t={t} />
      </Group>

      <Group label="Collab types" hint="Creators see these on your profile so they know how to approach you." t={t}>
        {COLLAB_TYPE_OPTIONS.map((o, i) => (
          <button key={o.label} onClick={() => toggleType(o.label)}
            className="w-full flex items-center px-4 py-4 text-left transition-opacity active:opacity-70"
            style={{ borderBottom: i === COLLAB_TYPE_OPTIONS.length - 1 ? "none" : `1px solid ${t.divider}` }}>
            <div className="min-w-0 flex-1 pr-3">
              <p className="text-[14px]" style={{ color: c.types.includes(o.label) ? ACCENT : t.body, fontWeight: c.types.includes(o.label) ? 700 : 400 }}>
                {o.label}
              </p>
              <p className="text-[12px] mt-0.5" style={{ color: t.sub }}>{o.sub}</p>
            </div>
            <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
              style={{
                background: c.types.includes(o.label) ? ACCENT : "transparent",
                border: c.types.includes(o.label) ? `1px solid ${ACCENT}` : `1.5px solid ${t.chevron}`,
              }}>
              {c.types.includes(o.label) && <Check className="w-3.5 h-3.5 text-white" strokeWidth={3} />}
            </div>
          </button>
        ))}
      </Group>

      <div className="mb-5">
        <p className="text-[11px] font-bold uppercase tracking-widest mb-2 px-1" style={{ color: t.sectionLbl }}>
          Typical budget
        </p>
        <div className="flex flex-wrap gap-2">
          {BUDGET_OPTIONS.map((b) => (
            <Chip key={b} label={b} selected={c.budget === b} onClick={() => set({ budget: b })} t={t} />
          ))}
        </div>
      </div>

      <div className="mb-5">
        <p className="text-[11px] font-bold uppercase tracking-widest mb-2 px-1" style={{ color: t.sectionLbl }}>
          What you create
        </p>
        <div className="flex flex-wrap gap-2">
          {CATEGORY_OPTIONS.map((cat) => (
            <Chip key={cat} label={cat} selected={prefs.categories.includes(cat)}
              onClick={() => toggleCategory(cat)} t={t} />
          ))}
        </div>
        <p className="text-[12px] leading-relaxed mt-2 px-1" style={{ color: t.sub }}>
          Your feed is personalised around these picks.
        </p>
      </div>

      <Group label="Screening" t={t}>
        <ToggleRow label="Auto-screen requests" sub="Hide requests from low-rated creators"
          value={c.autoScreen} onChange={(v) => set({ autoScreen: v })} t={t} />
        <div className="px-4 py-4" style={{ opacity: c.autoScreen ? 1 : 0.4, pointerEvents: c.autoScreen ? "auto" : "none" }}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-[14px]" style={{ color: t.body }}>Minimum Collab Score</span>
            <span className="text-[14px] font-bold" style={{ color: ACCENT }}>⭐ {c.minCollabScore.toFixed(1)}</span>
          </div>
          <input type="range" min={1} max={5} step={0.1} value={c.minCollabScore}
            onChange={(e) => set({ minCollabScore: Number(e.target.value) })}
            aria-label="Minimum Collab Score"
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, ${ACCENT} ${((c.minCollabScore - 1) / 4) * 100}%, ${t.switchOff} ${((c.minCollabScore - 1) / 4) * 100}%)`,
            }} />
          <div className="flex justify-between mt-1.5">
            <span className="text-[11px]" style={{ color: t.sub }}>1.0</span>
            <span className="text-[11px]" style={{ color: t.sub }}>5.0</span>
          </div>
        </div>
        <ToggleRow label="Remote collabs only" sub="Filter out anything requiring travel" last
          value={c.remoteOnly} onChange={(v) => set({ remoteOnly: v })} t={t} />
      </Group>

      <Group label="Related" t={t}>
        <Row label="Response time" sub="How fast you typically reply" onClick={() => onNavigate("responseTime")} last t={t}
          right={<span className="text-[13px]" style={{ color: t.sub }}>{prefs.responseTime}</span>} />
      </Group>
    </SubPage>
  );
}