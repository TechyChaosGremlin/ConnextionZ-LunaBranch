import { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { 
  ArrowLeft, Phone, Video, 
  MoreHorizontal, Smile, Send 
} from "lucide-react";
import { useTheme } from "../ThemeContext";
import { uid } from "../seed/data";
import type { Conversation, DM } from "../seed/types";

interface DMThreadProps {
  convo: Conversation;
  onBack: () => void;
}

export function DMThread({ convo, onBack }: DMThreadProps) {
  const isDark          = useTheme();
  const [msgs, setMsgs] = useState<DM[]>(convo.messages);
  const [text, setText] = useState("");
  const bottomRef       = useRef<HTMLDivElement | null>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView(); }, [msgs]);

  const send = () => {
    const t = text.trim();
    if (!t) return;
    setMsgs((prev) => [...prev, { 
      id: uid(), 
      from: "me", 
      text: t, 
      time: "Just now", 
      read: false 
    }]);
    setText("");
  };

  const D = {
    bg:             isDark ? "linear-gradient(160deg,#00071a,#000c22)" : "linear-gradient(160deg,#f2f5fb,#eaf1fc)",
    headerBorder:   isDark ? "rgba(0,174,239,0.12)" : "rgba(0,0,0,0.08)",
    btnBg:          isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.05)",
    iconColor:      isDark ? "rgba(255,255,255,0.6)" : "rgba(10,14,26,0.5)",
    arrowColor:     isDark ? "#fff" : "#0a0e1a",
    username:       isDark ? "#fff" : "#0a0e1a",
    offlineColor:   isDark ? "rgba(255,255,255,0.35)" : "rgba(10,14,26,0.35)",
    themBubble:     isDark ? "rgba(255,255,255,0.09)" : "rgba(0,0,0,0.07)",
    themText:       isDark ? "#fff" : "#0a0e1a",
    timeColor:      isDark ? "rgba(255,255,255,0.3)" : "rgba(10,14,26,0.35)",
    inputBg:        isDark ? "rgba(0,60,140,0.3)" : "rgba(0,0,0,0.05)",
    inputBorder:    isDark ? "1px solid rgba(0,174,239,0.2)" : "1px solid rgba(0,0,0,0.08)",
    inputText:      isDark ? "#fff" : "#0a0e1a",
    inputBorderTop: isDark ? "rgba(0,174,239,0.1)" : "rgba(0,0,0,0.07)",
    smileColor:     isDark ? "rgba(255,255,255,0.35)" : "rgba(10,14,26,0.35)",
  };

  return (
    <motion.div
      initial=   {{ x: "100%"                                   }} 
      animate=   {{ x: 0                                        }} 
      exit=      {{ x: "100%"                                   }}
      transition={{ type: "spring", damping: 32, stiffness: 300 }}
      className="absolute inset-0 z-30 flex flex-col"
      style={{ background: D.bg }}
    >
      <div className="flex items-center gap-3 px-4 pt-12 pb-4" style={{ borderBottom: `1px solid ${D.headerBorder}` }}>
        <button onClick={onBack} className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: D.btnBg }}>
          <ArrowLeft className="w-4 h-4" style={{ color: D.arrowColor }} />
        </button>
        <div className="relative flex-shrink-0">
          <img src={convo.avatar} alt={convo.username} className="w-9 h-9 rounded-full object-cover" />
          {convo.online && <div className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-green-400 border-2" style={{ borderColor: isDark ? "#000" : "#f2f5fb" }} />}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-[14px]" style={{ color: D.username }}>@{convo.username}</p>
          <p className="text-[11px]" style={{ color: convo.online ? "#4ade80" : D.offlineColor }}>
            {convo.online ? "Active now" : "Offline"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {[Phone, Video, MoreHorizontal].map((Icon, i) => (
            <button key={i} className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: D.btnBg }}>
              <Icon className="w-3.5 h-3.5" style={{ color: D.iconColor }} />
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ scrollbarWidth: "none" }}>
        {msgs.map((m, i) => {
          const isMe = m.from === "me";
          const showAvatar = !isMe && (i === 0 || msgs[i - 1].from !== "them");
          return (
            <div key={m.id} className={`flex items-end gap-2 ${isMe ? "justify-end" : "justify-start"}`}>
              {!isMe && (
                <div className="w-6 flex-shrink-0">
                  {showAvatar && <img src={convo.avatar} alt="" className="w-6 h-6 rounded-full object-cover" />}
                </div>
              )}
              <div className="max-w-[72%] space-y-0.5">
                <div className={`px-3.5 py-2.5 rounded-2xl text-[14px] leading-snug ${isMe ? "rounded-br-sm" : "rounded-bl-sm"}`}
                  style={{ background: isMe ? "linear-gradient(135deg,#00AEEF,#0077cc)" : D.themBubble, color: isMe ? "#fff" : D.themText }}>
                  {m.text}
                </div>
                <p className={`text-[10px] px-1 ${isMe ? "text-right" : "text-left"}`} style={{ color: D.timeColor }}>
                  {m.time}{isMe && m.read && " · Read"}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <div className="flex items-center gap-2 px-4 pb-8 pt-2" style={{ borderTop: `1px solid ${D.inputBorderTop}` }}>
        <button style={{ color: D.smileColor }} className="flex-shrink-0"><Smile className="w-5 h-5" /></button>
        <div className="flex-1 flex items-center gap-2 rounded-full px-4 py-2.5" style={{ background: D.inputBg, border: D.inputBorder }}>
          <input value={text} onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") send(); }}
            placeholder="Message…"
            className="flex-1 bg-transparent text-[14px] outline-none"
            style={{ color: D.inputText }} />
        </div>
        <motion.button whileTap={{ scale: 0.88 }} onClick={send} style={{ opacity: text.trim() ? 1 : 0.35 }}>
          <Send className="w-5 h-5" style={{ color: "#00AEEF" }} />
        </motion.button>
      </div>
    </motion.div>
  );
}
