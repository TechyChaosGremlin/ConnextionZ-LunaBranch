import { useState, useEffect, useRef } from "react";
import { VideoPlayer } from "./VideoPlayer";

interface Video {
  id:          string;
  username:    string;
  description: string;
  likes:       number;
  comments:    number;
  shares:      number;
  thumbnail:   string;
  videoUrl:    string;
}

// Curated video URLs (YouTube embeds), each matched to a creator's activity.
// Videos play automatically on loop while the user is scrolled to them.
const PEXELS_VIDEOS: string[] = [
  // Male DJ
  "https://www.youtube.com/embed/kLdaIxDM-_Y",
  // Male DJ
  "https://www.youtube.com/embed/VUd0wYVfh9s",
  // Female DJ
  "https://www.youtube.com/embed/nQ4H5WUpKyA",
  // Female DJ
  "https://www.youtube.com/embed/lsduGj42ZJA",
  // Female rock
  "https://www.youtube.com/embed/SQNtGoM3FVU",
  // Female rock
  "https://www.youtube.com/embed/ryT512TA4nA",
  // Male hip hop
  "https://www.youtube.com/embed/28hYUZMufDg",
  // Female country
  "https://www.youtube.com/embed/lGvEG2LnP0k",
  // Cinematography
  "https://www.youtube.com/embed/xBasQG_6p40",
  // Male Photography
  "https://www.youtube.com/embed/TbixociDmPY",
];

// Mock video data
const generateMockVideos = (startIndex: number, count: number): Video[] => {
  const videos: Video[] = [];
  for (let i = 0; i < count; i++) {
    const index = startIndex + i;
    videos.push({
      id: `video-${index}`,
      username: `user${index % 20 + 1}`,
      description: [
        "Just vibing 🎵 #ForYou",
        "This took me 5 hours to make! 🎨",
        "Watch till the end! 😱 #Trending",
        "Day ${index} of learning this dance 💃",
        "POV: You're scrolling at 3am 🌙",
        "Rate this fit 1-10 👗",
        "Things nobody talks about... 🤔",
        "Life hack you need to try! 💡",
      ][index % 8],
      likes: Math.floor(Math.random() * 1000000),
      comments: Math.floor(Math.random() * 50000),
      shares: Math.floor(Math.random() * 10000),
      thumbnail: `https://picsum.photos/seed/${index}/1080/1920`,
      // Assign a Pexels video that best matches this user's activity
      videoUrl: PEXELS_VIDEOS[index % PEXELS_VIDEOS.length],
    });
  }
  return videos;
};

export function VideoFeed() {
  const [videos, setVideos]                       = useState<Video[]>(() => generateMockVideos(0, 10));
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isLoading, setIsLoading]                 = useState(false);
  const containerRef                              = useRef<HTMLDivElement>(null);
  const touchStartY                               = useRef<number>(0);
  const isScrolling                               = useRef(false);

  // Load more videos when approaching the end
  useEffect(() => {
    if (currentVideoIndex >= videos.length - 3 && !isLoading) {
      setIsLoading(true);
      setTimeout(() => {
        setVideos((prev) => [...prev, ...generateMockVideos(prev.length, 5)]);
        setIsLoading(false);
      }, 500);
    }
  }, [currentVideoIndex, videos.length, isLoading]);

  const scrollToVideo = (index: number) => {
    if (index >= 0 && index < videos.length) {
      setCurrentVideoIndex(index);
      const container = containerRef.current;
      if (container) {
        container.scrollTo({
          top: index * window.innerHeight,
          behavior: "smooth",
        });
      }
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (isScrolling.current) return;
    
    isScrolling.current = true;
    if (e.deltaY > 0) {
      scrollToVideo(currentVideoIndex + 1);
    } else {
      scrollToVideo(currentVideoIndex - 1);
    }
    
    setTimeout(() => {
      isScrolling.current = false;
    }, 800);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (isScrolling.current) return;
    
    const touchEndY = e.changedTouches[0].clientY;
    const diff = touchStartY.current - touchEndY;
    
    if (Math.abs(diff) > 50) {
      isScrolling.current = true;
      if (diff > 0) {
        scrollToVideo(currentVideoIndex + 1);
      } else {
        scrollToVideo(currentVideoIndex - 1);
      }
      
      setTimeout(() => {
        isScrolling.current = false;
      }, 800);
    }
  };

  return (
    <div
      ref={containerRef}
      className="h-screen w-full overflow-hidden snap-y snap-mandatory"
      onWheel={handleWheel}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {videos.map((video, index) => (
        <div key={video.id} className="h-screen w-full snap-start snap-always">
          <VideoPlayer
            video={video}
            isActive={index === currentVideoIndex}
          />
        </div>
      ))}
    </div>
  );
}
