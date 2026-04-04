import { useEffect, useRef, useState } from "react";
import type {
  ActiveTab,
  AgentStatusState,
  CampaignResults,
  ChannelApprovalState,
  ChannelKey,
  ChatMessage,
  ChatSender,
  CopywriterMode,
  StreamMessage,
} from "@/types/campaign";

const initialAgentStatus: AgentStatusState = {
  researcher: "idle",
  copywriter: "idle",
  editor: "idle",
};

const initialResults: CampaignResults = {
  source_of_truth: "",
  ambiguity_flags: [],
  target_audience: "",
  value_proposition: "",
  draft_copy: "",
  social_draft: "",
  email_draft: "",
  editor_feedback: "",
  is_approved: false,
  copywriter_runtime_note: "",
};

const initialChannelApprovals: ChannelApprovalState = {
  blog: false,
  social: false,
  email: false,
};

export function useCampaign() {
  const [step, setStep] = useState<1 | 2>(1);
  const [sourceMaterial, setSourceMaterial] = useState("");
  const [agentStatus, setAgentStatus] = useState<AgentStatusState>(initialAgentStatus);
  const [chatFeed, setChatFeed] = useState<ChatMessage[]>([]);
  const [activeTab, setActiveTab] = useState<ActiveTab>("source");
  const [results, setResults] = useState<CampaignResults>(initialResults);
  const [channelApprovals, setChannelApprovals] = useState<ChannelApprovalState>(
    initialChannelApprovals,
  );
  const [regeneratingChannel, setRegeneratingChannel] = useState<ChannelKey | null>(null);
  const [isCampaignRunning, setIsCampaignRunning] = useState(false);
  const [copywriterMode, setCopywriterMode] = useState<CopywriterMode>("groq");
  const [isExporting, setIsExporting] = useState(false);
  const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://localhost:8000";

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatFeed]);

  const pushChat = (sender: ChatSender, text: string) => {
    setChatFeed((prev) => [
      ...prev,
      { id: `${Date.now()}-${Math.random()}`, sender, text, timestamp: new Date() },
    ]);
  };

  const handleStartCampaign = async () => {
    if (!sourceMaterial.trim() || isCampaignRunning) return;

    setIsCampaignRunning(true);

    setStep(2);
    setAgentStatus({ researcher: "thinking", copywriter: "idle", editor: "idle" });
    setChatFeed([]);
    setResults(initialResults);
    setChannelApprovals(initialChannelApprovals);

    pushChat("System", "Campaign initialized. Waking up agents...");
    pushChat("Researcher", "I'm on it. Analyzing source material to extract ground truths.");

    try {
      const response = await fetch(`${backendBaseUrl}/api/generate-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_material: sourceMaterial, copywriter_mode: copywriterMode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let sseBuffer = "";

      let done = false;
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          sseBuffer += decoder.decode(value, { stream: true });
        }

        // Process complete SSE events only; leave partial event in buffer.
        const events = sseBuffer.split("\n\n");
        sseBuffer = events.pop() ?? "";

        for (const event of events) {
          const dataLines = event
            .split("\n")
            .filter((line) => line.startsWith("data: "))
            .map((line) => line.slice(6));

          if (!dataLines.length) continue;

          const dataStr = dataLines.join("\n");

          try {
            const data = JSON.parse(dataStr) as StreamMessage;

            if (data.type === "node_start") {
              if (data.node === "researcher") {
                setAgentStatus({ researcher: "thinking", copywriter: "idle", editor: "idle" });
                pushChat("Researcher", "Analyzing source material now...");
              } else if (data.node === "copywriter") {
                setAgentStatus((prev) => ({ ...prev, copywriter: "thinking", editor: "idle" }));
                pushChat("Copywriter", "Generating campaign drafts...");
              } else if (data.node === "editor") {
                setAgentStatus((prev) => ({ ...prev, editor: "thinking" }));
                pushChat("Editor", "Auditing accuracy and tone...");
              }
            } else if (data.type === "revision") {
              pushChat("System", data.message ?? "Running revision cycle...");
            } else if (data.type === "node_update") {
              const node = data.node;
              const state = data.state ?? {};

              if (node === "researcher") {
                setAgentStatus((prev) => ({ ...prev, researcher: "done", copywriter: "thinking" }));
                setResults((prev) => ({
                  ...prev,
                  source_of_truth: state.source_of_truth ?? prev.source_of_truth,
                  ambiguity_flags: state.ambiguity_flags ?? prev.ambiguity_flags,
                  target_audience: state.target_audience ?? prev.target_audience,
                  value_proposition: state.value_proposition ?? prev.value_proposition,
                }));
                pushChat("Researcher", "Done. Extracted core facts and passed them to the Copywriter.");
                pushChat("Copywriter", "Thanks. Drafting the Blog, Social thread, and Email copy now...");
              } else if (node === "copywriter") {
                setAgentStatus((prev) => ({ ...prev, copywriter: "done", editor: "thinking" }));
                setResults((prev) => ({
                  ...prev,
                  draft_copy: state.draft_copy ?? prev.draft_copy,
                  social_draft: state.social_draft ?? prev.social_draft,
                  email_draft: state.email_draft ?? prev.email_draft,
                  copywriter_runtime_note:
                    state.copywriter_runtime_note ?? prev.copywriter_runtime_note,
                }));
                setChannelApprovals(initialChannelApprovals);
                pushChat("Copywriter", "Drafts are ready. Sending over to the Editor for review.");
                if (state.copywriter_runtime_note) {
                  pushChat("System", state.copywriter_runtime_note);
                }
                pushChat("Editor", "Reviewing content against brand safety and strict guidelines...");
              } else if (node === "editor") {
                setResults((prev) => ({
                  ...prev,
                  editor_feedback: state.editor_feedback ?? prev.editor_feedback,
                  is_approved: !!state.is_approved,
                }));

                if (state.is_approved) {
                  setAgentStatus((prev) => ({ ...prev, editor: "done" }));
                  pushChat("Editor", "All good. Content is approved for distribution!");
                  setActiveTab("blog");
                } else {
                  setAgentStatus((prev) => ({ ...prev, editor: "thinking", copywriter: "thinking" }));
                  pushChat("Editor", `Rejecting drafts. Issues found: ${state.editor_feedback ?? "N/A"}`);
                  pushChat("Copywriter", "Fixing issues and rewriting now...");
                }
              }
            } else if (data.type === "end") {
              pushChat("System", data.message ?? "Campaign execution completed.");
              setActiveTab("blog");
            } else if (data.type === "error") {
              pushChat("System", `Error encountered: ${data.message ?? "Unknown error"}`);
              setAgentStatus({ researcher: "error", copywriter: "error", editor: "error" });
            }
          } catch (error) {
            console.error("Failed to parse SSE JSON", error);
          }
        }
      }
    } catch (error) {
      console.error(error);
      pushChat("System", "Connection failed. Is the backend running?");
      setAgentStatus({ researcher: "error", copywriter: "error", editor: "error" });
    } finally {
      setIsCampaignRunning(false);
    }
  };

  const hasEditorAlert =
    agentStatus.editor === "error" || (!!results.editor_feedback && !results.is_approved);

  const handleApproveChannel = (channel: ChannelKey) => {
    setChannelApprovals((prev) => ({ ...prev, [channel]: true }));
    pushChat("System", `${channel.toUpperCase()} channel approved manually.`);
  };

  const handleRegenerateChannel = async (channel: ChannelKey) => {
    if (!results.source_of_truth) {
      pushChat("System", "Cannot regenerate yet. Source of truth is missing.");
      return;
    }

    setRegeneratingChannel(channel);
    pushChat("Copywriter", `Regenerating ${channel.toUpperCase()} channel with the latest constraints...`);

    try {
      const response = await fetch(`${backendBaseUrl}/api/regenerate-channel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel,
          source_of_truth: results.source_of_truth,
          value_proposition: results.value_proposition,
          target_audience: results.target_audience,
          editor_feedback: results.editor_feedback,
          draft_copy: results.draft_copy,
          social_draft: results.social_draft,
          email_draft: results.email_draft,
          copywriter_mode: copywriterMode,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = (await response.json()) as {
        success: boolean;
        draft_copy: string;
        social_draft: string;
        email_draft: string;
        copywriter_runtime_note?: string;
      };

      if (!data.success) {
        throw new Error("Regeneration failed");
      }

      setResults((prev) => ({
        ...prev,
        draft_copy: data.draft_copy ?? prev.draft_copy,
        social_draft: data.social_draft ?? prev.social_draft,
        email_draft: data.email_draft ?? prev.email_draft,
        copywriter_runtime_note: data.copywriter_runtime_note ?? prev.copywriter_runtime_note,
      }));
      setChannelApprovals((prev) => ({ ...prev, [channel]: false }));
      setActiveTab(channel);
      pushChat("Copywriter", `${channel.toUpperCase()} channel regenerated successfully.`);
      if (data.copywriter_runtime_note) {
        pushChat("System", data.copywriter_runtime_note);
      }
    } catch (error) {
      console.error(error);
      pushChat("System", `Failed to regenerate ${channel.toUpperCase()} channel.`);
    } finally {
      setRegeneratingChannel(null);
    }
  };

  const handleExportCampaignKit = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(`${backendBaseUrl}/api/export-campaign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_of_truth: results.source_of_truth,
          blog_draft: results.draft_copy,
          social_draft: results.social_draft,
          email_draft: results.email_draft,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "prismai_campaign_kit.zip";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      pushChat("System", "Campaign Kit exported as ZIP.");
    } catch (error) {
      console.error(error);
      pushChat("System", "Failed to export Campaign Kit.");
    } finally {
      setIsExporting(false);
    }
  };

  return {
    step,
    sourceMaterial,
    setSourceMaterial,
    agentStatus,
    chatFeed,
    activeTab,
    setActiveTab,
    results,
    channelApprovals,
    copywriterMode,
    setCopywriterMode,
    regeneratingChannel,
    isCampaignRunning,
    isExporting,
    chatEndRef,
    hasEditorAlert,
    handleStartCampaign,
    handleApproveChannel,
    handleRegenerateChannel,
    handleExportCampaignKit,
  };
}
