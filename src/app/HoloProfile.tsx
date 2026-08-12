import { useRef, useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  UserPlus,
  MessageCircle,
  Zap,
  Briefcase,
  Share2,
  X,
  ChevronRight,
  Star,
  Shield,
  Flame,
  Music2,
  Award,
  Gem,
  Check,
} from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────────────────

const AVATAR_URL =
  "https://images.unsplash.com/photo-1618673747378-7e0d3561371a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400";

const PROJECT_IMAGES = [
  "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=300",
  "https://images.unsplash.com/photo-1541126274323-dbac58d14741?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=300",
  "https://images.unsplash.com/photo-1594623930572-300a3011d9ae?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=300",
];

const FACE_STYLE: React.CSSProperties = {
  position: "absolute",
  width: 380,
  height: 380,
  borderRadius: 30,
  background: "rgba(8, 16, 40, 0.85)",
  backdropFilter: "blur(32px)",
  WebkitBackdropFilter: "blur(32px)",
  border: "1px solid rgba(0, 174, 239, 0.25)",
  boxShadow:
    "0 0 60px rgba(0,174,239,0.15), inset 0 0 40px rgba(0,174,239,0.04)",
  backfaceVisibility: "hidden",
  WebkitBackfaceVisibility: "hidden",
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: 28,
  boxSizing: "border-box",
  left: "50%",
  top: "50%",
  marginLeft: -190,
  marginTop: -190,
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function FaceFront({ onExpand }: { onExpand: () => void }) {
  return (
    <div style={{ ...FACE_STYLE, transform: "rotateY(0deg) translateZ(200px)" }}>
      <div style={{ position: "relative", marginBottom: 16 }}>
        <img
          src={AVATAR_URL}
          alt="Nova DJ"
          style={{
            width: 100,
            height: 100,
            borderRadius: "50%",
            objectFit: "cover",
            border: "2px solid rgba(0,174,239,0.6)",
            boxShadow: "0 0 24px rgba(0,174,239,0.4)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: 2,
            right: 2,
            width: 18,
            height: 18,
            borderRadius: "50%",
            background: "#00AEEF",
            border: "2px solid #010814",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Check size={9} color="#010814" strokeWidth={3} />
        </div>
      </div>
      <p style={{ color: "#00AEEF", fontFamily: "monospace", fontSize: 12, letterSpacing: 2, marginBottom: 4, margin: "0 0 4px" }}>
        @nova.dj
      </p>
      <h2 style={{ color: "#fff", fontWeight: 800, fontSize: 20, margin: "0 0 6px", textAlign: "center", fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
        Nova Vasquez
      </h2>
      <p style={{ color: "rgba(255,255,255,0.55)", fontSize: 12, textAlign: "center", margin: "0 0 16px", lineHeight: 1.5 }}>
        Electronic Producer · DJ · Composer
      </p>
      <div style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        background: "rgba(0,174,239,0.12)",
        border: "1px solid rgba(0,174,239,0.35)",
        borderRadius: 20,
        padding: "5px 14px",
        marginBottom: 16,
      }}>
        <Star size={12} color="#f59e0b" fill="#f59e0b" />
        <span style={{ color: "#f59e0b", fontSize: 13, fontWeight: 700 }}>4.9</span>
        <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>Collab Score</span>
      </div>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onExpand}
        style={{
          background: "rgba(0,174,239,0.15)",
          border: "1px solid rgba(0,174,239,0.4)",
          borderRadius: 20,
          color: "#00AEEF",
          fontSize: 12,
          padding: "6px 18px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        Full Profile <ChevronRight size={12} />
      </motion.button>
    </div>
  );
}

function FaceLeft({ onExpand }: { onExpand: () => void }) {
  const stats = [
    { label: "Followers", value: "2.4M" },
    { label: "Following", value: "891" },
    { label: "Collabs", value: "312" },
    { label: "Total Views", value: "847M" },
  ];
  return (
    <div style={{ ...FACE_STYLE, transform: "rotateY(-90deg) translateZ(200px)" }}>
      <p style={{ color: "#00AEEF", fontFamily: "monospace", fontSize: 11, letterSpacing: 2, marginBottom: 20, margin: "0 0 20px" }}>
        STATISTICS
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, width: "100%" }}>
        {stats.map((s) => (
          <div key={s.label} style={{
            background: "rgba(0,174,239,0.07)",
            border: "1px solid rgba(0,174,239,0.18)",
            borderRadius: 16,
            padding: "16px 12px",
            textAlign: "center",
          }}>
            <p style={{ color: "#fff", fontWeight: 800, fontSize: 22, margin: "0 0 4px", fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
              {s.value}
            </p>
            <p style={{ color: "rgba(255,255,255,0.45)", fontSize: 11, margin: 0, letterSpacing: 0.5 }}>
              {s.label}
            </p>
          </div>
        ))}
      </div>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onExpand}
        style={{
          marginTop: 20,
          background: "transparent",
          border: "1px solid rgba(0,174,239,0.3)",
          borderRadius: 20,
          color: "rgba(0,174,239,0.8)",
          fontSize: 11,
          padding: "5px 16px",
          cursor: "pointer",
        }}
      >
        View Analytics
      </motion.button>
    </div>
  );
}

function FaceRight({ onExpand }: { onExpand: () => void }) {
  const projects = [
    { title: "Neon Requiem", partner: "w/ Arion Bell", img: PROJECT_IMAGES[0] },
    { title: "Pulse Architecture", partner: "w/ Sonar Collective", img: PROJECT_IMAGES[1] },
    { title: "Midnight Lattice", partner: "w/ DJ Kira", img: PROJECT_IMAGES[2] },
  ];
  return (
    <div style={{ ...FACE_STYLE, transform: "rotateY(90deg) translateZ(200px)" }}>
      <p style={{ color: "#00AEEF", fontFamily: "monospace", fontSize: 11, letterSpacing: 2, marginBottom: 16, margin: "0 0 16px" }}>
        FEATURED PROJECTS
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%" }}>
        {projects.map((p) => (
          <div key={p.title} style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            background: "rgba(0,174,239,0.06)",
            border: "1px solid rgba(0,174,239,0.15)",
            borderRadius: 12,
            padding: "10px 12px",
          }}>
            <img src={p.img} alt={p.title} style={{ width: 42, height: 42, borderRadius: 8, objectFit: "cover", flexShrink: 0 }} />
            <div>
              <p style={{ color: "#fff", fontWeight: 700, fontSize: 13, margin: "0 0 2px", fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
                {p.title}
              </p>
              <p style={{ color: "rgba(0,174,239,0.7)", fontSize: 11, margin: 0 }}>{p.partner}</p>
            </div>
          </div>
        ))}
      </div>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onExpand}
        style={{
          marginTop: 14,
          background: "transparent",
          border: "1px solid rgba(0,174,239,0.3)",
          borderRadius: 20,
          color: "rgba(0,174,239,0.8)",
          fontSize: 11,
          padding: "5px 16px",
          cursor: "pointer",
        }}
      >
        All Projects
      </motion.button>
    </div>
  );
}

function FaceBack({ onExpand }: { onExpand: () => void }) {
  const tags = ["#TechHouse", "#Ambient", "#Synthesis", "#LiveSets", "#Modular"];
  const skills = ["Music Production", "Sound Design", "Mixing", "Mastering", "Live Performance"];
  const socials = [
    { name: "SoundCloud", color: "#ff5500" },
    { name: "Spotify", color: "#1db954" },
    { name: "Instagram", color: "#e1306c" },
    { name: "YouTube", color: "#ff0000" },
  ];
  return (
    <div style={{ ...FACE_STYLE, transform: "rotateY(180deg) translateZ(200px)" }}>
      <p style={{ color: "#00AEEF", fontFamily: "monospace", fontSize: 11, letterSpacing: 2, marginBottom: 10, margin: "0 0 10px" }}>
        BIO
      </p>
      <p style={{ color: "rgba(255,255,255,0.65)", fontSize: 12, textAlign: "center", lineHeight: 1.6, margin: "0 0 12px" }}>
        Berlin-based electronic architect blending raw techno with cinematic soundscapes. Residency at Tresor. Label founder at Voidcraft Records.
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center", marginBottom: 12 }}>
        {tags.map((t) => (
          <span key={t} style={{ background: "rgba(0,174,239,0.1)", border: "1px solid rgba(0,174,239,0.25)", borderRadius: 20, padding: "3px 10px", color: "#00AEEF", fontSize: 10 }}>
            {t}
          </span>
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 5, justifyContent: "center", marginBottom: 12 }}>
        {skills.map((sk) => (
          <span key={sk} style={{ background: "rgba(255,255,255,0.05)", borderRadius: 6, padding: "3px 8px", color: "rgba(255,255,255,0.6)", fontSize: 10 }}>
            {sk}
          </span>
        ))}
      </div>
      <div style={{ display: "flex", gap: 10 }}>
        {socials.map((s) => (
          <button key={s.name} style={{ width: 34, height: 34, borderRadius: "50%", background: `${s.color}22`, border: `1px solid ${s.color}55`, color: s.color, fontSize: 9, cursor: "pointer", fontWeight: 700 }}>
            {s.name.slice(0, 2)}
          </button>
        ))}
      </div>
    </div>
  );
}

function FaceBottom({ onExpand }: { onExpand: () => void }) {
  const badges = [
    { icon: <Award size={18} color="#f59e0b" />, label: "Top Creator" },
    { icon: <Zap size={18} color="#00AEEF" />, label: "Collab King" },
    { icon: <Shield size={18} color="#a78bfa" />, label: "Verified" },
    { icon: <Flame size={18} color="#f97316" />, label: "Trending" },
    { icon: <Gem size={18} color="#34d399" />, label: "Premium" },
    { icon: <Music2 size={18} color="#f472b6" />, label: "Sound Maker" },
  ];
  return (
    <div style={{ ...FACE_STYLE, transform: "rotateX(90deg) translateZ(200px)" }}>
      <p style={{ color: "#00AEEF", fontFamily: "monospace", fontSize: 11, letterSpacing: 2, marginBottom: 16, margin: "0 0 16px" }}>
        ACHIEVEMENTS
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, width: "100%", marginBottom: 16 }}>
        {badges.map((b) => (
          <div key={b.label} style={{
            background: "rgba(0,174,239,0.07)",
            border: "1px solid rgba(0,174,239,0.15)",
            borderRadius: 14,
            padding: "12px 8px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 6,
          }}>
            {b.icon}
            <span style={{ color: "rgba(255,255,255,0.65)", fontSize: 9, textAlign: "center", letterSpacing: 0.3 }}>{b.label}</span>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Star size={14} color="#f59e0b" fill="#f59e0b" />
        <span style={{ color: "#fff", fontWeight: 800, fontSize: 18, fontFamily: "'Plus Jakarta Sans', sans-serif" }}>4.9</span>
        <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>/ 5 Collab Score</span>
      </div>
    </div>
  );
}

function FaceTop({ onExpand }: { onExpand: () => void }) {
  const [selected, setSelected] = useState(0);
  const statuses = [
    { label: "Available to Collaborate", glow: "#00ff88", dot: "#00ff88" },
    { label: "Busy", glow: "#f59e0b", dot: "#f59e0b" },
    { label: "Open for Hire", glow: "#a78bfa", dot: "#a78bfa" },
    { label: "Live Now", glow: "#ff3333", dot: "#ff3333" },
  ];
  return (
    <div style={{ ...FACE_STYLE, transform: "rotateX(-90deg) translateZ(200px)" }}>
      <p style={{ color: "#00AEEF", fontFamily: "monospace", fontSize: 11, letterSpacing: 2, marginBottom: 20, margin: "0 0 20px" }}>
        STATUS
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%" }}>
        {statuses.map((s, i) => (
          <motion.button
            key={s.label}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSelected(i)}
            style={{
              background: selected === i ? `${s.glow}18` : "rgba(255,255,255,0.04)",
              border: `1px solid ${selected === i ? s.glow + "60" : "rgba(255,255,255,0.1)"}`,
              borderRadius: 12,
              padding: "11px 14px",
              display: "flex",
              alignItems: "center",
              gap: 10,
              cursor: "pointer",
              boxShadow: selected === i ? `0 0 16px ${s.glow}30` : "none",
            }}
          >
            <div style={{
              width: 9,
              height: 9,
              borderRadius: "50%",
              background: selected === i ? s.dot : "rgba(255,255,255,0.2)",
              boxShadow: selected === i ? `0 0 8px ${s.glow}` : "none",
            }} />
            <span style={{ color: selected === i ? "#fff" : "rgba(255,255,255,0.5)", fontSize: 13, fontWeight: selected === i ? 600 : 400 }}>
              {s.label}
            </span>
            {selected === i && <Check size={12} color={s.glow} style={{ marginLeft: "auto" }} />}
          </motion.button>
        ))}
      </div>
    </div>
  );
}

// ─── Particle Canvas ───────────────────────────────────────────────────────────

function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    type Particle = { x: number; y: number; vx: number; vy: number; radius: number; opacity: number; color: string };
    const colors = ["#00AEEF", "#38bdf8"];
    const particles: Particle[] = Array.from({ length: 80 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: 0.5 + Math.random() * 1.5,
      opacity: 0.1 + Math.random() * 0.5,
      color: colors[Math.floor(Math.random() * colors.length)],
    }));

    let rafId: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      rafId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}
    />
  );
}

// ─── Expand Modal ──────────────────────────────────────────────────────────────

type ModalSection = "front" | "left" | "right" | "back" | "bottom" | "top" | null;

function ExpandModal({ section, onClose }: { section: ModalSection; onClose: () => void }) {
  const titles: Record<Exclude<ModalSection, null>, string> = {
    front: "Full Profile",
    left: "Detailed Analytics",
    right: "All Projects",
    back: "About Nova",
    bottom: "All Achievements",
    top: "Availability Settings",
  };

  const content: Record<Exclude<ModalSection, null>, React.ReactNode> = {
    front: (
      <div style={{ textAlign: "center" }}>
        <img src={AVATAR_URL} alt="Nova" style={{ width: 120, height: 120, borderRadius: "50%", objectFit: "cover", border: "2px solid #00AEEF", marginBottom: 16 }} />
        <h2 style={{ color: "#fff", fontWeight: 800, fontSize: 26, margin: "0 0 6px" }}>Nova Vasquez</h2>
        <p style={{ color: "#00AEEF", margin: "0 0 12px", fontFamily: "monospace" }}>@nova.dj</p>
        <p style={{ color: "rgba(255,255,255,0.6)", lineHeight: 1.7, maxWidth: 480, margin: "0 auto 20px" }}>
          Electronic music architect with over a decade shaping dancefloors across Europe and Asia. Known for intricate layering and live improvisational energy. Alumni of the Ableton Certified Trainer program and Berklee Online.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
          {["Berlin", "Techno", "Ambient", "Modular Synth"].map(t => (
            <span key={t} style={{ background: "rgba(0,174,239,0.12)", border: "1px solid rgba(0,174,239,0.3)", borderRadius: 20, padding: "4px 12px", color: "#00AEEF", fontSize: 12 }}>{t}</span>
          ))}
        </div>
      </div>
    ),
    left: (
      <div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
          {[["2.4M", "Followers"], ["891", "Following"], ["312", "Collaborations"], ["847M", "Total Views"], ["98%", "Response Rate"], ["4.9★", "Avg Rating"]].map(([v, l]) => (
            <div key={l} style={{ background: "rgba(0,174,239,0.08)", border: "1px solid rgba(0,174,239,0.2)", borderRadius: 16, padding: "18px 16px", textAlign: "center" }}>
              <p style={{ color: "#fff", fontWeight: 800, fontSize: 24, margin: "0 0 4px" }}>{v}</p>
              <p style={{ color: "rgba(255,255,255,0.45)", fontSize: 12, margin: 0 }}>{l}</p>
            </div>
          ))}
        </div>
        <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 13, textAlign: "center" }}>Growth: +12.4% this month</p>
      </div>
    ),
    right: (
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {[
          { title: "Neon Requiem", partner: "Arion Bell", genre: "Techno / Industrial", plays: "12.1M", img: PROJECT_IMAGES[0] },
          { title: "Pulse Architecture", partner: "Sonar Collective", genre: "Ambient / Electronic", plays: "8.7M", img: PROJECT_IMAGES[1] },
          { title: "Midnight Lattice", partner: "DJ Kira", genre: "Deep House", plays: "6.4M", img: PROJECT_IMAGES[2] },
        ].map(p => (
          <div key={p.title} style={{ display: "flex", gap: 14, background: "rgba(0,174,239,0.06)", border: "1px solid rgba(0,174,239,0.15)", borderRadius: 14, padding: 14 }}>
            <img src={p.img} alt={p.title} style={{ width: 70, height: 70, borderRadius: 10, objectFit: "cover" }} />
            <div>
              <p style={{ color: "#fff", fontWeight: 700, fontSize: 15, margin: "0 0 4px" }}>{p.title}</p>
              <p style={{ color: "#00AEEF", fontSize: 12, margin: "0 0 4px" }}>w/ {p.partner}</p>
              <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, margin: "0 0 4px" }}>{p.genre}</p>
              <p style={{ color: "rgba(255,255,255,0.55)", fontSize: 11, margin: 0 }}>{p.plays} streams</p>
            </div>
          </div>
        ))}
      </div>
    ),
    back: (
      <div>
        <p style={{ color: "rgba(255,255,255,0.7)", lineHeight: 1.8, marginBottom: 20 }}>
          Nova Vasquez started producing at age 14 in a repurposed closet studio in Bogotá. A decade later, her sets at Berghain, Fabric, and Boiler Room have accumulated over 847 million views. She runs Voidcraft Records independently, has collaborated with 312 artists across 44 countries, and advocates loudly for fair pay and open-source music tools.
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
          {["Music Production", "Sound Design", "Mixing", "Mastering", "Live Performance", "Label Management", "Synthesis", "Modular"].map(s => (
            <span key={s} style={{ background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, padding: "4px 10px", color: "rgba(255,255,255,0.65)", fontSize: 12 }}>{s}</span>
          ))}
        </div>
      </div>
    ),
    bottom: (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
        {[
          { icon: <Award size={24} color="#f59e0b" />, label: "Top Creator", desc: "Top 0.1% of creators" },
          { icon: <Zap size={24} color="#00AEEF" />, label: "Collab King", desc: "312 collaborations" },
          { icon: <Shield size={24} color="#a78bfa" />, label: "Verified", desc: "Identity verified" },
          { icon: <Flame size={24} color="#f97316" />, label: "Trending", desc: "#3 this week" },
          { icon: <Gem size={24} color="#34d399" />, label: "Premium", desc: "Pro subscriber" },
          { icon: <Music2 size={24} color="#f472b6" />, label: "Sound Maker", desc: "1000+ tracks" },
        ].map(b => (
          <div key={b.label} style={{ background: "rgba(0,174,239,0.07)", border: "1px solid rgba(0,174,239,0.15)", borderRadius: 16, padding: 16, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
            {b.icon}
            <p style={{ color: "#fff", fontWeight: 700, fontSize: 13, margin: 0, textAlign: "center" }}>{b.label}</p>
            <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, margin: 0, textAlign: "center" }}>{b.desc}</p>
          </div>
        ))}
      </div>
    ),
    top: (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <p style={{ color: "rgba(255,255,255,0.55)", fontSize: 13, marginBottom: 8 }}>
          Your status is visible to all ConnextionZ members. Update it anytime.
        </p>
        {[
          { label: "Available to Collaborate", sub: "Open for new projects and partnerships", glow: "#00ff88" },
          { label: "Busy", sub: "Heads-down on current work", glow: "#f59e0b" },
          { label: "Open for Hire", sub: "Available for paid commissions", glow: "#a78bfa" },
          { label: "Live Now", sub: "Currently streaming or performing", glow: "#ff3333" },
        ].map((s, i) => (
          <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 14, background: i === 0 ? `${s.glow}15` : "rgba(255,255,255,0.04)", border: `1px solid ${i === 0 ? s.glow + "50" : "rgba(255,255,255,0.1)"}`, borderRadius: 12, padding: "14px 16px" }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: s.glow, boxShadow: `0 0 10px ${s.glow}`, flexShrink: 0 }} />
            <div>
              <p style={{ color: "#fff", fontWeight: 600, fontSize: 14, margin: "0 0 2px" }}>{s.label}</p>
              <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 12, margin: 0 }}>{s.sub}</p>
            </div>
            {i === 0 && <Check size={14} color={s.glow} style={{ marginLeft: "auto" }} />}
          </div>
        ))}
      </div>
    ),
  };

  if (!section) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(1,8,20,0.85)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        zIndex: 9999,
        padding: "0 16px",
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 80, opacity: 0 }}
        transition={{ type: "spring", damping: 26, stiffness: 320 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "rgba(8, 16, 40, 0.97)",
          border: "1px solid rgba(0,174,239,0.25)",
          borderRadius: "24px 24px 0 0",
          padding: "28px 28px 40px",
          width: "100%",
          maxWidth: 560,
          maxHeight: "78vh",
          overflowY: "auto",
          boxShadow: "0 -20px 60px rgba(0,174,239,0.12)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <h3 style={{ color: "#fff", fontWeight: 800, fontSize: 20, margin: 0, fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
            {titles[section]}
          </h3>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onClose}
            style={{
              width: 36, height: 36, borderRadius: "50%",
              background: "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.12)",
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer", color: "rgba(255,255,255,0.7)",
            }}
          >
            <X size={16} />
          </motion.button>
        </div>
        {content[section]}
      </motion.div>
    </motion.div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function HoloProfile({ onBack }: { onBack?: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rot, setRot] = useState({ x: -15, y: 0 });
  const [scale, setScale] = useState(1);
  const [expandedSection, setExpandedSection] = useState<ModalSection>(null);
  const dragStart = useRef<{ x: number; y: number; rx: number; ry: number } | null>(null);

  // Auto-rotation
  useEffect(() => {
    const id = setInterval(() => {
      if (!dragStart.current) {
        setRot((r) => ({ ...r, y: r.y + 0.3 }));
      }
    }, 16);
    return () => clearInterval(id);
  }, []);

  // Mouse drag
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragStart.current = { x: e.clientX, y: e.clientY, rx: rot.x, ry: rot.y };
  }, [rot]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragStart.current) return;
    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;
    setRot({ x: dragStart.current.rx - dy * 0.4, y: dragStart.current.ry + dx * 0.4 });
  }, []);

  const onMouseUp = useCallback(() => {
    dragStart.current = null;
  }, []);

  // Touch drag
  const onTouchStart = useCallback((e: React.TouchEvent) => {
    const t = e.touches[0];
    dragStart.current = { x: t.clientX, y: t.clientY, rx: rot.x, ry: rot.y };
  }, [rot]);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    if (!dragStart.current) return;
    const t = e.touches[0];
    const dx = t.clientX - dragStart.current.x;
    const dy = t.clientY - dragStart.current.y;
    setRot({ x: dragStart.current.rx - dy * 0.4, y: dragStart.current.ry + dx * 0.4 });
  }, []);

  const onTouchEnd = useCallback(() => {
    dragStart.current = null;
  }, []);

  // Scroll / pinch zoom
  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setScale((s) => Math.min(1.6, Math.max(0.6, s - e.deltaY * 0.001)));
  }, []);

  const actionButtons = [
    { icon: <UserPlus size={20} />, label: "Follow", style: { top: "15%", left: "5%" } },
    { icon: <MessageCircle size={20} />, label: "Message", style: { top: "50%", left: "2%", transform: "translateY(-50%)" } },
    { icon: <Zap size={20} />, label: "Collab", style: { bottom: "20%", left: "5%" } },
    { icon: <Briefcase size={20} />, label: "Hire", style: { bottom: "20%", right: "5%" } },
    { icon: <Share2 size={20} />, label: "Share", style: { top: "50%", right: "2%", transform: "translateY(-50%)" } },
  ];

  return (
    <div
      className="relative w-full min-h-screen flex items-center justify-center overflow-hidden"
      style={{ background: "linear-gradient(135deg, #010814 0%, #020c24 40%, #010814 100%)", fontFamily: "'Plus Jakarta Sans', sans-serif" }}
    >
      {/* Back button */}
      {onBack && (
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={onBack}
          style={{
            position: "absolute", top: 52, left: 20, zIndex: 50,
            width: 40, height: 40, borderRadius: "50%",
            background: "rgba(0,174,239,0.12)", border: "1px solid rgba(0,174,239,0.35)",
            backdropFilter: "blur(16px)", display: "flex", alignItems: "center", justifyContent: "center",
            cursor: "pointer", color: "#00AEEF",
          }}
        >
          <X size={18} />
        </motion.button>
      )}

      {/* Particle canvas */}
      <ParticleCanvas />

      {/* Grid overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(0,174,239,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,174,239,0.04) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }}
      />

      {/* Lighting blobs */}
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at 30% 20%, rgba(0,174,239,0.18) 0%, transparent 60%)" }} />
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at 80% 80%, rgba(100,50,255,0.12) 0%, transparent 50%)" }} />
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at 60% 10%, rgba(0,174,239,0.06) 0%, transparent 40%)" }} />
      </div>

      {/* 460px sphere container */}
      <div
        style={{ position: "relative", width: 460, height: 460, flexShrink: 0 }}
      >
        {/* Draggable perspective wrapper */}
        <div
          ref={containerRef}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
          onWheel={onWheel}
          style={{
            width: "100%",
            height: "100%",
            perspective: 1200,
            cursor: dragStart.current ? "grabbing" : "grab",
          }}
        >
          <div
            style={{
              width: "100%",
              height: "100%",
              position: "relative",
              transformStyle: "preserve-3d",
              transform: `scale(${scale}) rotateX(${rot.x}deg) rotateY(${rot.y}deg)`,
              transition: dragStart.current ? "none" : "transform 0.05s linear",
            }}
          >
            <FaceFront onExpand={() => setExpandedSection("front")} />
            <FaceLeft onExpand={() => setExpandedSection("left")} />
            <FaceRight onExpand={() => setExpandedSection("right")} />
            <FaceBack onExpand={() => setExpandedSection("back")} />
            <FaceBottom onExpand={() => setExpandedSection("bottom")} />
            <FaceTop onExpand={() => setExpandedSection("top")} />
          </div>
        </div>

        {/* Floating action buttons */}
        {actionButtons.map((btn) => (
          <div
            key={btn.label}
            style={{ position: "absolute", display: "flex", flexDirection: "column", alignItems: "center", gap: 4, ...btn.style }}
          >
            <motion.button
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.9 }}
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "rgba(0,174,239,0.12)",
                border: "1px solid rgba(0,174,239,0.4)",
                backdropFilter: "blur(16px)",
                WebkitBackdropFilter: "blur(16px)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                color: "#00AEEF",
                boxShadow: "0 4px 20px rgba(0,174,239,0.2)",
              }}
            >
              {btn.icon}
            </motion.button>
            <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 10, letterSpacing: 0.5, whiteSpace: "nowrap" }}>
              {btn.label}
            </span>
          </div>
        ))}
      </div>

      {/* Section expand modal */}
      <AnimatePresence>
        {expandedSection && (
          <ExpandModal section={expandedSection} onClose={() => setExpandedSection(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
