import { useState, useCallback, useRef, useEffect } from "react";
import { Heart, MessageCircle, Share2, Play } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface Video {
  id: string;
  username: string;
  description: string;
  likes: number;
  comments: number;
  shares: number;
  thumbnail: string;
  videoUrl: string;
}

interface VideoPlayerProps {
  video: Video;
  isActive: boolean;
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
};

const SHARDS = Array.from({ length: 20 }, (_, i) => {
  const angle = (i / 20) * Math.PI * 2 + (i % 3) * 0.3;
  const dist = 55 + (i % 4) * 22;
  const width = 5 + (i % 5) * 4;
  const height = 4 + (i % 3) * 3;
  return {
    id: i,
    tx: Math.cos(angle) * dist,
    ty: Math.sin(angle) * dist,
    rotate: (i * 73) % 360,
    width,
    height,
    delay: i * 0.018,
    // slightly different blue shades
    blue: ["#3b82f6", "#60a5fa", "#93c5fd", "#2563eb", "#1d4ed8"][i % 5],
  };
});

// ─── YouTube IFrame API loader ───────────────────────────────────────────────
// Ensures the YT API script is loaded exactly once, then runs the callback
// (creating a player) as soon as the API is ready — even if it was already
// loaded by a previous mount.
let ytApiPromise: Promise<void> | null = null;

function ensureYouTubeApiReady(callback: () => void): void {
  if ((window as any).YT && (window as any).YT.Player) {
    callback();
    return;
  }

  if (!ytApiPromise) {
    ytApiPromise = new Promise<void>((resolve) => {
      (window as any).onYouTubeIframeAPIReady = () => {
        resolve();
      };
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    });
  }

  ytApiPromise.then(() => callback());
}

function CollabButton({ onCollab }: { onCollab: () => void }) {
  const [phase, setPhase] = useState<"idle" | "exploding" | "gone" | "reappearing">("idle");

  const handleClick = useCallback(() => {
    if (phase !== "idle") return;
    setPhase("exploding");
    setTimeout(() => onCollab(), 120);
    setTimeout(() => setPhase("gone"), 380);
    setTimeout(() => setPhase("reappearing"), 900);
    setTimeout(() => setPhase("idle"), 1400);
  }, [phase, onCollab]);

  const isExploding = phase === "exploding";
  const isGone = phase === "gone";
  const isReappearing = phase === "reappearing";
  const showCircle = phase === "idle" || phase === "exploding";

  return (
    <button
      onClick={handleClick}
      className="flex flex-col items-center gap-1 relative"
      style={{ minWidth: 52 }}
    >
      {/* Shards */}
      <div
        className="absolute pointer-events-none"
        style={{ width: 48, height: 48, top: 0, left: "50%", transform: "translateX(-50%)" }}
      >
        {SHARDS.map((s) => (
          <motion.div
            key={s.id}
            initial={{ x: 0, y: 0, rotate: 0, opacity: 0, scale: 0 }}
            animate={
              isExploding
                ? {
                    x: s.tx,
                    y: s.ty,
                    rotate: s.rotate,
                    opacity: [0, 1, 1, 0],
                    scale: [0.4, 1.1, 0.8, 0],
                  }
                : { x: 0, y: 0, rotate: 0, opacity: 0, scale: 0 }
            }
            transition={{
              duration: 0.55,
              delay: s.delay,
              ease: [0.1, 0.8, 0.3, 1],
            }}
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: s.width,
              height: s.height,
              marginTop: -s.height / 2,
              marginLeft: -s.width / 2,
              borderRadius: 2,
              backgroundColor: s.blue,
              boxShadow: `0 0 6px 1px ${s.blue}`,
            }}
          />
        ))}

        {/* Shockwave ring */}
        <AnimatePresence>
          {isExploding && (
            <motion.div
              key="ring"
              initial={{ scale: 0.3, opacity: 0.9 }}
              animate={{ scale: 3.5, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.45, ease: "easeOut" }}
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "50%",
                border: "2.5px solid #60a5fa",
                boxShadow: "0 0 12px 4px #3b82f6",
              }}
            />
          )}
        </AnimatePresence>
      </div>

      {/* Main circle */}
      <AnimatePresence mode="wait">
        {showCircle && (
          <motion.div
            key="circle"
            initial={false}
            animate={
              isExploding
                ? { scale: [1, 1.35, 0], opacity: [1, 1, 0], filter: ["blur(0px)", "blur(0px)", "blur(6px)"] }
                : { scale: [1, 1.06, 1], opacity: 1, filter: "blur(0px)" }
            }
            transition={
              isExploding
                ? { duration: 0.28, ease: "easeIn" }
                : { duration: 2, repeat: Infinity, ease: "easeInOut" }
            }
            className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center"
            style={{ boxShadow: "0 4px 20px rgba(59,130,246,0.5)" }}
          >
            <span className="text-white font-bold text-xl leading-none select-none">C</span>
          </motion.div>
        )}

        {isReappearing && (
          <motion.div
            key="reappear"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: [0, 1.25, 1], opacity: 1 }}
            transition={{ duration: 0.45, ease: [0.17, 0.89, 0.32, 1.28] }}
            className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center"
            style={{ boxShadow: "0 4px 20px rgba(59,130,246,0.5)" }}
          >
            <span className="text-white font-bold text-xl leading-none select-none">C</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Placeholder so layout doesn't collapse while gone */}
      {isGone && <div className="w-12 h-12" />}

      <span className="text-white text-xs font-semibold">Collab</span>
    </button>
  );
}

export function VideoPlayer({ video, isActive }: VideoPlayerProps) {
  const [isLiked, setIsLiked] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [showCollabDialog, setShowCollabDialog] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<any>(null);
  const isActiveRef = useRef(isActive);
  const videoId = video.videoUrl.split("/").pop();

  // Keep latest isActive available inside callbacks
  useEffect(() => {
    isActiveRef.current = isActive;
  }, [isActive]);

  // Create the player for this video once the YouTube API is ready
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const createPlayer = () => {
      playerRef.current = new (window as any).YT.Player(container, {
        videoId,
        playerVars: {
          autoplay: isActiveRef.current ? 1 : 0,
          loop: 1,
          playlist: videoId,
          mute: 1,
          playsinline: 1,
          controls: 0,
          rel: 0,
        },
        events: {
          onReady: () => {
            if (isActiveRef.current) {
              playerRef.current?.playVideo();
              setIsPlaying(true);
            }
          },
        },
      });
    };

    ensureYouTubeApiReady(createPlayer);

    return () => {
      playerRef.current?.destroy();
      playerRef.current = null;
    };
  }, [videoId]);

  // Play automatically on loop while scrolled to; pause when scrolled away
  useEffect(() => {
    const player = playerRef.current;
    if (!player || typeof player.playVideo !== "function") return;
    if (isActive) {
      player.playVideo();
      setIsPlaying(true);
    } else {
      player.pauseVideo();
      setIsPlaying(false);
    }
  }, [isActive]);

  const handleLike = () => setIsLiked(!isLiked);

  const handleCollab = useCallback(() => {
    setShowCollabDialog(true);
    setTimeout(() => setShowCollabDialog(false), 2000);
  }, []);

  const togglePlay = () => {
    const player = playerRef.current;
    if (!player || typeof player.playVideo !== "function") return;
    if (isPlaying) {
      player.pauseVideo();
      setIsPlaying(false);
    } else {
      player.playVideo();
      setIsPlaying(true);
    }
  };

  return (
    <div className="relative h-full w-full bg-black flex items-center justify-center">
      {/* Thumbnail poster (behind the video) */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-30"
        style={{ backgroundImage: `url(${video.thumbnail})` }}
      />
      {/* Video player (on top of thumbnail) */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
      {/* Play/pause overlay (on top of video) */}
      <div className="absolute inset-0" onClick={togglePlay}>
        <AnimatePresence>
          {!isPlaying && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="absolute inset-0 flex items-center justify-center bg-black/30"
            >
              <div className="bg-white/20 backdrop-blur-sm rounded-full p-6">
                <Play className="size-16 text-white fill-white" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/80 via-black/40 to-transparent pointer-events-none" />

      <div className="absolute right-4 bottom-24 flex flex-col gap-6 z-10">
        {/* Profile */}
        <div className="flex flex-col items-center">
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center text-white font-semibold">
              {video.username[0].toUpperCase()}
            </div>
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
              +
            </div>
          </div>
        </div>

        {/* Like */}
        <motion.button whileTap={{ scale: 0.9 }} onClick={handleLike} className="flex flex-col items-center gap-1">
          <motion.div animate={isLiked ? { scale: [1, 1.2, 1] } : {}} transition={{ duration: 0.3 }}>
            <Heart className={`size-8 ${isLiked ? "fill-red-500 text-red-500" : "text-white"}`} />
          </motion.div>
          <span className="text-white text-xs font-semibold">{formatNumber(video.likes + (isLiked ? 1 : 0))}</span>
        </motion.button>

        {/* Comment */}
        <motion.button whileTap={{ scale: 0.9 }} className="flex flex-col items-center gap-1">
          <MessageCircle className="size-8 text-white" />
          <span className="text-white text-xs font-semibold">{formatNumber(video.comments)}</span>
        </motion.button>

        {/* Collab */}
        <CollabButton onCollab={handleCollab} />

        {/* Share */}
        <motion.button whileTap={{ scale: 0.9 }} className="flex flex-col items-center gap-1">
          <Share2 className="size-8 text-white" />
          <span className="text-white text-xs font-semibold">{formatNumber(video.shares)}</span>
        </motion.button>
      </div>

      <div className="absolute bottom-6 left-4 right-20 z-10">
        <div className="space-y-2">
          <h3 className="text-white font-semibold text-lg">@{video.username}</h3>
          <p className="text-white text-sm">{video.description}</p>
        </div>
      </div>

      <AnimatePresence>
        {showCollabDialog && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl p-6 shadow-2xl z-50 max-w-sm mx-4"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm leading-none">C</span>
              </div>
              <h4 className="font-bold text-lg">Collab Request</h4>
            </div>
            <p className="text-gray-600 text-sm">
              Want to collaborate with @{video.username}? This feature will let you create duets and joint content!
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
