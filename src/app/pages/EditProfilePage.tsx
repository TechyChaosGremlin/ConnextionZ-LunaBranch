// ─── EDIT PROFILE ────────────────────────────────────────────────────────────

import { useState } from "react";
import { AlertCircle, Check } from "lucide-react";
import { profileOf, updateProfile } from "../auth-store";
import { normalizeProfilePatch } from "../profile-validation";
import { ACCENT, Callout, Field, Group, PrimaryAction, Row, SubPage } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

const AVATAR_COLORS = ["#00AEEF", "#a78bfa", "#22c55e", "#f59e0b", "#f472b6", "#ef4444"];

export function EditProfilePage({ account, t, onBack, onAccountChange }: PageProps) {
  const current = profileOf(account);
  const [displayName, setDisplayName] = useState(current.displayName);
  const [username, setUsername] = useState(current.username);
  const [bio, setBio] = useState(current.bio);
  const [location, setLocation] = useState(current.location);
  const [website, setWebsite] = useState(current.website);
  const [avatarColor, setAvatarColor] = useState(current.avatarColor);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const dirty =
    displayName !== current.displayName || username !== current.username ||
    bio !== current.bio || location !== current.location ||
    website !== current.website || avatarColor !== current.avatarColor;

  const handleSave = async () => {
    setSaving(true);
    setError("");
    const normalized = normalizeProfilePatch({
      displayName,
      username,
      bio,
      location,
      website,
    });
    const result = await updateProfile(account.email, { ...normalized, avatarColor });
    setSaving(false);
    if (!result.ok) { setError(result.error); return; }
    onAccountChange(result.value);
    setSaved(true);
    setTimeout(() => setSaved(false), 1800);
  };

  const initial = (displayName.trim() || username || "?")[0].toUpperCase();

  return (
    <SubPage title="Edit Profile" subtitle="How other creators see you" onBack={onBack} t={t}
      footer={
        <PrimaryAction onClick={handleSave} disabled={!dirty && !saved} loading={saving} done={saved}>
          Save Changes
        </PrimaryAction>
      }>
      {/* Avatar */}
      <div className="flex items-center gap-5 mb-6">
        <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-3xl font-bold flex-shrink-0"
          style={{ background: avatarColor, boxShadow: `0 8px 24px ${avatarColor}55` }}>
          {initial}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: t.sectionLbl }}>Avatar colour</p>
          <div className="flex flex-wrap gap-2">
            {AVATAR_COLORS.map((c) => (
              <button key={c} onClick={() => setAvatarColor(c)} aria-label={`Avatar colour ${c}`}
                className="w-9 h-9 rounded-full flex items-center justify-center transition-transform hover:scale-110"
                style={{ background: c, border: avatarColor === c ? "2.5px solid white" : "2.5px solid transparent" }}>
                {avatarColor === c && <Check className="w-4 h-4 text-white" strokeWidth={3} />}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <Callout icon={<AlertCircle className="w-4 h-4" />} tone="warn" t={t}>
          <span className="text-red-400">{error}</span>
        </Callout>
      )}

      <Field label="Display name" value={displayName} onChange={setDisplayName}
        placeholder="Maya Chen" maxLength={40} t={t} />
      <Field label="Username" value={username} onChange={(v) => setUsername(v.toLowerCase())}
        placeholder="maya.creates" prefix="@" maxLength={24} t={t}
        hint="3–24 characters. Letters, numbers, dots and underscores." />
      <Field label="Bio" value={bio} onChange={setBio} multiline rows={3} maxLength={160}
        placeholder="What do you make, and who do you want to make it with?" t={t} />
      <Field label="Location" value={location} onChange={setLocation} placeholder="Los Angeles, CA" t={t} />
      <Field label="Website" value={website} onChange={setWebsite} placeholder="yoursite.com" t={t} />

      <Group label="Account" t={t}>
        <Row label="Email" right={<span className="text-[13px]" style={{ color: t.sub }}>{account.email}</span>} t={t} />
        <Row label="Signed up as" last
          right={<span className="text-[13px]" style={{ color: t.sub }}>{account.firstName} {account.lastName}</span>} t={t} />
      </Group>
      <p className="text-[12px] leading-relaxed px-1 -mt-2" style={{ color: t.sub }}>
        Your email is never shown on your public profile.
      </p>
    </SubPage>
  );
}