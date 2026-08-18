// ─── HELP CENTER ─────────────────────────────────────────────────────────────

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ChevronDown, FileText, Flag, HelpCircle, Search } from "lucide-react";
import { ACCENT, EmptyState, Group, Row, SubPage } from "../settings-ui";
import type { Tokens } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

const FAQS = [
  {
    q: "How does the Collab Score work?",
    a: "Your Collab Score averages the ratings other creators leave after a completed collaboration, weighted toward recent work. Replying inside your stated response time and finishing what you accept are the two things that move it most.",
  },
  {
    q: "Who can send me a collab request?",
    a: "By default, anyone. Settings → Privacy Settings → “Who can send collab requests” narrows this to people you follow back, or closes it entirely. Turning on auto-screening in Collab Preferences also hides requests from creators below a score you choose.",
  },
  {
    q: "What happens when I accept a request?",
    a: "Accepting opens a direct message thread with that creator, marked with a C badge in your Inbox so you can tell collab threads from ordinary conversations. Ignoring a request removes it without notifying the sender.",
  },
  {
    q: "Can I use a sound I found in Discover?",
    a: "Yes. Open the sound from Discover and tap “Use This Sound” — it attaches to your next upload. Trending sounds show a growth percentage so you can see what's climbing before it peaks.",
  },
  {
    q: "How do I go live?",
    a: "Tap the + button in the bottom navigation, give the stream a title, and start. Viewers can send collab requests mid-stream, which land in your Inbox like any other request.",
  },
  {
    q: "Why can't I sign in with my password?",
    a: "If you created the account with Google or Apple it may not have a password yet. Sign in with that provider, then use Settings → Change Password to set one.",
  },
  {
    q: "How do I delete my account?",
    a: "Settings → Delete Profile. It's a two-step flow and asks you to type DELETE, because it removes your profile, collab history, messages and saved sounds permanently.",
  },
];

function FaqItem({ q, a, open, onToggle, last, t }: {
  q: string; a: string; open: boolean; onToggle: () => void; last: boolean; t: Tokens;
}) {
  return (
    <div style={{ borderBottom: last ? "none" : `1px solid ${t.divider}` }}>
      <button onClick={onToggle} aria-expanded={open}
        className="w-full flex items-center gap-3 px-4 py-4 text-left transition-opacity active:opacity-70">
        <span className="flex-1 text-[14px] font-semibold" style={{ color: open ? ACCENT : t.body }}>{q}</span>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }} className="flex-shrink-0">
          <ChevronDown className="w-4 h-4" style={{ color: open ? ACCENT : t.chevron }} />
        </motion.div>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22 }} className="overflow-hidden">
            <p className="px-4 pb-4 text-[13px] leading-relaxed" style={{ color: t.sub }}>{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function HelpCenterPage({ t, onBack, onNavigate }: PageProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return FAQS;
    return FAQS.filter((f) => f.q.toLowerCase().includes(q) || f.a.toLowerCase().includes(q));
  }, [query]);

  return (
    <SubPage title="Help Center" subtitle="Answers to the questions we get most" onBack={onBack} t={t}>
      <div className="rounded-2xl px-4 py-3.5 flex items-center gap-3 mb-5"
        style={{ background: t.fieldBg, border: t.fieldBorder }}>
        <Search className="w-4 h-4 flex-shrink-0" style={{ color: t.sub }} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search help articles…"
          className="flex-1 bg-transparent text-[15px] outline-none" style={{ color: t.heading }} />
      </div>

      {matches.length === 0 ? (
        <EmptyState icon={<HelpCircle className="w-7 h-7" />} title="No results"
          body={`Nothing matches “${query}”. Try a different word, or report the problem and we'll pick it up.`} t={t} />
      ) : (
        <Group label={query ? `${matches.length} result${matches.length === 1 ? "" : "s"}` : "Popular questions"} t={t}>
          {matches.map((f, i) => (
            <FaqItem key={f.q} q={f.q} a={f.a} open={open === f.q}
              onToggle={() => setOpen(open === f.q ? null : f.q)}
              last={i === matches.length - 1} t={t} />
          ))}
        </Group>
      )}

      <Group label="Still stuck?" t={t}>
        <Row label="Report a problem" sub="Tell us what broke and we'll look into it"
          onClick={() => onNavigate("reportProblem")} t={t}
          right={<Flag className="w-4 h-4" style={{ color: ACCENT }} />} />
        <Row label="Terms of Service" onClick={() => onNavigate("terms")} t={t}
          right={<FileText className="w-4 h-4" style={{ color: t.chevron }} />} />
        <Row label="Privacy Policy" last onClick={() => onNavigate("privacyPolicy")} t={t}
          right={<FileText className="w-4 h-4" style={{ color: t.chevron }} />} />
      </Group>
    </SubPage>
  );
}