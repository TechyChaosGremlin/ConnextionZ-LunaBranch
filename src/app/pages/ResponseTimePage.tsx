// ─── RESPONSE TIME ───────────────────────────────────────────────────────────

import { Clock } from "lucide-react";
import { RESPONSE_TIME_OPTIONS } from "../settings-store";
import { ACCENT, Callout, ChoiceRow, Group, SubPage } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

export function ResponseTimePage({ prefs, t, onBack, onPatch }: PageProps) {
  return (
    <SubPage title="Response Time" subtitle="Set expectations before someone reaches out" onBack={onBack} t={t}>
      <Callout icon={<Clock className="w-4 h-4" />} t={t}>
        This shows on your profile and in collab requests. Creators who reply inside their stated
        window keep a higher Collab Score, so pick the one you can actually hold.
      </Callout>

      <Group label="Typical response time" t={t}>
        {RESPONSE_TIME_OPTIONS.map((o, i) => (
          <ChoiceRow key={o.value} label={o.label} sub={o.sub}
            selected={prefs.responseTime === o.value}
            onSelect={() => onPatch({ responseTime: o.value })}
            last={i === RESPONSE_TIME_OPTIONS.length - 1} t={t} />
        ))}
      </Group>

      <div className="rounded-2xl p-4" style={{ background: t.cardBg, border: t.cardBorder }}>
        <p className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: t.sectionLbl }}>
          How your profile will read
        </p>
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: "rgba(0,174,239,0.15)" }}>
            <Clock className="w-4 h-4" style={{ color: ACCENT }} />
          </div>
          <div>
            <p className="text-[14px] font-bold" style={{ color: t.heading }}>Usually replies {prefs.responseTime}</p>
            <p className="text-[12px]" style={{ color: t.sub }}>Shown on every collab request you receive</p>
          </div>
        </div>
      </div>
    </SubPage>
  );
}