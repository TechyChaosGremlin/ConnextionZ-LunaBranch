// ─── LEGAL DOCUMENTS ─────────────────────────────────────────────────────────

import { FileText } from "lucide-react";
import { Callout, SubPage } from "../settings-ui";
import type { Tokens } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

interface LegalDoc {
  title: string;
  updated: string;
  intro: string;
  sections: { heading: string; body: string[] }[];
}

const TERMS: LegalDoc = {
  title: "Terms of Service",
  updated: "Last updated 1 June 2026",
  intro: "These terms cover your use of ConnextionZ. By creating an account you agree to them.",
  sections: [
    {
      heading: "1. Your account",
      body: [
        "You must be at least 13 years old to use ConnextionZ, and old enough to enter a contract where you live if you intend to accept paid collaborations.",
        "You are responsible for what happens under your account, including keeping your password to yourself. Tell us straight away if you think someone else has access.",
      ],
    },
    {
      heading: "2. Your content",
      body: [
        "You keep ownership of everything you post. You grant us a licence to host, display and distribute it so the service can function — nothing wider than that.",
        "Only post work you have the rights to. If you use a sound, sample or clip from another creator, make sure you are allowed to.",
      ],
    },
    {
      heading: "3. Collaborations",
      body: [
        "A collab request is an introduction, not a contract. Terms you agree with another creator — payment, deliverables, deadlines — are between the two of you.",
        "We may show a Collab Score based on ratings from completed collaborations. It reflects other creators' feedback and is not a guarantee of anyone's conduct.",
      ],
    },
    {
      heading: "4. What you may not do",
      body: [
        "Do not harass, impersonate or threaten anyone. Do not post content that is illegal where you or your audience are.",
        "Do not scrape the service, automate requests, or attempt to interfere with anyone else's use of it.",
      ],
    },
    {
      heading: "5. Ending your account",
      body: [
        "You can delete your account at any time from Settings. Deletion is permanent and removes your profile, collab history, messages and saved content.",
        "We may suspend or end an account that repeatedly breaks these terms, and will tell you why unless we are legally prevented from doing so.",
      ],
    },
    {
      heading: "6. Changes",
      body: [
        "We will give notice in the app before any material change to these terms takes effect. Continuing to use ConnextionZ after that means you accept the new version.",
      ],
    },
  ],
};

const PRIVACY_POLICY: LegalDoc = {
  title: "Privacy Policy",
  updated: "Last updated 1 June 2026",
  intro: "What we collect, why we collect it, and the control you have over it.",
  sections: [
    {
      heading: "1. What we collect",
      body: [
        "Account details you give us: name, email, and anything you add to your profile such as a bio, location or website.",
        "Activity on the service: posts, comments, collab requests and messages, plus the preferences you set in Settings.",
        "Technical data your device sends: approximate region, device type and app version, used to keep the service working.",
      ],
    },
    {
      heading: "2. Why we use it",
      body: [
        "To run the service — showing your posts, delivering collab requests, and letting creators find each other.",
        "To personalise your feed, which you can turn off in Settings → Privacy Settings → Personalised recommendations.",
        "To keep the platform safe: detecting spam, impersonation and abuse.",
      ],
    },
    {
      heading: "3. What we share",
      body: [
        "We do not sell your personal data.",
        "Your public profile, posts and Collab Score are visible to other creators, subject to the visibility settings you choose.",
        "Service providers who host or process data on our behalf are bound to use it only for that purpose.",
      ],
    },
    {
      heading: "4. Your controls",
      body: [
        "Privacy Settings controls who can message you, who can send collab requests, and whether you appear in Discover.",
        "Notification Preferences controls what reaches you and how often.",
        "You can edit your profile at any time, and delete your account and its data permanently from Settings.",
      ],
    },
    {
      heading: "5. Keeping data",
      body: [
        "We keep your data while your account is open. When you delete it, your profile, messages and collab history are removed.",
        "Some records may be retained where the law requires it, for the shortest period allowed.",
      ],
    },
    {
      heading: "6. Contact",
      body: [
        "Questions about this policy, or a request to access or export your data, can be raised from Settings → Report a Problem.",
      ],
    },
  ],
};

function LegalPage({ doc, t, onBack }: { doc: LegalDoc; t: Tokens; onBack: () => void }) {
  return (
    <SubPage title={doc.title} subtitle={doc.updated} onBack={onBack} t={t}>
      <Callout icon={<FileText className="w-4 h-4" />} t={t}>
        Prototype copy. A production build serves the reviewed legal text from the same route.
      </Callout>

      <p className="text-[14px] leading-relaxed mb-6" style={{ color: t.body }}>{doc.intro}</p>

      <div className="space-y-6">
        {doc.sections.map((s) => (
          <div key={s.heading}>
            <h2 className="font-bold text-[15px] mb-2" style={{ color: t.heading }}>{s.heading}</h2>
            <div className="space-y-2.5">
              {s.body.map((p, i) => (
                <p key={i} className="text-[13px] leading-relaxed" style={{ color: t.sub }}>{p}</p>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="text-center text-[12px] mt-10" style={{ color: t.sub }}>ConnextionZ v1.0.0</p>
    </SubPage>
  );
}

export const TermsPage = ({ t, onBack }: PageProps) => <LegalPage doc={TERMS} t={t} onBack={onBack} />;
export const PrivacyPolicyPage = ({ t, onBack }: PageProps) => <LegalPage doc={PRIVACY_POLICY} t={t} onBack={onBack} />;