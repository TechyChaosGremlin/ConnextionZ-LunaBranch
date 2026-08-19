export interface CollabRequest {
  id: string;
  username: string;
  avatar: string;
  verified: boolean;
  collabScore: number;
  mutualCollabs: number;
  category: string;
  categoryIcon: string;
  message: string;
  budget: string | null;
  timeline: string;
  isRemote: boolean;
  timeSent: string;
  accent: string;
}

export interface Conversation {
  id: string;
  username: string;
  avatar: string;
  online: boolean;
  lastMsg: string;
  timestamp: string;
  unread: number;
  hasCollabBadge: boolean;
  messages: DM[];
}

export interface DM {
  id: string;
  from: "them" | "me";
  text: string;
  time: string;
  read?: boolean;
}
