import { MessageSquare } from "lucide-react";
import type { ChatMessage } from "@/types/campaign";

interface LiveChatFeedProps {
  chatFeed: ChatMessage[];
  chatEndRef: React.RefObject<HTMLDivElement | null>;
}

function senderTagClasses(sender: ChatMessage["sender"]) {
  if (sender === "System") return "bg-[#3C4A42] text-white";
  if (sender === "Researcher") return "bg-[#9ed2b5]/20 text-[#9ed2b5]";
  if (sender === "Copywriter") return "bg-[#ffb3af]/20 text-[#ffb3af]";
  return "bg-[#fc7c78]/20 text-[#fc7c78]";
}

export default function LiveChatFeed({ chatFeed, chatEndRef }: LiveChatFeedProps) {
  return (
    <section className="w-80 border-r border-[#3C4A42]/30 bg-[#131313] flex flex-col">
      <div className="p-4 border-b border-[#3C4A42]/30 bg-[#1c1b1b]">
        <h3 className="text-xs font-bold text-[#bbcabf] uppercase tracking-widest flex items-center gap-2">
          <MessageSquare size={16} /> Live Comm Feed
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-sm">
        {chatFeed.map((msg) => (
          <div key={msg.id} className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${senderTagClasses(
                  msg.sender,
                )}`}
              >
                {msg.sender}
              </span>
              <span className="text-[10px] text-[#86948a]">
                {msg.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            </div>
            <p className="text-[#E5E2E1] leading-relaxed text-xs p-2 rounded bg-[#1c1b1b] border border-[#3C4A42]/30 shadow-sm whitespace-pre-wrap">
              {msg.text}
            </p>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
    </section>
  );
}
