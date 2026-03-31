import {
  CheckCircle2,
  CircleDashed,
  Eye,
  LayoutDashboard,
  PenTool,
  RefreshCcw,
  Search,
} from "lucide-react";
import type { AgentStatus, AgentStatusState } from "@/types/campaign";

interface AgentRoomSidebarProps {
  agentStatus: AgentStatusState;
}

function getStatusIcon(status: AgentStatus) {
  switch (status) {
    case "idle":
      return <CircleDashed className="text-[#3C4A42]" size={20} />;
    case "thinking":
      return <RefreshCcw className="text-[#4edea3] animate-spin" size={20} />;
    case "done":
      return <CheckCircle2 className="text-[#10b981]" size={20} />;
    case "error":
      return <CircleDashed className="text-red-500" size={20} />;
  }
}

export default function AgentRoomSidebar({ agentStatus }: AgentRoomSidebarProps) {
  return (
    <aside className="w-64 border-r border-[#3C4A42]/30 bg-[#1c1b1b] flex flex-col p-4">
      <h3 className="text-xs font-bold text-[#bbcabf] uppercase tracking-widest mb-6 flex items-center gap-2">
        <LayoutDashboard size={16} /> Agent Room
      </h3>

      <div className="space-y-4">
        <div
          className={`p-4 rounded-lg border ${
            agentStatus.researcher === "thinking"
              ? "border-[#4edea3] bg-[#4edea3]/5"
              : "border-[#3C4A42]/50 bg-[#131313]"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 font-semibold text-sm">
              <Search size={16} className="text-[#9ed2b5]" /> Researcher
            </div>
            {getStatusIcon(agentStatus.researcher)}
          </div>
          <p className="text-[11px] text-[#86948a] leading-tight">
            Extracts ground truths and builds the foundational knowledge base.
          </p>
        </div>

        <div
          className={`p-4 rounded-lg border ${
            agentStatus.copywriter === "thinking"
              ? "border-[#4edea3] bg-[#4edea3]/5"
              : "border-[#3C4A42]/50 bg-[#131313]"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 font-semibold text-sm">
              <PenTool size={16} className="text-[#ffb3af]" /> Copywriter
            </div>
            {getStatusIcon(agentStatus.copywriter)}
          </div>
          <p className="text-[11px] text-[#86948a] leading-tight">
            Transforms facts into multi-channel marketing campaigns.
          </p>
        </div>

        <div
          className={`p-4 rounded-lg border ${
            agentStatus.editor === "thinking"
              ? "border-[#4edea3] bg-[#4edea3]/5"
              : "border-[#3C4A42]/50 bg-[#131313]"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 font-semibold text-sm">
              <Eye size={16} className="text-[#fc7c78]" /> Editor
            </div>
            {getStatusIcon(agentStatus.editor)}
          </div>
          <p className="text-[11px] text-[#86948a] leading-tight">
            Enforces brand safety and quality assurance.
          </p>
        </div>
      </div>
    </aside>
  );
}
