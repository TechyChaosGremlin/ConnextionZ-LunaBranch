import { useEffect, useRef } from "react";

interface YouTubePlayerProps {
  videoUrl: string;
  username: string;
  isActive: boolean;
  paused:   boolean;
}

// ─── YouTube IFrame API loader ───────────────────────────────────────────────
let ytApiPromise: Promise<void> | null = null;

function ensureYouTubeApiReady(callback: () => void): void {
  if ((window as any).YT && (window as any).YT.Player) {
    callback();
    return;
  }

  if (!ytApiPromise) {
    ytApiPromise = new Promise<void>((resolve) => {
      (window as any).onYouTubeIframeAPIReady = () => resolve();
      const tag  = document.createElement("script");
      tag.src    = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    });
  }

  ytApiPromise.then(() => callback());
}

export function YouTubePlayer({ videoUrl, username, isActive, paused }: YouTubePlayerProps) {
  const containerRef     = useRef<HTMLDivElement | null>(null);
  const playerRef        = useRef<any>(null);
  const isActiveRef      = useRef(isActive);
  const pausedRef        = useRef(paused);
  const unmuteTimeoutRef = useRef<number | null>(null);
  
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
          autoplay:    isActiveRef.current && !pausedRef.current ? 1 : 0,
          mute:        1, // start muted to satisfy autoplay policy
          loop:        1,
          playlist:    videoId,
          playsinline: 1,
          controls:    0,
          rel:         0,
        },
        events: {
          onReady: () => {
            console.log("Player ready, isActive:", isActiveRef.current, "paused:", pausedRef.current);
            // Attempt to play after a short delay to ensure the player is fully ready
            setTimeout(() => {
              if (isActiveRef.current && !pausedRef.current) {
                playerRef.current?.playVideo();
                // Schedule unmute after 1 second of playback
                unmuteTimeoutRef.current = window.setTimeout(() => {
                  if (isActiveRef.current && !pausedRef.current) {
                    playerRef.current?.unMute();
                  }
                }, 1000);
              }
            }, 100);
          },
          onStateChange: (event: any) => {
            // If the player is not playing and we expect it to, retry
            if (event.data === -1 && isActiveRef.current && !pausedRef.current) {
              playerRef.current?.playVideo();
            }
          },
        },
      });
    };

    ensureYouTubeApiReady(createPlayer);

    return () => {
      if (unmuteTimeoutRef.current) {
        clearTimeout(unmuteTimeoutRef.current);
        unmuteTimeoutRef.current = null;
      }
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
      // If we're starting playback, schedule unmute after 1 second
      if (unmuteTimeoutRef.current) clearTimeout(unmuteTimeoutRef.current);
      unmuteTimeoutRef.current = window.setTimeout(() => {
        if (isActiveRef.current && !pausedRef.current) {
          player.unMute();
        }
      }, 1000);
    } else {
      player.pauseVideo();
      // Clear any pending unmute
      if (unmuteTimeoutRef.current) {
        clearTimeout(unmuteTimeoutRef.current);
        unmuteTimeoutRef.current = null;
      }
    }
  }, [isActive, paused]);

  return (
    <div
      className="relative w-full h-full"
      onClick={(e) => {
        e.stopPropagation(); // prevent parent from toggling paused
        playerRef.current?.playVideo(); // force play
        // If user clicks, unmute immediately
        playerRef.current?.unMute();
        // Clear any pending unmute timeout
        if (unmuteTimeoutRef.current) {
          clearTimeout(unmuteTimeoutRef.current);
          unmuteTimeoutRef.current = null;
        }
      }}
    >
      {/* Video container */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
}