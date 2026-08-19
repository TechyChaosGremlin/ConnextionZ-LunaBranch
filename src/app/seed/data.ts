import type { CollabRequest, Conversation } from "./types";

export const fmt = (n: number) => (n >= 1000 ? (n / 1000).toFixed(1) + "K" : String(n));
export const uid = () => Math.random().toString(36).slice(2);

export const SEED_REQUESTS: CollabRequest[] = [
  {
    id: "r1", username: "nova.dj", verified: true, collabScore: 4.8,
    avatar: "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=80&h=80&fit=crop&auto=format",
    mutualCollabs: 3, category: "Music", categoryIcon: "🎵",
    message: "Hey! Huge fan of your production style. I'd love to create a track together — I'm thinking something in the 130bpm electronic space. I have full studio access and can handle mixing/mastering. Let's make something the feed hasn't heard before 🔊",
    budget: "$2K–$5K", timeline: "1 month", isRemote: true, timeSent: "2m ago",
    accent: "#00AEEF",
  },
  {
    id: "r2", username: "zara.creates", verified: true, collabScore: 4.9,
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&h=80&fit=crop&auto=format",
    mutualCollabs: 7, category: "Brand Deal", categoryIcon: "💼",
    message: "A skincare brand I work with is looking for a tech/creator crossover campaign. Your audience would be a perfect fit. They're offering a flat fee + commission. Happy to jump on a call to share more details — the brief is super flexible.",
    budget: "$10K+", timeline: "2 weeks", isRemote: false, timeSent: "15m ago",
    accent: "#f472b6",
  },
  {
    id: "r3", username: "milo.visuals", verified: false, collabScore: 4.7,
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&auto=format",
    mutualCollabs: 1, category: "Video", categoryIcon: "📹",
    message: "I'm shooting a short film series about creator culture and I want to feature you in episode 3. No script — just you doing your thing while I capture it. Could be a great piece for both our portfolios. I'll cover all travel costs.",
    budget: null, timeline: "3 months", isRemote: false, timeSent: "1h ago",
    accent: "#a78bfa",
  },
  {
    id: "r4", username: "ren.filmco", verified: false, collabScore: 4.6,
    avatar: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=80&h=80&fit=crop&auto=format",
    mutualCollabs: 0, category: "Podcast", categoryIcon: "🎙",
    message: "Starting a new podcast on creative entrepreneurship and would love you as my first guest. The show already has a waitlist of 2K+ subscribers. I think your story about building in public would resonate massively with the audience.",
    budget: "Open to discuss", timeline: "ASAP", isRemote: true, timeSent: "3h ago",
    accent: "#22c55e",
  },
  {
    id: "r5", username: "freq.faye", verified: true, collabScore: 4.3,
    avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&h=80&fit=crop&auto=format",
    mutualCollabs: 2, category: "Gaming", categoryIcon: "🎮",
    message: "Running a gaming creator event next month and want to create content together around it — think challenge videos, reaction content, the works. The event has brand sponsorship already sorted so all content costs are covered.",
    budget: "$500–$2K", timeline: "1 month", isRemote: false, timeSent: "5h ago",
    accent: "#f59e0b",
  },
];

export const SEED_CONVOS: Conversation[] = [
  {
    id: "c1", username: "nova.dj", online: true,
    avatar: "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=80&h=80&fit=crop&auto=format",
    lastMsg: "Sent you the stems 🎧", timestamp: "2m", unread: 2, hasCollabBadge: true,
    messages: [
      { id: "m1", from: "them", text: "Hey! Loved your last set. Would you be down to collab?", time: "Yesterday 9:41 PM" },
      { id: "m2", from: "me", text: "100%! What kind of track are you thinking?", time: "Yesterday 9:45 PM", read: true },
      { id: "m3", from: "them", text: "Something in the 128bpm space — I have a vocal sample that's 🔥", time: "Yesterday 10:02 PM" },
      { id: "m4", from: "me", text: "Send it over! I'm in the studio tomorrow", time: "Yesterday 10:05 PM", read: true },
      { id: "m5", from: "them", text: "Sent you the stems 🎧", time: "Just now" },
    ],
  },
  {
    id: "c2", username: "zara.creates", online: true,
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&h=80&fit=crop&auto=format",
    lastMsg: "The brand loved the concept!", timestamp: "15m", unread: 1, hasCollabBadge: true,
    messages: [
      { id: "m1", from: "them", text: "The brand just reviewed our pitch deck", time: "1h ago" },
      { id: "m2", from: "them", text: "The brand loved the concept!", time: "15m ago" },
    ],
  },
  {
    id: "c3", username: "milo.visuals", online: false,
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&auto=format",
    lastMsg: "You: Sounds great, let's do it", timestamp: "1h", unread: 0, hasCollabBadge: false,
    messages: [
      { id: "m1", from: "them", text: "Hey! Saw your collab score went up — congrats 🙌", time: "2h ago" },
      { id: "m2", from: "me", text: "Thanks! Been putting in the work haha", time: "1h 30m ago", read: true },
      { id: "m3", from: "them", text: "Would love to do a shoot together sometime", time: "1h 10m ago" },
      { id: "m4", from: "me", text: "Sounds great, let's do it", time: "1h ago", read: true },
    ],
  },
  {
    id: "c4", username: "beatsby.kai", online: false,
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&h=80&fit=crop&auto=format",
    lastMsg: "Check out this loop I made", timestamp: "3h", unread: 0, hasCollabBadge: false,
    messages: [
      { id: "m1", from: "them", text: "Check out this loop I made", time: "3h ago" },
    ],
  },
  {
    id: "c5", username: "drop.dani", online: true,
    avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&h=80&fit=crop&auto=format",
    lastMsg: "You: On it 🙏", timestamp: "Yesterday", unread: 0, hasCollabBadge: true,
    messages: [
      { id: "m1", from: "them", text: "Can you review the collab brief I sent?", time: "Yesterday" },
      { id: "m2", from: "me", text: "On it 🙏", time: "Yesterday", read: true },
    ],
  },
];
