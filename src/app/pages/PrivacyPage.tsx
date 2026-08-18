// ─── PRIVACY SETTINGS ────────────────────────────────────────────────────────

import { Shield } from "lucide-react";
import type { Audience } from "../settings-store";
import { AUDIENCE_OPTIONS } from "../settings-store";
import { Callout, ChoiceRow, Group, SubPage, ToggleRow } from "../settings-ui";
import type { Tokens } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

function AudienceGroup({ label, hint, value, onChange, t }: {
  label: string; hint?: string; value: Audience; onChange: (v: Audience) => void; t: Tokens;
}) {
  return (
    <Group label={label} hint={hint} t={t}>
      {AUDIENCE_OPTIONS.map((o, i) => (
        <ChoiceRow key={o.value} label={o.label} selected={value === o.value}
          onSelect={() => onChange(o.value)} last={i === AUDIENCE_OPTIONS.length - 1} t={t} />
      ))}
    </Group>
  );
}

export function PrivacyPage({ prefs, t, onBack, onPatch }: PageProps) {
  const p = prefs.privacy;
  const set = (patch: Partial<typeof p>) => onPatch({ privacy: { ...p, ...patch } });

  return (
    <SubPage title="Privacy Settings" subtitle="Who can see you and reach you" onBack={onBack} t={t}>
      <Group label="Account" hint="A private account still appears in Discover unless you also turn off discoverability below." t={t}>
        <ToggleRow label="Private account" sub="Only approved followers see your posts" last
          value={p.privateAccount} onChange={(v) => set({ privateAccount: v })} t={t} />
      </Group>

      <AudienceGroup label="Who can message you" value={p.whoCanMessage}
        onChange={(v) => set({ whoCanMessage: v })} t={t} />

      <AudienceGroup label="Who can send collab requests" value={p.whoCanCollab}
        onChange={(v) => set({ whoCanCollab: v })} t={t}
        hint="Set this to “No one” and your profile shows as closed to collabs." />

      <Group label="Profile visibility" t={t}>
        <ToggleRow label="Show Collab Score" sub="Your rating and collab count on your profile"
          value={p.showCollabScore} onChange={(v) => set({ showCollabScore: v })} t={t} />
        <ToggleRow label="Show online status" sub="The green dot in Inbox conversations"
          value={p.showOnlineStatus} onChange={(v) => set({ showOnlineStatus: v })} t={t} />
        <ToggleRow label="Allow mentions" sub="Others can tag @you in captions and comments" last
          value={p.allowMentions} onChange={(v) => set({ allowMentions: v })} t={t} />
      </Group>

      <Group label="Data" t={t}>
        <ToggleRow label="Appear in Discover" sub="Your profile can surface in search and trending"
          value={p.discoverable} onChange={(v) => set({ discoverable: v })} t={t} />
        <ToggleRow label="Personalised recommendations" sub="Use your activity to tune your feed" last
          value={p.personalisation} onChange={(v) => set({ personalisation: v })} t={t} />
      </Group>

      <Callout icon={<Shield className="w-4 h-4" />} t={t}>
        This prototype stores every preference in your browser only. Nothing is sent to a server.
      </Callout>
    </SubPage>
  );
}