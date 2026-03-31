import React from "react";
import { Bell, Circle } from "lucide-react";
import GlassSurface from "./GlassSurface";

const SystemStatus = () => {
  return (
    <div className="hidden md:flex items-center gap-2 text-[11px] text-white/70 font-semibold">
      <span
        title="Connection Status: Ollama (Local Llama-3)"
        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full border border-white/10 bg-white/5"
      >
        <Circle className="w-2.5 h-2.5 fill-current text-emerald-400" />
        Ollama Local
      </span>
      <span
        title="Connection Status: Groq (Cloud Llama-3)"
        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full border border-white/10 bg-white/5"
      >
        <Circle className="w-2.5 h-2.5 fill-current text-[#4edea3]" />
        Groq Cloud
      </span>
      <span
        title="API Status: Gemini 2.5 Flash (Active)"
        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full border border-white/10 bg-white/5"
      >
        <Circle className="w-2.5 h-2.5 fill-current text-cyan-300" />
        Gemini
      </span>
    </div>
  );
};

const Header = ({ hasEditorAlert = false }) => {
  return (
    <div className="w-full max-w-[1000px] mx-auto p-4 relative z-50 ">
      <GlassSurface
        displace={0.5}
        distortionScale={-180}
        redOffset={0}
        greenOffset={10}
        blueOffset={20}
        brightness={50}
        opacity={0.93}
        mixBlendMode="screen"
        width="100%"
        className="px-6 py-1"
      >
        <div className="flex w-full justify-between items-center text-white">
          <div className="flex items-baseline gap-2 font-bold tracking-tight text-xl">
            <span className="text-emerald-500 text-3xl">PrismAI</span>
            <span className="text-xs font-normal text-white/60">
              v1.0 (Alpha)
            </span>
          </div>

          <div className="flex items-center gap-4 text-white/80">
            <SystemStatus />

            <button
              type="button"
              aria-label="Notifications"
              className="relative text-white/80 hover:text-white transition-colors"
            >
              <Bell className="w-5 h-5" />
              {hasEditorAlert && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 border border-[#131313]" />
              )}
            </button>
          </div>
        </div>
      </GlassSurface>
    </div>
  );
};

export default Header;
