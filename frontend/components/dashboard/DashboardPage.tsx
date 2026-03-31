import type {
  ActiveTab,
  AgentStatusState,
  CampaignResults,
  ChannelApprovalState,
  ChannelKey,
  ChatMessage,
  CopywriterMode,
} from "@/types/campaign";
import AgentRoomSidebar from "@/components/dashboard/AgentRoomSidebar";
import ComparisonTabs from "@/components/dashboard/ComparisonTabs";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import LiveChatFeed from "@/components/dashboard/LiveChatFeed";

interface DashboardPageProps {
  agentStatus: AgentStatusState;
  chatFeed: ChatMessage[];
  chatEndRef: React.RefObject<HTMLDivElement | null>;
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  results: CampaignResults;
  channelApprovals: ChannelApprovalState;
  regeneratingChannel: ChannelKey | null;
  onApproveChannel: (channel: ChannelKey) => void;
  onRegenerateChannel: (channel: ChannelKey) => Promise<void>;
  onRegenerateAll: () => Promise<void>;
  onExportCampaignKit: () => Promise<void>;
  isCampaignRunning: boolean;
  isExporting: boolean;
  copywriterMode: CopywriterMode;
  setCopywriterMode: (mode: CopywriterMode) => void;
  sourceMaterial: string;
}

export default function DashboardPage({
  agentStatus,
  chatFeed,
  chatEndRef,
  activeTab,
  setActiveTab,
  results,
  channelApprovals,
  regeneratingChannel,
  onApproveChannel,
  onRegenerateChannel,
  onRegenerateAll,
  onExportCampaignKit,
  isCampaignRunning,
  isExporting,
  copywriterMode,
  setCopywriterMode,
  sourceMaterial,
}: DashboardPageProps) {
  return (
    <main className="flex flex-col h-screen bg-[#131313] text-[#E5E2E1] font-sans">
      <DashboardHeader
        onRegenerateAll={onRegenerateAll}
        onExportCampaignKit={onExportCampaignKit}
        isCampaignRunning={isCampaignRunning}
        isExporting={isExporting}
        copywriterMode={copywriterMode}
        setCopywriterMode={setCopywriterMode}
      />

      <div className="flex-1 flex overflow-hidden">
        <AgentRoomSidebar agentStatus={agentStatus} />
        <LiveChatFeed chatFeed={chatFeed} chatEndRef={chatEndRef} />
        <ComparisonTabs
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          results={results}
          channelApprovals={channelApprovals}
          regeneratingChannel={regeneratingChannel}
          onApproveChannel={onApproveChannel}
          onRegenerateChannel={onRegenerateChannel}
          sourceMaterial={sourceMaterial}
        />
      </div>

      <style
        dangerouslySetInnerHTML={{
          __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1c1b1b;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #3C4A42;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #4edea3;
        }
      `,
        }}
      />
    </main>
  );
}
