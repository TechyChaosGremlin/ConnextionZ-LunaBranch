// ─── PORTFOLIO ───────────────────────────────────────────────────────────────

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Briefcase, Plus, Star, Trash2 } from "lucide-react";
import { ACCENT, EmptyState, Field, PrimaryAction, SecondaryAction, SubPage } from "../settings-ui";
import type { PageProps } from "./settingsPages.types";

export function PortfolioPage({ prefs, t, onBack, onPatch }: PageProps) {
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState("");
  const [role, setRole] = useState("");
  const [year, setYear] = useState("");

  const items = prefs.portfolio;
  const canAdd = title.trim().length > 0;

  const add = () => {
    if (!canAdd) return;
    onPatch({
      portfolio: [
        {
          // Unique without a date dependency: the highest existing suffix + 1.
          id: `p${items.reduce((max, it) => Math.max(max, Number(it.id.slice(1)) || 0), 0) + 1}`,
          title: title.trim(),
          role: role.trim() || "Creator",
          year: year.trim() || "2026",
          image: "",
          featured: false,
        },
        ...items,
      ],
    });
    setTitle(""); setRole(""); setYear(""); setAdding(false);
  };

  const remove = (id: string) => onPatch({ portfolio: items.filter((i) => i.id !== id) });
  const toggleFeatured = (id: string) =>
    onPatch({ portfolio: items.map((i) => (i.id === id ? { ...i, featured: !i.featured } : i)) });

  return (
    <SubPage title="Portfolio" subtitle={`${items.length} ${items.length === 1 ? "piece" : "pieces"} of work`}
      onBack={onBack} t={t}
      footer={
        adding
          ? <div className="space-y-3">
              <PrimaryAction onClick={add} disabled={!canAdd}><Plus className="w-4 h-4" /> Add to Portfolio</PrimaryAction>
              <SecondaryAction onClick={() => setAdding(false)} t={t}>Cancel</SecondaryAction>
            </div>
          : <PrimaryAction onClick={() => setAdding(true)}><Plus className="w-4 h-4" /> Add Work</PrimaryAction>
      }>
      <AnimatePresence initial={false}>
        {adding && (
          <motion.div key="add-form" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="rounded-2xl p-4 mb-5" style={{ background: t.cardBg, border: t.cardBorder }}>
              <Field label="Title" value={title} onChange={setTitle} placeholder="Midnight Rush" maxLength={60} t={t} />
              <Field label="Your role" value={role} onChange={setRole} placeholder="Producer · with @nova.dj" t={t} />
              <Field label="Year" value={year} onChange={setYear} placeholder="2026" t={t} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {items.length === 0 ? (
        <EmptyState icon={<Briefcase className="w-7 h-7" />} title="No work yet"
          body="Add the collabs you're proudest of. Creators check your portfolio before they send a request."
          t={t} />
      ) : (
        <div className="space-y-3">
          <AnimatePresence initial={false}>
            {items.map((item) => (
              <motion.div key={item.id} layout
                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -60, transition: { duration: 0.18 } }}
                className="flex items-center gap-3 p-3 rounded-2xl"
                style={{ background: t.groupBg, border: t.groupBorder }}>
                <div className="w-14 h-14 rounded-xl overflow-hidden flex-shrink-0 flex items-center justify-center"
                  style={{ background: "rgba(0,174,239,0.12)" }}>
                  {item.image
                    ? <img src={item.image} alt="" className="w-full h-full object-cover" />
                    : <Briefcase className="w-5 h-5" style={{ color: ACCENT }} />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <p className="text-[14px] font-bold truncate" style={{ color: t.heading }}>{item.title}</p>
                    {item.featured && <Star className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "#f59e0b", fill: "#f59e0b" }} />}
                  </div>
                  <p className="text-[12px] truncate mt-0.5" style={{ color: t.sub }}>{item.role}</p>
                  <p className="text-[11px] mt-0.5" style={{ color: t.sub }}>{item.year}</p>
                </div>
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  <button onClick={() => toggleFeatured(item.id)}
                    aria-label={item.featured ? "Unfeature" : "Feature"}
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: item.featured ? "rgba(245,158,11,0.15)" : t.chipBg }}>
                    <Star className="w-3.5 h-3.5" style={{ color: item.featured ? "#f59e0b" : t.sub }} />
                  </button>
                  <button onClick={() => remove(item.id)} aria-label="Remove"
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: "rgba(239,68,68,0.1)" }}>
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </SubPage>
  );
}