import { useEffect } from "react";
import { motion } from "motion/react";

interface CelebrationOverlayProps {
  username: string;
  onDone: () => void;
}

export function CelebrationOverlay({ username, onDone }: CelebrationOverlayProps) {
  // Confetti-style particles
  const PARTICLES = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    x: 10 + Math.random() * 80,
    y: 20 + Math.random() * 60,
    color: ["#00AEEF", "#38bdf8", "#a78bfa", "#f472b6", "#f59e0b", "#22c55e"][i % 6],
    size: 6 + Math.random() * 10,
    delay: Math.random() * 0.4,
  }));

  useEffect(() => { const t = setTimeout(onDone, 2800); return () => clearTimeout(t); }, [onDone]);

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 flex flex-col items-center justify-center"
      style={{ background: "rgba(0,5,20,0.92)", backdropFilter: "blur(12px)" }}
    >
      {/* Particles */}
      {PARTICLES.map((p) => (
        <motion.div key={p.id}
          initial={{ x: `${p.x}vw`, y: "-5vh", opacity: 1, rotate: 0, scale: 1 }}
          animate={{ y: "110vh", opacity: 0, rotate: 720, scale: 0 }}
          transition={{ duration: 2 + Math.random(), delay: p.delay, ease: "easeIn" }}
          className="absolute rounded-sm"
          style={{ width: p.size, height: p.size, background: p.color, left: 0, top: 0 }}
        />
      ))}

      {/* Central celebration */}
      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", damping: 12, delay: 0.1 }}
        className="flex flex-col items-center gap-4 text-center px-8">
        <motion.div animate={{ rotate: [0, -10, 10, -10, 0] }} transition={{ delay: 0.3, duration: 0.5 }}
          className="text-6xl">🚀</motion.div>
        <div>
          <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
            className="text-white font-extrabold text-[26px] leading-tight">
            Your collaboration<br />is officially live!
          </motion.p>
          <motion.p initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            className="mt-2 text-[14px]" style={{ color: "#00AEEF" }}>
            with @{username}
          </motion.p>
        </div>
        {/* Pulse ring */}
        <motion.div animate={{ scale: [1, 2.5], opacity: [0.6, 0] }} transition={{ duration: 1.2, repeat: Infinity }}
          className="absolute w-24 h-24 rounded-full" style={{ border: "2px solid #00AEEF" }} />
      </motion.div>
    </motion.div>
  );
}
