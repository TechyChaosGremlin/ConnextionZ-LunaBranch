import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  X, Mic, MicOff, Video, VideoOff, Share2, MessageCircle,
  Music2, Code2, Palette, Podcast, Film, Zap, Building2,
  Gamepad2, Users, GraduationCap, Briefcase, Globe,
  ChevronRight, Send, Bot, Sparkles, Play, Volume2,
  Wifi, Settings, Map, Home, Star, Crown, Shield,
  ArrowLeft, Plus, Search, Bell,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────
type View = "entry" | "hub" | "zone" | "avatar";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
}

interface NPCMessage {
  id: number;
  from: "aria" | "user";
  text: string;
}

interface CollabTask {
  id: number;
  text: string;
  col: "todo" | "inprogress" | "done";
}

// ─── Data ────────────────────────────────────────────────────────────────────
const AVATAR_SKINS = [
  { emoji: "🧑‍🎤", color: "#00AEEF" },
  { emoji: "👩‍🎨", color: "#ec4899" },
  { emoji: "🧑‍💻", color: "#22c55e" },
  { emoji: "👨‍🎵", color: "#a855f7" },
  { emoji: "🧑‍🚀", color: "#f59e0b" },
  { emoji: "👩‍🔬", color: "#ef4444" },
  { emoji: "🦸", color: "#06b6d4" },
  { emoji: "🧙", color: "#8b5cf6" },
];

const ZONES = [
  { id: "plaza", name: "Creator Plaza", icon: <Users size={20} />, color: "#00AEEF", desc: "Network & discover", online: 1247, emoji: "🏙️" },
  { id: "studio", name: "Music Studios", icon: <Music2 size={20} />, color: "#a855f7", desc: "Record & collaborate", online: 384, emoji: "🎵" },
  { id: "video", name: "Video Sets", icon: <Film size={20} />, color: "#ef4444", desc: "Produce content", online: 291, emoji: "🎬" },
  { id: "podcast", name: "Podcast Rooms", icon: <Podcast size={20} />, color: "#f59e0b", desc: "Broadcast live", online: 156, emoji: "🎙️" },
  { id: "gallery", name: "Art Gallery", icon: <Palette size={20} />, color: "#ec4899", desc: "Showcase & inspire", online: 203, emoji: "🎨" },
  { id: "coding", name: "Coding Labs", icon: <Code2 size={20} />, color: "#22c55e", desc: "Build together", online: 472, emoji: "💻" },
  { id: "startup", name: "Startup Incubator", icon: <Zap size={20} />, color: "#f97316", desc: "Launch & grow", online: 89, emoji: "🚀" },
  { id: "chess", name: "Chess Arena", icon: <Gamepad2 size={20} />, color: "#8b5cf6", desc: "Strategic minds", online: 134, emoji: "♟️" },
  { id: "concert", name: "Concert Venue", icon: <Volume2 size={20} />, color: "#00AEEF", desc: "Live performances", online: 3821, emoji: "🎤" },
  { id: "biz", name: "Convention Center", icon: <Building2 size={20} />, color: "#64748b", desc: "Business events", online: 612, emoji: "🏢" },
  { id: "campus", name: "Education Campus", icon: <GraduationCap size={20} />, color: "#10b981", desc: "Learn & teach", online: 924, emoji: "📚" },
  { id: "hq", name: "Private HQ", icon: <Shield size={20} />, color: "#7c3aed", desc: "Your team space", online: 12, emoji: "🔒" },
];

const CREATORS = [
  { id: 1, username: "nova.dj", score: 9.8, tags: ["Music", "DJ", "EDM"], online: true, avatar: "https://images.unsplash.com/photo-1517256673644-36ad11246d21?w=80&h=80&fit=crop&auto=format" },
  { id: 2, username: "zara.creates", score: 9.4, tags: ["Video", "Film", "Art"], online: true, avatar: "https://images.unsplash.com/photo-1758600436089-0660fce3e7e5?w=80&h=80&fit=crop&auto=format" },
  { id: 3, username: "beatsby.kai", score: 8.9, tags: ["Beats", "Producer"], online: true, avatar: "https://images.unsplash.com/photo-1638305610693-7f00e71500c3?w=80&h=80&fit=crop&auto=format" },
  { id: 4, username: "pixel.arjun", score: 8.6, tags: ["Code", "Design"], online: false, avatar: "https://images.unsplash.com/photo-1610716632318-acfc6a85d1ed?w=80&h=80&fit=crop&auto=format" },
  { id: 5, username: "lyra.voice", score: 9.1, tags: ["Podcast", "Writing"], online: true, avatar: "https://images.unsplash.com/photo-1772130204534-24c9a96b7c38?w=80&h=80&fit=crop&auto=format" },
  { id: 6, username: "hex.visuals", score: 8.3, tags: ["VFX", "Motion"], online: true, avatar: "https://images.unsplash.com/photo-1761957375235-46acb4862151?w=80&h=80&fit=crop&auto=format" },
];

const GALLERY_ARTWORKS = [
  { title: "Neon Genesis", creator: "hex.visuals", likes: 2341, img: "https://images.unsplash.com/photo-1550275994-cdc89cd1948f?w=300&h=400&fit=crop&auto=format" },
  { title: "Purple Drift", creator: "zara.creates", likes: 1892, img: "https://images.unsplash.com/photo-1617751218806-9077a9093d8b?w=300&h=400&fit=crop&auto=format" },
  { title: "Chromatic Storm", creator: "nova.dj", likes: 3104, img: "https://images.unsplash.com/photo-1549317336-206569e8475c?w=300&h=400&fit=crop&auto=format" },
  { title: "Signal Blue", creator: "pixel.arjun", likes: 987, img: "https://images.unsplash.com/photo-1618386230353-3631c1365be2?w=300&h=400&fit=crop&auto=format" },
  { title: "Light Trails", creator: "lyra.voice", likes: 1456, img: "https://images.unsplash.com/photo-1490049350474-498de43bc885?w=300&h=400&fit=crop&auto=format" },
  { title: "Dark Pulse", creator: "beatsby.kai", likes: 2788, img: "https://images.unsplash.com/photo-1550275994-72944c00abde?w=300&h=400&fit=crop&auto=format" },
];

const TICKER_TEXT = "🎵 nova.dj live in Concert Venue · 📹 zara.creates starting collab session · 🚀 beatsby.kai launched new startup idea · 🎨 hex.visuals drops new NFT series · 💻 pixel.arjun open-sourced metaverse SDK · 🎤 lyra.voice live podcast in 10 mins · ";

const ZONE_BG: Record<string, string> = {
  plaza: "linear-gradient(180deg,#000a1f 0%,#000510 100%)",
  studio: "linear-gradient(180deg,#0d0018 0%,#000510 100%)",
  coding: "linear-gradient(180deg,#000d08 0%,#000510 100%)",
  gallery: "linear-gradient(180deg,#100014 0%,#000510 100%)",
  concert: "linear-gradient(180deg,#000810 0%,#000000 100%)",
  campus: "linear-gradient(180deg,#001014 0%,#000510 100%)",
  default: "linear-gradient(180deg,#000a1f 0%,#000510 100%)",
};

const INITIAL_NPC_MESSAGES: NPCMessage[] = [
  { id: 1, from: "aria", text: "Welcome to the Metaverse! I've found 3 creators that match your collab style. Want me to make introductions?" },
  { id: 2, from: "aria", text: "There's a live music session in Studio 7 that matches your genre preferences — starting in 4 minutes." },
  { id: 3, from: "aria", text: "Your collab score went up by 0.2 this week. Keep it up! 🚀" },
];

const COLLAB_TASKS: CollabTask[] = [
  { id: 1, text: "Finalize track arrangement", col: "done" },
  { id: 2, text: "Record vocal takes", col: "done" },
  { id: 3, text: "Mix stems in DAW", col: "inprogress" },
  { id: 4, text: "Design album cover", col: "inprogress" },
  { id: 5, text: "Write press release", col: "todo" },
  { id: 6, text: "Schedule release date", col: "todo" },
];

// ─── Particle Canvas ──────────────────────────────────────────────────────────
function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const colors = ["#00AEEF", "#38bdf8", "#7c3aed", "#06b6d4"];
    let animId: number;

    const particles: Particle[] = Array.from({ length: 120 }, (_, i) => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      size: Math.random() * 2.5 + 0.5,
      opacity: Math.random() * 0.6 + 0.2,
      color: colors[i % 4],
    }));

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };

    resize();
    window.addEventListener("resize", resize);

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.save();
        ctx.globalAlpha = p.opacity;
        ctx.shadowBlur = 6;
        ctx.shadowColor = p.color;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
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

// ─── Floating City ────────────────────────────────────────────────────────────
const ISLANDS = [
  { w: 180, h: 50, top: "12%", left: "8%", delay: 0 },
  { w: 120, h: 35, top: "22%", left: "72%", delay: 0.7 },
  { w: 90, h: 30, top: "38%", left: "18%", delay: 1.4 },
  { w: 200, h: 65, top: "45%", left: "55%", delay: 2.1 },
  { w: 70, h: 28, top: "60%", left: "5%", delay: 0.3 },
  { w: 150, h: 45, top: "15%", left: "38%", delay: 1.1 },
  { w: 100, h: 38, top: "55%", left: "82%", delay: 1.8 },
  { w: 80, h: 32, top: "68%", left: "42%", delay: 0.9 },
  { w: 130, h: 40, top: "30%", left: "88%", delay: 2.5 },
];

function FloatingCity() {
  return (
    <>
      {ISLANDS.map((island, i) => (
        <motion.div
          key={i}
          style={{ position: "absolute", top: island.top, left: island.left }}
          animate={{ y: [0, -12, 0] }}
          transition={{ duration: 4 + i * 0.7, repeat: Infinity, ease: "easeInOut", delay: island.delay }}
        >
          {/* Island body */}
          <div
            style={{
              width: island.w,
              height: island.h,
              clipPath: "polygon(10% 0%, 90% 0%, 100% 100%, 0% 100%)",
              background: "linear-gradient(to bottom, rgba(0,174,239,0.25), rgba(0,174,239,0.04))",
              borderTop: "2px solid rgba(0,174,239,0.6)",
              position: "relative",
            }}
          >
            {/* Windows */}
            {Array.from({ length: Math.floor(island.w / 18) }).map((_, j) => (
              <div
                key={j}
                style={{
                  position: "absolute",
                  width: 4,
                  height: 4,
                  borderRadius: 1,
                  background: Math.random() > 0.4 ? "rgba(0,174,239,0.9)" : "rgba(124,58,237,0.7)",
                  top: Math.random() * (island.h - 8) + 4,
                  left: 12 + j * 16 + Math.random() * 6,
                  boxShadow: "0 0 4px rgba(0,174,239,0.8)",
                }}
              />
            ))}
          </div>
          {/* Light beam */}
          <div
            style={{
              width: Math.max(1, Math.floor(island.w * 0.015)),
              height: 80 + i * 10,
              background: "linear-gradient(to bottom, rgba(0,174,239,0.35), transparent)",
              margin: "0 auto",
            }}
          />
        </motion.div>
      ))}
      {/* Light rays */}
      {[
        { left: "20%", top: "0%", rotate: "-20deg" },
        { left: "50%", top: "0%", rotate: "5deg" },
        { left: "75%", top: "0%", rotate: "15deg" },
      ].map((ray, i) => (
        <motion.div
          key={i}
          style={{
            position: "absolute",
            left: ray.left,
            top: ray.top,
            width: 2,
            height: "60%",
            background: "linear-gradient(to bottom, rgba(0,174,239,0.0), rgba(0,174,239,0.25), rgba(0,174,239,0.0))",
            transform: `rotate(${ray.rotate})`,
            transformOrigin: "top center",
            pointerEvents: "none",
          }}
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{ duration: 3 + i, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </>
  );
}

// ─── Zone Body Renderers ──────────────────────────────────────────────────────
function ZonePlaza({ onCollab }: { onCollab: () => void }) {
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    { id: 1, user: "nova.dj", text: "Anyone down for a collab session tonight?" },
    { id: 2, user: "zara.creates", text: "I'm in! Working on a new visual EP" },
    { id: 3, user: "hex.visuals", text: "Dropped a new pack in the gallery 🔥" },
    { id: 4, user: "beatsby.kai", text: "Studio 7 is open — come through" },
    { id: 5, user: "lyra.voice", text: "Podcast recording in 20 mins, who wants in?" },
    { id: 6, user: "pixel.arjun", text: "Just merged the SDK update, check it out" },
  ]);

  const sendChat = () => {
    if (!chatInput.trim()) return;
    setChatMessages(m => [...m, { id: Date.now(), user: "you", text: chatInput }]);
    setChatInput("");
  };

  return (
    <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
      {/* Creators grid */}
      <div style={{ flex: 1, padding: "16px", overflowY: "auto", display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(200px,1fr))", gap: "12px", alignContent: "start" }}>
        {CREATORS.map((c) => (
          <div
            key={c.id}
            style={{
              background: "rgba(8,16,40,0.8)",
              border: "1px solid rgba(0,174,239,0.2)",
              borderRadius: 12,
              padding: 14,
              position: "relative",
            }}
          >
            {/* Pulse rings */}
            {c.online && (
              <div style={{ position: "absolute", top: 14, right: 14 }}>
                <motion.div
                  style={{ position: "absolute", width: 28, height: 28, borderRadius: "50%", border: "1px solid rgba(0,174,239,0.5)", top: -4, left: -4 }}
                  animate={{ scale: [1, 1.8], opacity: [0.6, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e" }} />
              </div>
            )}
            <img src={c.avatar} alt={c.username} style={{ width: 56, height: 56, borderRadius: "50%", objectFit: "cover", border: "2px solid rgba(0,174,239,0.4)", marginBottom: 8 }} />
            <div style={{ color: "white", fontWeight: 700, fontSize: 14 }}>@{c.username}</div>
            <div style={{ color: "#00AEEF", fontSize: 12, marginBottom: 6 }}>Collab Score: {c.score}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 10 }}>
              {c.tags.map(t => (
                <span key={t} style={{ fontSize: 10, padding: "2px 6px", borderRadius: 20, background: "rgba(0,174,239,0.12)", color: "rgba(255,255,255,0.7)", border: "1px solid rgba(0,174,239,0.2)" }}>{t}</span>
              ))}
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button style={{ flex: 1, padding: "5px 0", fontSize: 11, borderRadius: 6, background: "rgba(0,174,239,0.15)", border: "1px solid rgba(0,174,239,0.3)", color: "#00AEEF", cursor: "pointer" }}>Connect</button>
              <button onClick={onCollab} style={{ flex: 1, padding: "5px 0", fontSize: 11, borderRadius: 6, background: "linear-gradient(135deg,#00AEEF,#7c3aed)", border: "none", color: "white", cursor: "pointer", fontWeight: 600 }}>Collab</button>
            </div>
          </div>
        ))}
      </div>
      {/* Chat sidebar */}
      <div style={{ width: 260, borderLeft: "1px solid rgba(0,174,239,0.15)", display: "flex", flexDirection: "column", background: "rgba(4,10,28,0.6)" }}>
        <div style={{ padding: "10px 12px", borderBottom: "1px solid rgba(0,174,239,0.1)", color: "rgba(255,255,255,0.5)", fontSize: 11, fontWeight: 700, letterSpacing: "0.1em" }}>ZONE CHAT</div>
        <div style={{ flex: 1, overflowY: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
          {chatMessages.map(m => (
            <div key={m.id}>
              <span style={{ color: "#00AEEF", fontSize: 11, fontWeight: 700 }}>@{m.user} </span>
              <span style={{ color: "rgba(255,255,255,0.75)", fontSize: 12 }}>{m.text}</span>
            </div>
          ))}
        </div>
        <div style={{ padding: 8, borderTop: "1px solid rgba(0,174,239,0.1)", display: "flex", gap: 6 }}>
          <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === "Enter" && sendChat()} placeholder="Type a message…" style={{ flex: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(0,174,239,0.2)", borderRadius: 6, padding: "5px 8px", color: "white", fontSize: 12, outline: "none" }} />
          <button onClick={sendChat} style={{ padding: "0 10px", borderRadius: 6, background: "#00AEEF", border: "none", color: "white", cursor: "pointer", display: "flex", alignItems: "center" }}><Send size={13} /></button>
        </div>
      </div>
    </div>
  );
}

function ZoneStudio() {
  const [playing, setPlaying] = useState(false);
  const [bpm] = useState(128);
  const tracks = [
    { label: "Kick", color: "#ef4444", muted: false },
    { label: "Snare", color: "#f59e0b", muted: false },
    { label: "Bass", color: "#a855f7", muted: false },
    { label: "Melody", color: "#00AEEF", muted: false },
  ];
  const noteRows = [0, 1, 2, 3];
  const noteBlocks: { row: number; col: number; color: string }[] = [
    { row: 0, col: 0, color: "#ef4444" }, { row: 0, col: 4, color: "#ef4444" },
    { row: 0, col: 8, color: "#ef4444" }, { row: 0, col: 12, color: "#ef4444" },
    { row: 1, col: 2, color: "#f59e0b" }, { row: 1, col: 6, color: "#f59e0b" },
    { row: 1, col: 10, color: "#f59e0b" }, { row: 1, col: 14, color: "#f59e0b" },
    { row: 2, col: 0, color: "#a855f7" }, { row: 2, col: 2, color: "#a855f7" },
    { row: 2, col: 7, color: "#a855f7" }, { row: 2, col: 9, color: "#a855f7" },
    { row: 3, col: 1, color: "#00AEEF" }, { row: 3, col: 3, color: "#00AEEF" },
    { row: 3, col: 5, color: "#00AEEF" }, { row: 3, col: 11, color: "#00AEEF" },
    { row: 3, col: 13, color: "#00AEEF" },
  ];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", padding: 12, gap: 10 }}>
      {/* Track list */}
      <div style={{ background: "rgba(8,16,40,0.8)", borderRadius: 10, border: "1px solid rgba(0,174,239,0.15)", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
        {tracks.map((track, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 48, color: "rgba(255,255,255,0.6)", fontSize: 11, fontWeight: 700 }}>{track.label}</span>
            <button style={{ padding: "2px 6px", fontSize: 10, borderRadius: 4, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}>M</button>
            <button style={{ padding: "2px 6px", fontSize: 10, borderRadius: 4, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}>S</button>
            <input type="range" min={0} max={100} defaultValue={75} style={{ width: 60, accentColor: track.color }} />
            {/* Waveform */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 1.5, height: 24 }}>
              {Array.from({ length: 48 }).map((_, j) => (
                <motion.div
                  key={j}
                  style={{ width: 2, borderRadius: 1, background: track.color, opacity: 0.7 }}
                  animate={playing ? { height: [4, Math.random() * 18 + 4, 4] } : { height: Math.abs(Math.sin(j * 0.4)) * 14 + 3 }}
                  transition={playing ? { duration: 0.3 + Math.random() * 0.3, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      {/* Transport */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(8,16,40,0.8)", borderRadius: 8, border: "1px solid rgba(0,174,239,0.15)", padding: "8px 12px" }}>
        <button style={transportBtn}>⏮</button>
        <button onClick={() => setPlaying(p => !p)} style={{ ...transportBtn, background: playing ? "#ef4444" : "#00AEEF", color: "white", borderRadius: "50%", width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center" }}>
          {playing ? "⏸" : "▶"}
        </button>
        <button style={transportBtn}>⏭</button>
        <button style={{ ...transportBtn, color: "#ef4444" }}>⏺</button>
        <div style={{ marginLeft: 8, color: "rgba(255,255,255,0.5)", fontSize: 12 }}>
          <span style={{ color: "#00AEEF", fontWeight: 700 }}>{bpm} BPM</span> · 4/4
        </div>
      </div>
      {/* Piano roll */}
      <div style={{ flex: 1, background: "rgba(8,16,40,0.8)", borderRadius: 10, border: "1px solid rgba(0,174,239,0.15)", padding: 10, overflow: "hidden" }}>
        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, fontWeight: 700, marginBottom: 8 }}>PIANO ROLL</div>
        <div style={{ position: "relative", display: "grid", gridTemplateRows: "repeat(4,32px)", gap: 2 }}>
          {noteRows.map(row => (
            <div key={row} style={{ position: "relative", background: "rgba(255,255,255,0.02)", borderRadius: 4, display: "grid", gridTemplateColumns: "repeat(16,1fr)", gap: 2 }}>
              {Array.from({ length: 16 }).map((_, col) => {
                const block = noteBlocks.find(b => b.row === row && b.col === col);
                return (
                  <div key={col} style={{ borderRadius: 3, background: block ? block.color : "transparent", opacity: block ? 0.85 : 1, border: block ? "none" : "1px solid rgba(255,255,255,0.04)", cursor: "pointer" }} />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const transportBtn: React.CSSProperties = {
  background: "rgba(255,255,255,0.07)",
  border: "1px solid rgba(255,255,255,0.1)",
  color: "rgba(255,255,255,0.7)",
  borderRadius: 6,
  padding: "4px 10px",
  cursor: "pointer",
  fontSize: 14,
};

function ZoneCoding() {
  const codeLines = [
    { tokens: [{ t: "import ", c: "#a855f7" }, { t: "{ useState, useEffect }", c: "#00AEEF" }, { t: " from ", c: "#a855f7" }, { t: "'react'", c: "#f59e0b" }] },
    { tokens: [] },
    { tokens: [{ t: "interface ", c: "#a855f7" }, { t: "TrackProps ", c: "#22c55e" }, { t: "{", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [{ t: "  id", c: "#00AEEF" }, { t: ": ", c: "rgba(255,255,255,0.5)" }, { t: "number", c: "#f59e0b" }, { t: ";", c: "rgba(255,255,255,0.5)" }] },
    { tokens: [{ t: "  name", c: "#00AEEF" }, { t: ": ", c: "rgba(255,255,255,0.5)" }, { t: "string", c: "#f59e0b" }, { t: ";", c: "rgba(255,255,255,0.5)" }] },
    { tokens: [{ t: "}", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [] },
    { tokens: [{ t: "export function ", c: "#a855f7" }, { t: "TrackItem", c: "#22c55e" }, { t: "({ id, name }", c: "rgba(255,255,255,0.7)" }, { t: ": ", c: "rgba(255,255,255,0.5)" }, { t: "TrackProps", c: "#22c55e" }, { t: ") {", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [{ t: "  const ", c: "#a855f7" }, { t: "[active, setActive]", c: "#00AEEF" }, { t: " = useState(", c: "rgba(255,255,255,0.7)" }, { t: "false", c: "#f59e0b" }, { t: ");", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [] },
    { tokens: [{ t: "  // ", c: "rgba(100,116,139,0.8)" }, { t: "Toggle track active state", c: "rgba(100,116,139,0.8)" }] },
    { tokens: [{ t: "  return ", c: "#a855f7" }, { t: "(", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [{ t: "    <div ", c: "#ef4444" }, { t: "onClick", c: "#00AEEF" }, { t: "={() => setActive(!active)}", c: "rgba(255,255,255,0.7)" }, { t: ">", c: "#ef4444" }] },
    { tokens: [{ t: "      {name}", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [{ t: "    </div>", c: "#ef4444" }] },
    { tokens: [{ t: "  );", c: "rgba(255,255,255,0.7)" }] },
    { tokens: [{ t: "}", c: "rgba(255,255,255,0.7)" }] },
  ];

  const files = ["index.tsx", "TrackItem.tsx", "AudioEngine.ts", "types.ts", "styles.css"];

  return (
    <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
      {/* File tree */}
      <div style={{ width: 140, borderRight: "1px solid rgba(0,174,239,0.1)", background: "rgba(4,10,28,0.6)", padding: 10 }}>
        <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>EXPLORER</div>
        {files.map((f, i) => (
          <div key={f} style={{ padding: "4px 6px", borderRadius: 4, cursor: "pointer", background: i === 1 ? "rgba(0,174,239,0.1)" : "transparent", color: i === 1 ? "#00AEEF" : "rgba(255,255,255,0.55)", fontSize: 12, marginBottom: 2 }}>
            {f}
          </div>
        ))}
      </div>
      {/* Editor */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "6px 12px", borderBottom: "1px solid rgba(0,174,239,0.1)", background: "rgba(4,10,28,0.4)", display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "#00AEEF" }}>TrackItem.tsx</span>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>TypeScript · React</span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
            <button style={{ ...transportBtn, fontSize: 11, color: "#22c55e" }}>▶ Run</button>
            <button style={{ ...transportBtn, fontSize: 11 }}><Share2 size={11} /></button>
          </div>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "10px 0", fontFamily: "'JetBrains Mono',monospace", fontSize: 12, lineHeight: 1.7 }}>
          {codeLines.map((line, i) => (
            <div key={i} style={{ display: "flex", paddingLeft: 8 }}>
              <span style={{ color: "rgba(255,255,255,0.2)", minWidth: 28, textAlign: "right", paddingRight: 12, userSelect: "none" }}>{i + 1}</span>
              <span>{line.tokens.map((tok, j) => <span key={j} style={{ color: tok.c }}>{tok.t}</span>)}</span>
            </div>
          ))}
        </div>
        {/* Terminal */}
        <div style={{ height: 100, borderTop: "1px solid rgba(0,174,239,0.1)", background: "#000d06", padding: 8, fontFamily: "'JetBrains Mono',monospace", fontSize: 11 }}>
          <div style={{ color: "rgba(255,255,255,0.3)", marginBottom: 4 }}>TERMINAL</div>
          <div style={{ color: "#22c55e" }}>$ npm run dev</div>
          <div style={{ color: "rgba(34,197,94,0.6)" }}>  ✓ ready on http://localhost:5173</div>
          <div style={{ color: "rgba(34,197,94,0.6)" }}>  ✓ 3 modules compiled</div>
        </div>
      </div>
    </div>
  );
}

function ZoneGallery() {
  const [index, setIndex] = useState(0);
  const prev = () => setIndex(i => (i - 1 + GALLERY_ARTWORKS.length) % GALLERY_ARTWORKS.length);
  const next = () => setIndex(i => (i + 1) % GALLERY_ARTWORKS.length);

  const visible = [
    GALLERY_ARTWORKS[(index - 1 + GALLERY_ARTWORKS.length) % GALLERY_ARTWORKS.length],
    GALLERY_ARTWORKS[index],
    GALLERY_ARTWORKS[(index + 1) % GALLERY_ARTWORKS.length],
  ];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", perspective: "1200px", padding: 16, gap: 16 }}>
      <div style={{ display: "flex", gap: 24, alignItems: "center", perspective: "1200px" }}>
        <button onClick={prev} style={{ ...transportBtn, fontSize: 18, padding: "8px 14px" }}>←</button>
        {visible.map((art, i) => (
          <motion.div
            key={art.title}
            animate={{ scale: i === 1 ? 1 : 0.8, rotateY: i === 0 ? 20 : i === 2 ? -20 : 0, opacity: i === 1 ? 1 : 0.5 }}
            transition={{ duration: 0.4 }}
            style={{ cursor: "pointer", transformStyle: "preserve-3d" }}
          >
            <div style={{ borderRadius: 8, overflow: "hidden", border: i === 1 ? "2px solid rgba(0,174,239,0.6)" : "2px solid rgba(255,255,255,0.1)", boxShadow: i === 1 ? "0 0 30px rgba(0,174,239,0.2)" : "none", width: i === 1 ? 240 : 160 }}>
              <img src={art.img} alt={art.title} style={{ width: "100%", height: i === 1 ? 320 : 200, objectFit: "cover", display: "block", background: "#0a0a1a" }} />
              {i === 1 && (
                <div style={{ background: "rgba(8,16,40,0.95)", padding: "10px 12px" }}>
                  <div style={{ color: "white", fontWeight: 700, fontSize: 14 }}>{art.title}</div>
                  <div style={{ color: "#00AEEF", fontSize: 12 }}>@{art.creator}</div>
                  <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, marginTop: 4 }}>♥ {art.likes.toLocaleString()} likes</div>
                </div>
              )}
            </div>
          </motion.div>
        ))}
        <button onClick={next} style={{ ...transportBtn, fontSize: 18, padding: "8px 14px" }}>→</button>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {GALLERY_ARTWORKS.map((_, i) => (
          <button key={i} onClick={() => setIndex(i)} style={{ width: 6, height: 6, borderRadius: "50%", background: i === index ? "#00AEEF" : "rgba(255,255,255,0.2)", border: "none", cursor: "pointer", padding: 0 }} />
        ))}
      </div>
      <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 11 }}>203 visitors · Gallery walk mode</div>
    </div>
  );
}

function ZoneConcert() {
  const [reactions, setReactions] = useState<{ id: number; emoji: string; x: number }[]>([]);
  const [progress, setProgress] = useState(42);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    { id: 1, user: "nova.dj", text: "This drop is insane 🔥" },
    { id: 2, user: "lyra.voice", text: "Best set of the year" },
    { id: 3, user: "hex.visuals", text: "⚡⚡⚡" },
  ]);

  const addReaction = (emoji: string) => {
    const id = Date.now();
    setReactions(r => [...r, { id, emoji, x: Math.random() * 80 + 10 }]);
    setTimeout(() => setReactions(r => r.filter(x => x.id !== id)), 2500);
  };

  const sendChat = () => {
    if (!chatInput.trim()) return;
    setChatMessages(m => [...m, { id: Date.now(), user: "you", text: chatInput }]);
    setChatInput("");
  };

  useEffect(() => {
    const t = setInterval(() => setProgress(p => (p + 0.2) % 100), 500);
    return () => clearInterval(t);
  }, []);

  const audienceEmojis = ["🧑‍🎤","👩‍🎨","🧑‍💻","🦸","🧙","👨‍🎵","🧑‍🚀","👩‍🔬","🎵","🎤","🎧","🎶","⚡","🔥","🎸","🥁","🎹","🎺","🎻","🪗"];

  return (
    <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
        {/* Stage */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative", background: "radial-gradient(ellipse 60% 40% at 50% 30%, rgba(0,174,239,0.12) 0%, transparent 70%)" }}>
          {/* Floating reactions */}
          <AnimatePresence>
            {reactions.map(r => (
              <motion.div key={r.id} initial={{ opacity: 1, y: 0 }} animate={{ opacity: 0, y: -120 }} exit={{ opacity: 0 }} transition={{ duration: 2.5 }}
                style={{ position: "absolute", bottom: "30%", left: `${r.x}%`, fontSize: 24, pointerEvents: "none", zIndex: 20 }}>
                {r.emoji}
              </motion.div>
            ))}
          </AnimatePresence>
          {/* Spotlight */}
          <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)", width: 200, height: "50%", background: "radial-gradient(ellipse at top, rgba(0,174,239,0.18) 0%, transparent 70%)", pointerEvents: "none" }} />
          {/* Performer */}
          <motion.div animate={{ scale: [1, 1.04, 1] }} transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}>
            <div style={{ width: 90, height: 90, borderRadius: "50%", background: "linear-gradient(135deg,#00AEEF,#7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, boxShadow: "0 0 40px rgba(0,174,239,0.5), 0 0 80px rgba(124,58,237,0.3)", marginBottom: 12 }}>🎤</div>
          </motion.div>
          <div style={{ color: "white", fontWeight: 700, fontSize: 16 }}>nova.dj</div>
          <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>Now Playing: Midnight Drive</div>
          {/* Progress */}
          <div style={{ marginTop: 10, width: 200 }}>
            <div style={{ height: 3, background: "rgba(255,255,255,0.1)", borderRadius: 2 }}>
              <div style={{ height: "100%", width: `${progress}%`, background: "linear-gradient(90deg,#00AEEF,#7c3aed)", borderRadius: 2, transition: "width 0.5s linear" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, color: "rgba(255,255,255,0.3)", fontSize: 10 }}>
              <span>2:{String(Math.floor(progress * 0.6)).padStart(2,"0")}</span><span>5:47</span>
            </div>
          </div>
          {/* Audience */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 16, maxWidth: 320, justifyContent: "center" }}>
            {audienceEmojis.map((e, i) => (
              <motion.div key={i} style={{ fontSize: 20 }} animate={{ y: [0, -4, 0] }} transition={{ duration: 1.5 + i * 0.1, repeat: Infinity, delay: i * 0.08 }}>{e}</motion.div>
            ))}
          </div>
          {/* Reactions */}
          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            {["🔥","❤️","🎵","⚡"].map(e => (
              <button key={e} onClick={() => addReaction(e)} style={{ fontSize: 22, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, padding: "6px 10px", cursor: "pointer" }}>{e}</button>
            ))}
          </div>
          {/* Visualizer */}
          <div style={{ display: "flex", gap: 2, alignItems: "flex-end", height: 30, marginTop: 12 }}>
            {Array.from({ length: 32 }).map((_, i) => (
              <motion.div key={i} style={{ width: 4, borderRadius: 2, background: `hsl(${190 + i * 4},100%,60%)` }}
                animate={{ height: [4, Math.random() * 24 + 4, 4] }} transition={{ duration: 0.3 + Math.random() * 0.3, repeat: Infinity, ease: "easeInOut" }} />
            ))}
          </div>
        </div>
      </div>
      {/* Chat */}
      <div style={{ width: 240, borderLeft: "1px solid rgba(0,174,239,0.15)", display: "flex", flexDirection: "column", background: "rgba(4,10,28,0.6)" }}>
        <div style={{ padding: "10px 12px", borderBottom: "1px solid rgba(0,174,239,0.1)", color: "rgba(255,255,255,0.5)", fontSize: 11, fontWeight: 700 }}>LIVE CHAT</div>
        <div style={{ flex: 1, overflowY: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
          {chatMessages.map(m => (
            <div key={m.id}><span style={{ color: "#00AEEF", fontSize: 11, fontWeight: 700 }}>@{m.user} </span><span style={{ color: "rgba(255,255,255,0.75)", fontSize: 12 }}>{m.text}</span></div>
          ))}
        </div>
        <div style={{ padding: 8, borderTop: "1px solid rgba(0,174,239,0.1)", display: "flex", gap: 6 }}>
          <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === "Enter" && sendChat()} placeholder="React…" style={{ flex: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(0,174,239,0.2)", borderRadius: 6, padding: "5px 8px", color: "white", fontSize: 12, outline: "none" }} />
          <button onClick={sendChat} style={{ padding: "0 8px", borderRadius: 6, background: "#00AEEF", border: "none", color: "white", cursor: "pointer" }}><Send size={12} /></button>
        </div>
      </div>
    </div>
  );
}

function ZoneCampus() {
  const [handRaised, setHandRaised] = useState(false);
  const students = ["🧑‍💻","👩‍🎨","🧑‍🎤","🦸","🧙","👨‍🎵","👩‍🔬","🧑‍🚀"];
  const [qaMessages] = useState([
    { id: 1, user: "pixel.arjun", text: "What's the difference between major and minor keys?" },
    { id: 2, user: "zara.creates", text: "Can you explain the circle of fifths again?" },
  ]);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", padding: 12, gap: 10 }}>
      {/* Session info */}
      <div style={{ background: "rgba(8,16,40,0.8)", borderRadius: 8, border: "1px solid rgba(16,185,129,0.2)", padding: "8px 12px", display: "flex", gap: 16, alignItems: "center" }}>
        <span style={{ color: "#10b981", fontWeight: 700, fontSize: 13 }}>Advanced Music Theory</span>
        <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>45 min remaining</span>
        <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>924 enrolled</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 4, alignItems: "center" }}><div style={{ width: 6, height: 6, borderRadius: "50%", background: "#ef4444" }} /><span style={{ color: "#ef4444", fontSize: 12, fontWeight: 700 }}>LIVE</span></div>
      </div>
      {/* Presenter */}
      <div style={{ flex: 1, display: "flex", gap: 10, overflow: "hidden" }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ flex: 1, background: "rgba(8,16,40,0.8)", borderRadius: 10, border: "1px solid rgba(16,185,129,0.2)", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at center, rgba(16,185,129,0.08) 0%, transparent 70%)" }} />
            <div style={{ textAlign: "center", zIndex: 1 }}>
              <div style={{ fontSize: 56, marginBottom: 8 }}>👨‍🏫</div>
              <div style={{ color: "white", fontWeight: 700 }}>Prof. harmonix.eth</div>
              <div style={{ marginTop: 12, background: "rgba(8,16,40,0.9)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: 8, padding: "16px 24px", maxWidth: 260 }}>
                <div style={{ color: "#10b981", fontSize: 10, fontWeight: 700, letterSpacing: "0.15em", marginBottom: 8 }}>SLIDE 3 / 12</div>
                <div style={{ color: "white", fontWeight: 700, fontSize: 16, marginBottom: 6 }}>Introduction to Music Theory</div>
                <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, lineHeight: 1.6 }}>Understanding scales, intervals, and chord progressions as the foundation of musical composition.</div>
              </div>
            </div>
          </div>
          {/* Students */}
          <div style={{ display: "flex", gap: 8, overflowX: "auto", padding: "4px 0" }}>
            {students.map((e, i) => (
              <div key={i} style={{ minWidth: 70, background: "rgba(8,16,40,0.8)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, padding: "8px 4px", textAlign: "center" }}>
                <div style={{ fontSize: 24 }}>{e}</div>
                <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 9, marginTop: 3 }}>Student {i + 1}</div>
              </div>
            ))}
          </div>
        </div>
        {/* Q&A */}
        <div style={{ width: 220, background: "rgba(8,16,40,0.8)", borderRadius: 10, border: "1px solid rgba(16,185,129,0.2)", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid rgba(16,185,129,0.1)", color: "rgba(255,255,255,0.5)", fontSize: 11, fontWeight: 700 }}>Q&A</div>
          <div style={{ flex: 1, overflowY: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
            {qaMessages.map(m => (
              <div key={m.id} style={{ background: "rgba(255,255,255,0.04)", borderRadius: 6, padding: 8 }}>
                <div style={{ color: "#10b981", fontSize: 11, fontWeight: 700, marginBottom: 3 }}>@{m.user}</div>
                <div style={{ color: "rgba(255,255,255,0.7)", fontSize: 12 }}>{m.text}</div>
              </div>
            ))}
          </div>
          <div style={{ padding: 10, borderTop: "1px solid rgba(16,185,129,0.1)" }}>
            <button onClick={() => setHandRaised(h => !h)} style={{ width: "100%", padding: "8px 0", borderRadius: 8, background: handRaised ? "rgba(16,185,129,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${handRaised ? "#10b981" : "rgba(255,255,255,0.1)"}`, color: handRaised ? "#10b981" : "rgba(255,255,255,0.6)", cursor: "pointer", fontSize: 13 }}>
              {handRaised ? "✋ Hand Raised" : "✋ Raise Hand"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ZoneDefault({ zone }: { zone: typeof ZONES[0] }) {
  return (
    <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16 }}>
      <div style={{ fontSize: 64 }}>{zone.emoji}</div>
      <div style={{ color: "white", fontSize: 20, fontWeight: 700 }}>{zone.name}</div>
      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 14 }}>{zone.desc}</div>
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e" }} />
        <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 13 }}>{zone.online.toLocaleString()} online</span>
      </div>
    </div>
  );
}

// ─── NPC Panel ────────────────────────────────────────────────────────────────
function NPCPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<NPCMessage[]>(INITIAL_NPC_MESSAGES);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const ARIA_RESPONSES = [
    "Great question! I'm analyzing your collab network for the best match...",
    "I found 2 upcoming events that align with your creative profile.",
    "Your zone activity is up 34% this week — you're on fire!",
    "I can connect you with nova.dj — she's online and open to collabs right now.",
    "Want me to schedule a studio session for you?",
  ];

  const send = () => {
    if (!input.trim()) return;
    const userMsg: NPCMessage = { id: Date.now(), from: "user", text: input };
    setInput("");
    setMessages(m => [...m, userMsg]);
    setTimeout(() => {
      setMessages(m => [...m, { id: Date.now() + 1, from: "aria", text: ARIA_RESPONSES[Math.floor(Math.random() * ARIA_RESPONSES.length)] }]);
    }, 800);
  };

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  return (
    <motion.div
      initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 26, stiffness: 220 }}
      style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: 320, background: "rgba(4,12,30,0.97)", backdropFilter: "blur(24px)", borderLeft: "1px solid rgba(0,174,239,0.2)", zIndex: 50, display: "flex", flexDirection: "column" }}
    >
      <div style={{ padding: "16px 14px", borderBottom: "1px solid rgba(0,174,239,0.15)", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 36, height: 36, borderRadius: "50%", background: "linear-gradient(135deg,#00AEEF,#7c3aed)", display: "flex", alignItems: "center", justifyContent: "center" }}><Bot size={18} color="white" /></div>
        <div>
          <div style={{ color: "white", fontWeight: 700, fontSize: 14 }}>ARIA</div>
          <div style={{ color: "#00AEEF", fontSize: 11 }}>AI Assistant · Online</div>
        </div>
        <button onClick={onClose} style={{ marginLeft: "auto", background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer" }}><X size={18} /></button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 12, display: "flex", flexDirection: "column", gap: 10 }}>
        {messages.map(m => (
          <div key={m.id} style={{ display: "flex", justifyContent: m.from === "user" ? "flex-end" : "flex-start" }}>
            <div style={{ maxWidth: "80%", padding: "8px 12px", borderRadius: m.from === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px", background: m.from === "user" ? "linear-gradient(135deg,#00AEEF,#7c3aed)" : "rgba(255,255,255,0.07)", color: "white", fontSize: 13, lineHeight: 1.5 }}>
              {m.text}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div style={{ padding: 10, borderTop: "1px solid rgba(0,174,239,0.15)", display: "flex", gap: 8 }}>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} placeholder="Ask ARIA anything…" style={{ flex: 1, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(0,174,239,0.25)", borderRadius: 8, padding: "7px 10px", color: "white", fontSize: 13, outline: "none" }} />
        <button onClick={send} style={{ padding: "0 12px", borderRadius: 8, background: "linear-gradient(135deg,#00AEEF,#7c3aed)", border: "none", color: "white", cursor: "pointer" }}><Send size={14} /></button>
      </div>
    </motion.div>
  );
}

// ─── Collab Panel ─────────────────────────────────────────────────────────────
function CollabPanel({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<"whiteboard" | "code" | "notes" | "board">("whiteboard");
  const [notes, setNotes] = useState("Session notes — Music Theory collab\n\nKey: A minor\nTempo: 128 BPM\nStyle: Dark ambient / EDM hybrid\n\nIdeas:\n- Open with arpeggio build\n- Drop at bar 32\n- Feature nova.dj on vocals");

  const tabs: { id: "whiteboard" | "code" | "notes" | "board"; label: string }[] = [
    { id: "whiteboard", label: "Whiteboard" },
    { id: "code", label: "Code" },
    { id: "notes", label: "Notes" },
    { id: "board", label: "Board" },
  ];

  const kanbanCols: { id: CollabTask["col"]; label: string; color: string }[] = [
    { id: "todo", label: "Todo", color: "#64748b" },
    { id: "inprogress", label: "In Progress", color: "#f59e0b" },
    { id: "done", label: "Done", color: "#22c55e" },
  ];

  return (
    <motion.div
      initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
      transition={{ type: "spring", damping: 26, stiffness: 220 }}
      style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: "55%", background: "rgba(4,12,30,0.97)", backdropFilter: "blur(24px)", borderTop: "1px solid rgba(0,174,239,0.2)", zIndex: 50, borderRadius: "20px 20px 0 0", display: "flex", flexDirection: "column" }}
    >
      <div style={{ padding: "12px 16px", borderBottom: "1px solid rgba(0,174,239,0.12)", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Collab Tools</span>
        <div style={{ display: "flex", gap: 4, marginLeft: 12 }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: "4px 12px", borderRadius: 6, fontSize: 12, border: "1px solid rgba(0,174,239,0.2)", background: tab === t.id ? "rgba(0,174,239,0.2)" : "transparent", color: tab === t.id ? "#00AEEF" : "rgba(255,255,255,0.5)", cursor: "pointer" }}>{t.label}</button>
          ))}
        </div>
        <button onClick={onClose} style={{ marginLeft: "auto", background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer" }}><X size={18} /></button>
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        {tab === "whiteboard" && (
          <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 12px", borderBottom: "1px solid rgba(0,174,239,0.1)", display: "flex", gap: 6 }}>
              {["#00AEEF","#ffffff","#f59e0b","#ef4444"].map(c => (
                <div key={c} style={{ width: 18, height: 18, borderRadius: "50%", background: c, cursor: "pointer", border: "2px solid rgba(255,255,255,0.2)" }} />
              ))}
              <button style={{ ...transportBtn, fontSize: 11, marginLeft: 8 }}>Clear</button>
              <button style={{ ...transportBtn, fontSize: 11 }}>Export</button>
            </div>
            <div style={{ flex: 1, background: "rgba(255,255,255,0.02)", position: "relative", overflow: "hidden" }}>
              <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.4 }}>
                <circle cx="120" cy="80" r="40" fill="none" stroke="#00AEEF" strokeWidth="2" />
                <rect x="220" y="50" width="80" height="60" fill="none" stroke="#7c3aed" strokeWidth="2" rx="4" />
                <line x1="80" y1="150" x2="320" y2="120" stroke="#f59e0b" strokeWidth="2" />
                <path d="M 400 60 Q 450 30 500 80 T 580 60" fill="none" stroke="#00AEEF" strokeWidth="2" />
                <text x="120" y="145" fill="rgba(255,255,255,0.5)" fontSize="12">Track idea</text>
                <text x="225" y="87" fill="rgba(255,255,255,0.5)" fontSize="11">Drop zone</text>
              </svg>
            </div>
          </div>
        )}
        {tab === "code" && (
          <div style={{ height: "100%", overflowY: "auto", padding: 16, fontFamily: "'JetBrains Mono',monospace", fontSize: 12, lineHeight: 1.8 }}>
            <span style={{ color: "#a855f7" }}>const </span><span style={{ color: "#00AEEF" }}>generateBeat</span><span style={{ color: "rgba(255,255,255,0.7)" }}> = (</span><span style={{ color: "#f59e0b" }}>bpm</span><span style={{ color: "rgba(255,255,255,0.7)" }}>: </span><span style={{ color: "#22c55e" }}>number</span><span style={{ color: "rgba(255,255,255,0.7)" }}>) ={">"} {"{"}</span><br />
            <span style={{ color: "rgba(100,116,139,0.8)" }}>  // Quantize to 16th notes</span><br />
            <span style={{ color: "rgba(255,255,255,0.7)" }}>  </span><span style={{ color: "#a855f7" }}>const </span><span style={{ color: "#00AEEF" }}>interval</span><span style={{ color: "rgba(255,255,255,0.7)" }}> = </span><span style={{ color: "#f59e0b" }}>60000</span><span style={{ color: "rgba(255,255,255,0.7)" }}> / bpm / </span><span style={{ color: "#f59e0b" }}>4</span><span style={{ color: "rgba(255,255,255,0.7)" }}>;</span><br />
            <span style={{ color: "rgba(255,255,255,0.7)" }}>  </span><span style={{ color: "#a855f7" }}>return </span><span style={{ color: "rgba(255,255,255,0.7)" }}>{"{ interval, steps: " }</span><span style={{ color: "#f59e0b" }}>16</span><span style={{ color: "rgba(255,255,255,0.7)" }}>{" }"}</span><br />
            <span style={{ color: "rgba(255,255,255,0.7)" }}>{"}"}</span>
          </div>
        )}
        {tab === "notes" && (
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Collaborative notes…"
            style={{ width: "100%", height: "100%", background: "transparent", border: "none", color: "rgba(255,255,255,0.75)", fontSize: 13, lineHeight: 1.7, padding: 16, outline: "none", resize: "none", fontFamily: "'Plus Jakarta Sans',sans-serif", boxSizing: "border-box" }}
          />
        )}
        {tab === "board" && (
          <div style={{ display: "flex", gap: 12, padding: 12, height: "100%", boxSizing: "border-box", overflowX: "auto" }}>
            {kanbanCols.map(col => (
              <div key={col.id} style={{ minWidth: 180, flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: col.color }} />
                  <span style={{ color: "rgba(255,255,255,0.6)", fontSize: 12, fontWeight: 700 }}>{col.label}</span>
                </div>
                {COLLAB_TASKS.filter(t => t.col === col.id).map(task => (
                  <div key={task.id} style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8, padding: "8px 10px", color: "rgba(255,255,255,0.75)", fontSize: 12, cursor: "grab" }}>
                    {task.text}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ─── Avatar View ──────────────────────────────────────────────────────────────
function AvatarView({ avatarSkin, setAvatarSkin, onEnter }: { avatarSkin: number; setAvatarSkin: (i: number) => void; onEnter: () => void }) {
  const [accentIdx, setAccentIdx] = useState(0);
  const accents = ["#00AEEF","#ec4899","#22c55e","#a855f7","#f59e0b","#ef4444"];

  return (
    <motion.div
      key="avatar"
      initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.35 }}
      style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg,#000510 0%,#000a1f 100%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24 }}
    >
      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, letterSpacing: "0.3em", fontWeight: 700 }}>AVATAR CUSTOMIZATION</div>
      {/* Preview */}
      <motion.div animate={{ scale: [1, 1.05, 1] }} transition={{ duration: 3, repeat: Infinity }}>
        <div style={{ width: 120, height: 120, borderRadius: "50%", background: `radial-gradient(circle at 35% 35%, ${AVATAR_SKINS[avatarSkin].color}, ${accents[accentIdx]}44)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 56, boxShadow: `0 0 40px ${AVATAR_SKINS[avatarSkin].color}66, 0 0 80px ${AVATAR_SKINS[avatarSkin].color}22`, border: `2px solid ${AVATAR_SKINS[avatarSkin].color}88` }}>
          {AVATAR_SKINS[avatarSkin].emoji}
        </div>
      </motion.div>
      {/* Skin grid */}
      <div>
        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, fontWeight: 700, letterSpacing: "0.15em", marginBottom: 10, textAlign: "center" }}>CHOOSE AVATAR</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
          {AVATAR_SKINS.map((skin, i) => (
            <button key={i} onClick={() => setAvatarSkin(i)} style={{ width: 56, height: 56, borderRadius: "50%", background: avatarSkin === i ? `${skin.color}22` : "rgba(255,255,255,0.06)", border: `2px solid ${avatarSkin === i ? skin.color : "rgba(255,255,255,0.1)"}`, fontSize: 24, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: avatarSkin === i ? `0 0 14px ${skin.color}55` : "none" }}>
              {skin.emoji}
            </button>
          ))}
        </div>
      </div>
      {/* Accent colors */}
      <div>
        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, fontWeight: 700, letterSpacing: "0.15em", marginBottom: 10, textAlign: "center" }}>ACCENT COLOR</div>
        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          {accents.map((c, i) => (
            <button key={c} onClick={() => setAccentIdx(i)} style={{ width: 24, height: 24, borderRadius: "50%", background: c, border: `3px solid ${accentIdx === i ? "white" : "transparent"}`, cursor: "pointer", padding: 0 }} />
          ))}
        </div>
      </div>
      <button onClick={onEnter} style={{ marginTop: 8, padding: "12px 36px", borderRadius: 40, background: "linear-gradient(135deg,#00AEEF,#7c3aed)", border: "none", color: "white", fontSize: 15, fontWeight: 700, cursor: "pointer", letterSpacing: "0.05em", boxShadow: "0 0 24px rgba(0,174,239,0.4)" }}>
        Enter World
      </button>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export function MetaverseHub({ onBack }: { onBack?: () => void }) {
  const [view, setView] = useState<View>("entry");
  const [activeZone, setActiveZone] = useState<string | null>(null);
  const [showNPC, setShowNPC] = useState(false);
  const [showCollab, setShowCollab] = useState(false);
  const [avatarSkin, setAvatarSkin] = useState(0);
  const [micOn, setMicOn] = useState(false);
  const [camOn, setCamOn] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [npcInput, setNpcInput] = useState("");

  const currentZone = ZONES.find(z => z.id === activeZone);
  const filteredZones = ZONES.filter(z =>
    z.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    z.desc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderZoneBody = useCallback(() => {
    if (!activeZone) return null;
    switch (activeZone) {
      case "plaza": return <ZonePlaza onCollab={() => setShowCollab(true)} />;
      case "studio": return <ZoneStudio />;
      case "coding": return <ZoneCoding />;
      case "gallery": return <ZoneGallery />;
      case "concert": return <ZoneConcert />;
      case "campus": return <ZoneCampus />;
      default: return <ZoneDefault zone={currentZone ?? ZONES[0]} />;
    }
  }, [activeZone, currentZone]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        fontFamily: "'Plus Jakarta Sans', sans-serif",
        color: "white",
      }}
    >
      <AnimatePresence mode="wait">
        {/* ── Entry ───────────────────────────────────────────────────── */}
        {view === "entry" && (
          <motion.div
            key="entry"
            initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.03 }}
            transition={{ duration: 0.45 }}
            style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg,#000510 0%,#000a1f 50%,#000510 100%)" }}
          >
            <ParticleField />
            <FloatingCity />

            {/* Holographic center */}
            <div className="relative z-10 flex flex-col items-center justify-center" style={{ minHeight: "100vh", gap: 20 }}>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <span style={{ fontFamily: "monospace", letterSpacing: "0.4em", color: "#00AEEF", fontSize: 11, fontWeight: 700 }}>🌐 CONNEXIONZ METAVERSE</span>
              </motion.div>

              <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", letterSpacing: "0.6em", fontWeight: 700, marginBottom: 4 }}>THE</div>
                <div style={{ fontSize: 72, fontWeight: 800, lineHeight: 1, letterSpacing: "-0.02em", textShadow: "0 0 40px rgba(0,174,239,0.6), 0 0 80px rgba(0,174,239,0.3)" }}>CREATOR</div>
                <div style={{ fontSize: 28, color: "#00AEEF", letterSpacing: "0.3em", fontWeight: 700, marginTop: 4 }}>UNIVERSE</div>
              </motion.div>

              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
                <p style={{ color: "rgba(255,255,255,0.45)", fontSize: 14, letterSpacing: "0.05em", textAlign: "center" }}>Step into a world where creativity has no limits</p>
              </motion.div>

              {/* Stats */}
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.65 }} style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
                {[
                  { val: "847K", label: "Creators Online" },
                  { val: "312", label: "Active Zones" },
                  { val: "2.4M", label: "Daily Sessions" },
                ].map(s => (
                  <div key={s.val} style={{ padding: "6px 14px", borderRadius: 20, background: "rgba(0,174,239,0.08)", border: "1px solid rgba(0,174,239,0.25)", display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: "#00AEEF", fontWeight: 800, fontSize: 15 }}>{s.val}</span>
                    <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 12 }}>{s.label}</span>
                  </div>
                ))}
              </motion.div>

              {/* Enter button */}
              <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.8 }}>
                <motion.div animate={{ boxShadow: ["0 0 20px rgba(0,174,239,0.3)", "0 0 45px rgba(0,174,239,0.7)", "0 0 20px rgba(0,174,239,0.3)"] }} transition={{ duration: 2.5, repeat: Infinity }} style={{ borderRadius: 50 }}>
                  <button
                    onClick={() => setView("avatar")}
                    style={{ padding: "14px 42px", borderRadius: 50, background: "linear-gradient(135deg,#00AEEF,#7c3aed)", border: "none", color: "white", fontSize: 15, fontWeight: 800, cursor: "pointer", letterSpacing: "0.1em" }}
                  >
                    ENTER THE METAVERSE
                  </button>
                </motion.div>
              </motion.div>

              {onBack && (
                <button onClick={onBack} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.3)", cursor: "pointer", fontSize: 13, marginTop: 8 }}>← Back</button>
              )}
            </div>

            {/* Bottom HUD */}
            <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "10px 20px", borderTop: "1px solid rgba(0,174,239,0.1)", background: "rgba(0,5,16,0.8)", backdropFilter: "blur(12px)", display: "flex", gap: 20, alignItems: "center", fontSize: 11 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e" }} />
                <span style={{ color: "rgba(255,255,255,0.5)" }}>Connected · 12ms</span>
              </div>
              <span style={{ color: "rgba(255,255,255,0.3)" }}>312 zones active</span>
              <span style={{ color: "rgba(255,255,255,0.3)" }}>847,291 users online</span>
              <span style={{ color: "rgba(255,255,255,0.2)", marginLeft: "auto" }}>v2.4.1-beta</span>
            </div>
          </motion.div>
        )}

        {/* ── Avatar ──────────────────────────────────────────────────── */}
        {view === "avatar" && (
          <AvatarView
            key="avatar"
            avatarSkin={avatarSkin}
            setAvatarSkin={setAvatarSkin}
            onEnter={() => setView("hub")}
          />
        )}

        {/* ── Hub ─────────────────────────────────────────────────────── */}
        {view === "hub" && (
          <motion.div
            key="hub"
            initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.35 }}
            style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg,#000a1f 0%,#000510 100%)", display: "flex", flexDirection: "column", overflow: "hidden" }}
          >
            {/* Floating creator dots */}
            {[
              { top: "20%", left: "12%" }, { top: "35%", left: "68%" }, { top: "55%", left: "25%" },
              { top: "70%", left: "80%" }, { top: "15%", left: "45%" }, { top: "80%", left: "50%" },
              { top: "42%", left: "90%" }, { top: "62%", left: "5%" },
            ].map((pos, i) => (
              <motion.div key={i} style={{ position: "absolute", ...pos, zIndex: 0, pointerEvents: "none" }}
                animate={{ y: [0, -8, 0], opacity: [0.4, 0.8, 0.4] }} transition={{ duration: 3 + i * 0.4, repeat: Infinity, delay: i * 0.3 }}>
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: `radial-gradient(circle, ${AVATAR_SKINS[i % 8].color}44, transparent)`, border: `1px solid ${AVATAR_SKINS[i % 8].color}55`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>
                  {AVATAR_SKINS[i % 8].emoji}
                </div>
              </motion.div>
            ))}

            {/* Top HUD */}
            <div style={{ position: "relative", zIndex: 10, padding: "12px 16px", borderBottom: "1px solid rgba(0,174,239,0.12)", background: "rgba(4,10,28,0.85)", backdropFilter: "blur(20px)", display: "flex", alignItems: "center", gap: 12 }}>
              <button onClick={() => setView("entry")} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.5)", cursor: "pointer", display: "flex", alignItems: "center" }}>
                <ArrowLeft size={18} />
              </button>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg,#00AEEF,#7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🌐</div>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14, letterSpacing: "0.05em" }}>METAVERSE HUB</span>

              <div style={{ flex: 1, maxWidth: 340, marginLeft: 12 }}>
                <div style={{ position: "relative" }}>
                  <Search size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "rgba(255,255,255,0.3)" }} />
                  <input
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search zones, creators, events…"
                    style={{ width: "100%", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(0,174,239,0.2)", borderRadius: 8, padding: "7px 10px 7px 30px", color: "white", fontSize: 12, outline: "none", boxSizing: "border-box" }}
                  />
                </div>
              </div>

              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
                <button onClick={() => setMicOn(m => !m)} style={{ background: micOn ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${micOn ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 8, padding: "6px 8px", cursor: "pointer", color: micOn ? "#00AEEF" : "rgba(255,255,255,0.5)", display: "flex" }}>
                  {micOn ? <Mic size={14} /> : <MicOff size={14} />}
                </button>
                <button onClick={() => setCamOn(c => !c)} style={{ background: camOn ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${camOn ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 8, padding: "6px 8px", cursor: "pointer", color: camOn ? "#00AEEF" : "rgba(255,255,255,0.5)", display: "flex" }}>
                  {camOn ? <Video size={14} /> : <VideoOff size={14} />}
                </button>
                <button onClick={() => setShowNPC(n => !n)} style={{ background: showNPC ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${showNPC ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 8, padding: "6px 10px", cursor: "pointer", color: showNPC ? "#00AEEF" : "rgba(255,255,255,0.5)", display: "flex", alignItems: "center", gap: 5, fontSize: 12 }}>
                  <Bot size={14} /> ARIA
                </button>
                <div style={{ width: 34, height: 34, borderRadius: "50%", background: `radial-gradient(circle, ${AVATAR_SKINS[avatarSkin].color}, #000a1f)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, border: `2px solid ${AVATAR_SKINS[avatarSkin].color}88`, cursor: "pointer" }}>
                  {AVATAR_SKINS[avatarSkin].emoji}
                </div>
              </div>
            </div>

            {/* Zone grid */}
            <div style={{ flex: 1, overflowY: "auto", padding: 16, position: "relative", zIndex: 1 }}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(220px,1fr))", gap: 12 }}>
                {filteredZones.map(zone => (
                  <motion.div
                    key={zone.id}
                    whileHover={{ scale: 1.04, y: -4 }}
                    onClick={() => { setActiveZone(zone.id); setView("zone"); }}
                    style={{
                      background: "rgba(8,16,40,0.75)",
                      backdropFilter: "blur(20px)",
                      border: `1px solid ${zone.color}25`,
                      borderRadius: 12,
                      overflow: "hidden",
                      cursor: "pointer",
                      position: "relative",
                    }}
                  >
                    <div style={{ height: 3, background: zone.color, opacity: 0.85 }} />
                    <div style={{ padding: "12px 14px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                        <div style={{ width: 36, height: 36, borderRadius: "50%", background: `${zone.color}22`, border: `1px solid ${zone.color}44`, display: "flex", alignItems: "center", justifyContent: "center", color: zone.color }}>
                          {zone.icon}
                        </div>
                        <span style={{ fontSize: 18 }}>{zone.emoji}</span>
                      </div>
                      <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 3 }}>{zone.name}</div>
                      <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 12, marginBottom: 10 }}>{zone.desc}</div>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e" }} />
                          <span style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>{zone.online.toLocaleString()} online</span>
                        </div>
                        <span style={{ color: zone.color, fontSize: 11, fontWeight: 700 }}>ENTER →</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Ticker */}
            <div style={{ borderTop: "1px solid rgba(0,174,239,0.1)", background: "rgba(4,10,28,0.9)", padding: "7px 0", overflow: "hidden", position: "relative", zIndex: 10 }}>
              <motion.div
                animate={{ x: [0, -2000] }}
                transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                style={{ whiteSpace: "nowrap", color: "rgba(255,255,255,0.4)", fontSize: 11, fontFamily: "monospace" }}
              >
                {TICKER_TEXT.repeat(4)}
              </motion.div>
            </div>

            {/* NPC Panel */}
            <AnimatePresence>{showNPC && <NPCPanel onClose={() => setShowNPC(false)} />}</AnimatePresence>
          </motion.div>
        )}

        {/* ── Zone ────────────────────────────────────────────────────── */}
        {view === "zone" && currentZone && (
          <motion.div
            key={`zone-${activeZone}`}
            initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.3 }}
            style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", overflow: "hidden", background: ZONE_BG[activeZone ?? "default"] ?? ZONE_BG.default }}
          >
            {/* Zone header */}
            <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", borderBottom: "1px solid rgba(0,174,239,0.1)", background: "rgba(4,10,28,0.7)", backdropFilter: "blur(20px)", flexShrink: 0 }}>
              <button onClick={() => setView("hub")} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.5)", cursor: "pointer", display: "flex" }}>
                <ArrowLeft size={18} />
              </button>
              <span style={{ fontSize: 20 }}>{currentZone.emoji}</span>
              <h1 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>{currentZone.name}</h1>
              <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e" }} />
                <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>{currentZone.online.toLocaleString()} online</span>
              </div>
              <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                <button onClick={() => setMicOn(m => !m)} style={{ background: micOn ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${micOn ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 7, padding: "5px 8px", cursor: "pointer", color: micOn ? "#00AEEF" : "rgba(255,255,255,0.4)", display: "flex" }}>
                  {micOn ? <Mic size={14} /> : <MicOff size={14} />}
                </button>
                <button onClick={() => setCamOn(c => !c)} style={{ background: camOn ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${camOn ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 7, padding: "5px 8px", cursor: "pointer", color: camOn ? "#00AEEF" : "rgba(255,255,255,0.4)", display: "flex" }}>
                  {camOn ? <Video size={14} /> : <VideoOff size={14} />}
                </button>
                <button onClick={() => setShowCollab(c => !c)} style={{ background: showCollab ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${showCollab ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 7, padding: "5px 10px", cursor: "pointer", color: showCollab ? "#00AEEF" : "rgba(255,255,255,0.4)", fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
                  <Share2 size={13} /> Collab
                </button>
                <button onClick={() => setShowNPC(n => !n)} style={{ background: showNPC ? "rgba(0,174,239,0.2)" : "rgba(255,255,255,0.06)", border: `1px solid ${showNPC ? "#00AEEF" : "rgba(255,255,255,0.1)"}`, borderRadius: 7, padding: "5px 10px", cursor: "pointer", color: showNPC ? "#00AEEF" : "rgba(255,255,255,0.4)", fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
                  <Bot size={13} /> ARIA
                </button>
              </div>
            </div>

            {/* Zone body */}
            <div style={{ flex: 1, display: "flex", overflow: "hidden", position: "relative" }}>
              {renderZoneBody()}
              <AnimatePresence>{showNPC && <NPCPanel onClose={() => setShowNPC(false)} />}</AnimatePresence>
              <AnimatePresence>{showCollab && <CollabPanel onClose={() => setShowCollab(false)} />}</AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
