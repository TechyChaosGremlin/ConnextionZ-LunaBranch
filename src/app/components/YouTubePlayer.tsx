import { useEffect, useRef } from "react";

interface YouTubePlayerProps {
  videoUrl: string;
  username: string;
  isActive: boolean;
  paused: boolean;
}

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
      (window as any).onYouTubeIframeAPIReady = () => resolve();
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    });
  }

  ytApiPromise.then(() => callback());
}

export function YouTubePlayer({ videoUrl, username, isActive, paused }: YouTubePlayerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<any>(null);
  const isActiveRef = useRef(isActive);
  const pausedRef = useRef(paused);
  const videoId = videoUrl.split("/").pop();

  // Keep latest props available inside callbacks
  useEffect(() => {
    isActiveRef.current = isActive;
  }, [isActive]);
  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  // Create the player once the YouTube API is ready
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const createPlayer = () => {
      playerRef.current = new (window as any).YT.Player(container, {
        videoId,
        playerVars: {
          autoplay: isActiveRef.current && !pausedRef.current ? 1 : 0,
          loop: 1,
          playlist: videoId,
          playsinline: 1,
          controls: 0,
          rel: 0,
        },
        events: {
          onReady: () => {
            if (isActiveRef.current && !pausedRef.current) {
              playerRef.current?.playVideo();
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

  // Play/pause based on active + paused state
  useEffect(() => {
    const player = playerRef.current;
    if (!player || typeof player.playVideo !== "function") return;
    if (isActive && !paused) {
      player.playVideo();
    } else {
      player.pauseVideo();
    }
  }, [isActive, paused]);

  return <div ref={containerRef} className="absolute inset-0 w-full h-full" />;
}
