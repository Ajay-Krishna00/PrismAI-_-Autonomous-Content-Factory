import { Play } from "lucide-react";
import type { CopywriterMode } from "@/types/campaign";
import Link from "next/link";

interface DashboardHeaderProps {
  onRegenerateAll: () => Promise<void>;
  onExportCampaignKit: () => Promise<void>;
  isCampaignRunning: boolean;
  isExporting: boolean;
  copywriterMode: CopywriterMode;
  setCopywriterMode: (mode: CopywriterMode) => void;
}

export default function DashboardHeader({
  onRegenerateAll,
  onExportCampaignKit,
  isCampaignRunning,
  isExporting,
  copywriterMode,
  setCopywriterMode,
}: DashboardHeaderProps) {
  return (
    <header className="flex justify-between items-center w-full px-6 py-4 border-b border-[#3C4A42]/30 bg-[#131313] shrink-0">
      <button onClick={()=> window.location.href = "/"} className="flex items-center gap-3 cursor-pointer" >
        <Play className="text-[#10B981] fill-current" size={20} />
        <span className="text-xl font-black text-[#10B981] tracking-tighter">
          PrismAI
        </span>
      </button>
      <div className="flex gap-3 items-center">
        <div className="inline-flex rounded-md border border-[#3C4A42] overflow-hidden">
          <button
            onClick={() => setCopywriterMode("local")}
            className={`px-3 py-1 text-xs font-bold uppercase tracking-widest ${
              copywriterMode === "local" ? "bg-[#10B981] text-black" : "bg-[#1c1b1b] text-[#bbcabf]"
            }`}
          >
            Local
          </button>
          <button
            onClick={() => setCopywriterMode("groq")}
            className={`px-3 py-1 text-xs font-bold uppercase tracking-widest ${
              copywriterMode === "groq" ? "bg-[#10B981] text-black" : "bg-[#1c1b1b] text-[#bbcabf]"
            }`}
          >
            Groq
          </button>
        </div>
        <button
          onClick={() => void onRegenerateAll()}
          disabled={isCampaignRunning}
          className="px-3 py-1 rounded-full border border-[#10B981]/30 bg-[#10B981]/15 text-[#4edea3] text-xs font-bold uppercase tracking-widest disabled:opacity-60"
        >
          {isCampaignRunning ? "Running..." : "Regenerate All"}
        </button>
        <button
          onClick={() => void onExportCampaignKit()}
          disabled={isExporting}
          className="px-3 py-1 rounded-full border border-[#10B981]/30 bg-[#10B981] text-black text-xs font-bold uppercase tracking-widest disabled:opacity-60"
        >
          {isExporting ? "Exporting..." : "One-Click Export"}
        </button>
        
      </div>
    </header>
  );
}
