// ─── CHANGE PASSWORD ─────────────────────────────────────────────────────────

import { useState } from "react";
import { motion } from "motion/react";
import { AlertCircle, Check, Lock, Shield } from "lucide-react";
import { changePassword, hasPassword } from "../auth-store";
import { Callout, Field, Group, PrimaryAction, Row, SubPage } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

export function ChangePasswordPage({ account, t, onBack, onAccountChange }: PageProps) {
  const isSettingFirst = !hasPassword(account);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const rules = [
    { label: "At least 8 characters", pass: next.length >= 8 },
    { label: "Contains a number", pass: /\d/.test(next) },
    { label: "Contains a letter", pass: /[a-zA-Z]/.test(next) },
    { label: "Both entries match", pass: next.length > 0 && next === confirm },
  ];
  const valid = rules.every((r) => r.pass) && (isSettingFirst || current.length > 0);

  const handleSubmit = async () => {
    setSaving(true);
    setError("");
    const result = await changePassword(account.email, current, next);
    setSaving(false);
    if (!result.ok) { setError(result.error); return; }
    onAccountChange(result.value);
    setDone(true);
    setCurrent(""); setNext(""); setConfirm("");
  };

  if (done) {
    return (
      <SubPage title={isSettingFirst ? "Password set" : "Password changed"} onBack={onBack} t={t}
        footer={<PrimaryAction onClick={onBack}>Back to Settings</PrimaryAction>}>
        <div className="flex flex-col items-center text-center pt-12">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", damping: 14, stiffness: 200 }}
            className="w-24 h-24 rounded-full flex items-center justify-center"
            style={{ background: "rgba(34,197,94,0.15)", border: "2px solid rgba(34,197,94,0.4)" }}>
            <Check className="w-10 h-10 text-green-400" strokeWidth={2.5} />
          </motion.div>
          <p className="font-extrabold text-[22px] mt-6" style={{ color: t.heading }}>You're all set</p>
          <p className="text-[14px] mt-2 leading-relaxed max-w-[280px]" style={{ color: t.sub }}>
            {isSettingFirst
              ? "You can now sign in with your email and password as well as your linked provider."
              : "Your old password no longer works. Any pending reset links have been cancelled."}
          </p>
        </div>
      </SubPage>
    );
  }

  return (
    <SubPage
      title={isSettingFirst ? "Set a Password" : "Change Password"}
      subtitle={isSettingFirst ? "Add a password to this account" : "Update the password you sign in with"}
      onBack={onBack} t={t}
      footer={
        <PrimaryAction onClick={handleSubmit} disabled={!valid} loading={saving}>
          <Lock className="w-4 h-4" /> {isSettingFirst ? "Set Password" : "Update Password"}
        </PrimaryAction>
      }>
      {isSettingFirst && (
        <Callout icon={<Shield className="w-4 h-4" />} t={t}>
          This account signs in with {account.providers.map((p) => (p === "google" ? "Google" : "Apple")).join(" and ") || "a provider"}.
          Setting a password adds a second way in — the provider keeps working.
        </Callout>
      )}

      {error && (
        <Callout icon={<AlertCircle className="w-4 h-4" />} tone="warn" t={t}>
          <span className="text-red-400">{error}</span>
        </Callout>
      )}

      {!isSettingFirst && (
        <Field label="Current password" type="password" value={current} onChange={setCurrent}
          placeholder="••••••••" t={t} />
      )}
      <Field label="New password" type="password" value={next} onChange={setNext}
        placeholder="Min. 8 characters" t={t} />
      <Field label="Confirm new password" type="password" value={confirm} onChange={setConfirm}
        placeholder="Repeat password" t={t} />

      <Group label="Requirements" t={t}>
        {rules.map((r, i) => (
          <Row key={r.label} label={r.label} last={i === rules.length - 1} t={t}
            right={
              <div className="w-5 h-5 rounded-full flex items-center justify-center"
                style={{ background: r.pass ? "rgba(34,197,94,0.2)" : "transparent", border: r.pass ? "1px solid rgba(34,197,94,0.5)" : `1.5px solid ${t.chevron}` }}>
                {r.pass && <Check className="w-3 h-3 text-green-400" strokeWidth={3} />}
              </div>
            } />
        ))}
      </Group>
    </SubPage>
  );
}