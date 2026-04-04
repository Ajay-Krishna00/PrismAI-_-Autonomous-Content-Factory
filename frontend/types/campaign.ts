export type AgentStatus = "idle" | "thinking" | "done" | "error";

export type ChatSender = "System" | "Researcher" | "Copywriter" | "Editor";

export type ActiveTab = "source" | "blog" | "social" | "email";
export type ChannelKey = "blog" | "social" | "email";
export type CopywriterMode = "local" | "groq";

export interface ChatMessage {
  id: string;
  sender: ChatSender;
  text: string;
  timestamp: Date;
}

export interface AgentStatusState {
  researcher: AgentStatus;
  copywriter: AgentStatus;
  editor: AgentStatus;
}

export interface CampaignResults {
  source_of_truth: string;
  ambiguity_flags: string[];
  target_audience: string;
  value_proposition: string;
  draft_copy: string;
  social_draft: string;
  email_draft: string;
  editor_feedback: string;
  is_approved: boolean;
  copywriter_runtime_note: string;
}

export interface ChannelApprovalState {
  blog: boolean;
  social: boolean;
  email: boolean;
}

export interface StreamStatePayload {
  source_of_truth?: string;
  ambiguity_flags?: string[];
  target_audience?: string;
  value_proposition?: string;
  draft_copy?: string;
  social_draft?: string;
  email_draft?: string;
  editor_feedback?: string;
  is_approved?: boolean;
  copywriter_mode?: CopywriterMode;
  copywriter_runtime_note?: string;
}

export interface StreamMessage {
  type: "node_start" | "node_update" | "revision" | "end" | "error";
  node?: "researcher" | "copywriter" | "editor";
  state?: StreamStatePayload;
  message?: string;
}
