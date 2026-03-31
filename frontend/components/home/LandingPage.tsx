import { Play, UploadCloud } from "lucide-react";
import Header from "@/components/Header";
import Prism from "@/components/Prism";
import type { CopywriterMode } from "@/types/campaign";

interface LandingPageProps {
  sourceMaterial: string;
  setSourceMaterial: (value: string) => void;
  handleStartCampaign: () => Promise<void>;
  hasEditorAlert: boolean;
  copywriterMode: CopywriterMode;
  setCopywriterMode: (mode: CopywriterMode) => void;
}

export default function LandingPage({
  sourceMaterial,
  setSourceMaterial,
  handleStartCampaign,
  hasEditorAlert,
  copywriterMode,
  setCopywriterMode,
}: LandingPageProps) {
  return (
    <div className="relative min-h-screen w-full font-sans overflow-hidden bg-[#0A0A0A]">
      <div className="absolute inset-0 z-0 w-full">
        <Prism
          animationType="rotate"
          timeScale={0.6}
          height={3.5}
          baseWidth={5.5}
          scale={2}
          hueShift={0}
          colorFrequency={1}
          noise={0}
          glow={1}
        />
      </div>

      <div className="relative z-10 pointer-events-auto w-full justify-center flex">
        <Header hasEditorAlert={hasEditorAlert} />
      </div>

      <section className="relative z-10 flex-1 flex flex-col items-center justify-center">
        <div className="max-w-4xl w-full text-center mt-2 mb-4 drop-shadow-lg mx-auto">
          {/* <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-[#10b981]/10 border border-[#10b981]/20 backdrop-blur-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest text-[#4edea3] font-bold">
              Factory Ready
            </span>
          </div> */}
          <h2 className="text-4xl md:text-6xl font-black tracking-tighter text-white mb-4 drop-shadow-xl">
            From Source to Strategy, Automatically.
          </h2>
          <p className="text-[#E5E2E1] text-lg max-w-2xl mx-auto font-medium leading-relaxed drop-shadow-md">
            Orchestrate a specialized agent assembly line to research, write, and audit your
            technical content in seconds.
          </p>
          <div className="mt-4 inline-flex rounded-md bg-[#131313]/70 border border-[#3C4A42]/60 p-1 backdrop-blur-sm">
            <button
              type="button"
              onClick={() => setCopywriterMode("groq")}
              className={`px-4 py-2 text-xs font-black uppercase tracking-widest rounded transition-colors ${
                copywriterMode === "groq"
                  ? "bg-[#10B981] text-black"
                  : "text-[#bbcabf] hover:text-white"
              }`}
            >
              Groq Cloud
            </button>
            <button
              type="button"
              onClick={() => setCopywriterMode("local")}
              className={`px-4 py-2 text-xs font-black uppercase tracking-widest rounded transition-colors ${
                copywriterMode === "local"
                  ? "bg-[#10B981] text-black"
                  : "text-[#bbcabf] hover:text-white"
              }`}
            >
              Local LLM
            </button>
          </div>
        </div>

        <div className="w-full max-w-2xl relative group drop-shadow-2xl">
          <div className="absolute inset-0 bg-[#4edea3]/10 blur-3xl rounded-full opacity-30 group-hover:opacity-60 transition-opacity duration-700" />
          <div className="relative h-full w-full rounded-xl flex flex-col items-center justify-center p-5 bg-[#131313]/40 backdrop-blur-xl border border-[#3C4A42]/50 hover:border-[#10b981]/80 transition-all duration-300">
            <UploadCloud className="text-[#4edea3] mb-1" size={48} />
            <p className="text-white font-semibold text-lg mb-1">Provide Source Material</p>
            <p className="text-[#bbcabf] text-sm font-medium mb-2">Paste text below to begin.</p>

            <textarea
              className="w-full h-40 bg-[#000000]/40 font-mono border border-[#3C4A42]/60 rounded-lg p-4 text-[#E5E2E1] focus:ring-1 focus:ring-[#10B981] outline-none resize-none backdrop-blur-sm"
              placeholder="E.g., We are launching a new smart thermos that keeps coffee hot for 24 hours..."
              value={sourceMaterial}
              onChange={(e) => setSourceMaterial(e.target.value)}
            />

            <button
              onClick={handleStartCampaign}
              disabled={!sourceMaterial.trim()}
              className="mt-6 px-8 py-3 bg-[#10B981] hover:bg-[#3ec48f] text-black disabled:bg-[#2a2a2a] disabled:text-[#86948a] text-xs font-black uppercase tracking-widest rounded-md transition-all active:scale-95 w-full flex items-center justify-center gap-2 shadow-lg"
            >
              <Play size={16} fill="currentColor" /> Initialize Agents
            </button>
          </div>
        </div>

        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 mb-8">
          <article className="rounded-xl border border-[#3C4A42]/50 bg-[#131313]/60 p-4 backdrop-blur-sm">
            <h3 className="text-[#10B981] font-bold uppercase text-sm tracking-widest mb-2">
              Lead Researcher
            </h3>
            <p className="text-[#bbcabf] text-sm">
              Extracts the &apos;Source of Truth&apos; and flags ambiguities using Gemini 2.5 Flash.
            </p>
          </article>
          <article className="rounded-xl border border-[#3C4A42]/50 bg-[#131313]/60 p-4 backdrop-blur-sm">
            <h3 className="text-[#10B981] font-bold uppercase text-sm tracking-widest mb-2">
              Creative Copywriter
            </h3>
            <p className="text-[#bbcabf] text-sm">
              Generates blogs, threads, and emails. Features a &apos;Hybrid Toggle&apos; between Local GPU and Groq Cloud.
            </p>
          </article>
          <article className="rounded-xl border border-[#3C4A42]/50 bg-[#131313]/60 p-4 backdrop-blur-sm">
            <h3 className="text-[#10B981] font-bold uppercase text-sm tracking-widest mb-2">
              Editor-in-Chief
            </h3>
            <p className="text-[#bbcabf] text-sm">
              The Quality Gatekeeper. Performs hallucination checks and triggers self-correction loops.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
