// ─── NOTIFICATION PREFERENCES ────────────────────────────────────────────────

import { Bell } from "lucide-react";
import { Callout, ChoiceRow, Group, SubPage, ToggleRow } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

export function NotificationsPage({ prefs, t, onBack, onPatch }: PageProps) {
  const n = prefs.notifications;
  const set = (patch: Partial<typeof n>) => onPatch({ notifications: { ...n, ...patch } });

  return (
    <SubPage title="Notification Preferences" subtitle="Choose what reaches you, and how" onBack={onBack} t={t}>
      <Callout icon={<Bell className="w-4 h-4" />} t={t}>
        Collab requests and direct messages are the two that matter most — leaving them on is how
        creators reach you before someone else does.
      </Callout>

      <Group label="Collaboration" t={t}>
        <ToggleRow label="Collab requests" sub="Someone wants to work with you"
          value={n.collabRequests} onChange={(v) => set({ collabRequests: v })} t={t} />
        <ToggleRow label="Direct messages" sub="New messages in your inbox" last
          value={n.messages} onChange={(v) => set({ messages: v })} t={t} />
      </Group>

      <Group label="Activity" t={t}>
        <ToggleRow label="Likes" value={n.likes} onChange={(v) => set({ likes: v })} t={t} />
        <ToggleRow label="Comments" value={n.comments} onChange={(v) => set({ comments: v })} t={t} />
        <ToggleRow label="New followers" last value={n.newFollowers} onChange={(v) => set({ newFollowers: v })} t={t} />
      </Group>

      <Group label="Discovery" t={t}>
        <ToggleRow label="Live alerts" sub="When creators you follow go live"
          value={n.liveAlerts} onChange={(v) => set({ liveAlerts: v })} t={t} />
        <ToggleRow label="Trending sounds" sub="Weekly roundup of what's climbing" last
          value={n.trendingSounds} onChange={(v) => set({ trendingSounds: v })} t={t} />
      </Group>

      <Group label="Email digest" hint="Transactional email — password resets and security alerts — is always sent." t={t}>
        {(["off", "daily", "weekly"] as const).map((v, i) => (
          <ChoiceRow key={v} t={t} last={i === 2}
            label={v === "off" ? "Off" : v === "daily" ? "Daily" : "Weekly"}
            sub={v === "off" ? "No digest email" : v === "daily" ? "A morning summary" : "Every Monday"}
            selected={n.emailDigest === v} onSelect={() => set({ emailDigest: v })} />
        ))}
      </Group>

      <Group label="Delivery" t={t}>
        <ToggleRow label="Quiet hours" sub="Mute push between 22:00 and 08:00" last
          value={n.quietHours} onChange={(v) => set({ quietHours: v })} t={t} />
        <ToggleRow label="Product updates" sub="New features and creator tips"
          value={n.productUpdates} onChange={(v) => set({ productUpdates: v })} t={t} />
      </Group>
    </SubPage>
  );
}