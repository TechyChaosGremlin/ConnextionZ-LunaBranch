// ─── REPORT A PROBLEM ────────────────────────────────────────────────────────

import { useState } from "react";
import { motion } from "motion/react";
import { AlertCircle, Check, Send } from "lucide-react";
import { ACCENT, Callout, ChoiceRow, Field, Group, PrimaryAction, SubPage } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

const REPORT_TOPICS = [
  { value: "bug", label: "Something is broken", sub: "A screen, button or action isn't working" },
  { value: "content", label: "Report content", sub: "A post, comment or sound that breaks the rules" },
  { value: "user", label: "Report a creator", sub: "Harassment, impersonation or spam" },
  { value: "payment", label: "Payments & collabs", sub: "A dispute over an agreed collaboration" },
  { value: "other", label: "Something else", sub: "Anything that doesn't fit above" },
];

export function ReportProblemPage({ account, t, onBack }: PageProps) {
  const [topic, setTopic] = useState<string | null>(null);
  const [details, setDetails] = useState("");
  const [contactEmail, setContactEmail] = useState(account.email);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const valid = !!topic && details.trim().length >= 10;

  const submit = async () => {
    setSending(true);
    // Stands in for POST /support/reports — the UI states are the real work here.
    await new Promise((r) => setTimeout(r, 1200));
    setSending(false);
    setSent(true);
  };

  if (sent) {
    return (
      <SubPage title="Report sent" onBack={onBack} t={t}
        footer={<PrimaryAction onClick={onBack}>Back to Settings</PrimaryAction>}>
        <div className="flex flex-col items-center text-center pt-12">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", damping: 14, stiffness: 200 }}
            className="w-24 h-24 rounded-full flex items-center justify-center"
            style={{ background: "rgba(0,174,239,0.15)", border: "2px solid rgba(0,174,239,0.4)" }}>
            <Check className="w-10 h-10" style={{ color: ACCENT }} strokeWidth={2.5} />
          </motion.div>
          <p className="font-extrabold text-[22px] mt-6" style={{ color: t.heading }}>Thanks for flagging it</p>
          <p className="text-[14px] mt-2 leading-relaxed max-w-[280px]" style={{ color: t.sub }}>
            We've logged your report. If we need more detail we'll email {contactEmail}.
          </p>
          <div className="w-full mt-8">
            <Callout icon={<AlertCircle className="w-4 h-4" />} t={t}>
              Prototype — reports are not actually transmitted anywhere.
            </Callout>
          </div>
        </div>
      </SubPage>
    );
  }

  return (
    <SubPage title="Report a Problem" subtitle="The more detail, the faster we can fix it" onBack={onBack} t={t}
      footer={
        <PrimaryAction onClick={submit} disabled={!valid} loading={sending}>
          <Send className="w-4 h-4" /> Send Report
        </PrimaryAction>
      }>
      <Group label="What's this about?" t={t}>
        {REPORT_TOPICS.map((o, i) => (
          <ChoiceRow key={o.value} label={o.label} sub={o.sub} selected={topic === o.value}
            onSelect={() => setTopic(o.value)} last={i === REPORT_TOPICS.length - 1} t={t} />
        ))}
      </Group>

      <Field label="What happened?" value={details} onChange={setDetails} multiline rows={5} maxLength={1000}
        placeholder="Describe what you did, what you expected, and what happened instead."
        hint={details.trim().length < 10 ? "At least 10 characters, so we have something to go on." : undefined}
        t={t} />

      <Field label="Contact email" type="email" value={contactEmail} onChange={setContactEmail}
        hint="We'll only use this to follow up on this report." t={t} />
    </SubPage>
  );
}