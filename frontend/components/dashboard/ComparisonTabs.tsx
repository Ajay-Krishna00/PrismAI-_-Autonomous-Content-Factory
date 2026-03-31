import { CheckCircle2, Files, LayoutDashboard, Play, RefreshCcw } from "lucide-react";
import type { ActiveTab, CampaignResults, ChannelApprovalState, ChannelKey } from "@/types/campaign";

interface ComparisonTabsProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  results: CampaignResults;
  channelApprovals: ChannelApprovalState;
  regeneratingChannel: ChannelKey | null;
  onApproveChannel: (channel: ChannelKey) => void;
  onRegenerateChannel: (channel: ChannelKey) => Promise<void>;
  sourceMaterial: string;
}

const tabs: ActiveTab[] = ["source", "blog", "social", "email"];

export default function ComparisonTabs({
  activeTab,
  setActiveTab,
  results,
  channelApprovals,
  regeneratingChannel,
  onApproveChannel,
  onRegenerateChannel,
  sourceMaterial,
}: ComparisonTabsProps) {
  return (
    <section className="flex-1 flex flex-col bg-[#1c1b1b] overflow-hidden">
      <div className="flex border-b border-[#3C4A42]/30 bg-[#131313] px-2 py-2 gap-2 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-xs font-bold uppercase tracking-widest transition-colors flex items-center gap-2 ${
              activeTab === tab
                ? "bg-[#2a2a2a] text-[#4edea3] border border-[#3C4A42]"
                : "text-[#86948a] hover:bg-[#1c1b1b] hover:text-[#bbcabf] border border-transparent"
            }`}
          >
            {tab === "source" ? <Files size={14} /> : <LayoutDashboard size={14} />}
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6 lg:p-10 custom-scrollbar">
        {activeTab === "source" && (
          <div className="h-full flex flex-col animate-in fade-in duration-300">
            <h2 className="text-xl font-bold mb-4 text-[#E5E2E1]">Original Source Context</h2>
            <div className="flex-1 p-6 bg-[#131313] border border-[#3C4A42]/50 rounded-xl leading-relaxed whitespace-pre-wrap text-[#bbcabf]">
              {sourceMaterial}
            </div>

            <div className="mt-4 p-4 bg-[#131313] border border-[#3C4A42]/50 rounded-xl">
              <h3 className="text-sm font-bold text-[#E5E2E1] mb-2">Researcher Structured Output</h3>
              <div className="text-sm text-[#bbcabf] mb-3">
                <div>
                  <span className="text-[#86948a]">Value Proposition: </span>
                  {results.value_proposition || "Not available"}
                </div>
                <div>
                  <span className="text-[#86948a]">Target Audience: </span>
                  {results.target_audience || "Not available"}
                </div>
              </div>

              <h4 className="text-xs uppercase tracking-widest text-[#86948a] mb-2">Ambiguity Flags</h4>
              {results.ambiguity_flags.length > 0 ? (
                <ul className="space-y-1 text-sm text-[#ffb3af]">
                  {results.ambiguity_flags.map((flag, idx) => (
                    <li key={`${idx}-${flag.slice(0, 16)}`}>• {flag}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[#9ed2b5]">No ambiguity flags detected.</p>
              )}
            </div>
          </div>
        )}

        {activeTab === "blog" && (
          <div className="max-w-3xl mx-auto animate-in fade-in duration-300">
            <h2 className="text-2xl font-bold mb-6 text-white border-b border-[#3C4A42]/50 pb-4">
              Approved Blog Draft
            </h2>
            {results.draft_copy ? (
              <>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => onApproveChannel("blog")}
                    className="px-3 py-2 rounded-md border border-[#10b981]/40 bg-[#10b981]/10 text-[#4edea3] text-xs font-bold uppercase tracking-widest"
                  >
                    <CheckCircle2 className="inline-block mr-2" size={14} />
                    Approve Blog
                  </button>
                  <button
                    onClick={() => void onRegenerateChannel("blog")}
                    disabled={regeneratingChannel === "blog"}
                    className="px-3 py-2 rounded-md border border-[#3C4A42] bg-[#131313] text-[#bbcabf] text-xs font-bold uppercase tracking-widest disabled:opacity-60"
                  >
                    <RefreshCcw
                      className={`inline-block mr-2 ${regeneratingChannel === "blog" ? "animate-spin" : ""}`}
                      size={14}
                    />
                    Regenerate Blog
                  </button>
                  {channelApprovals.blog && (
                    <span className="text-xs font-bold uppercase tracking-widest text-[#4edea3]">
                      Blog Approved
                    </span>
                  )}
                </div>

                <div className="prose prose-invert prose-emerald max-w-none">
                  <div className="whitespace-pre-wrap text-[#E5E2E1] leading-loose">
                    {results.draft_copy}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-[#86948a] flex items-center gap-2 italic">
                Awaiting draft generation...
              </div>
            )}
          </div>
        )}

        {activeTab === "social" && (
          <div className="max-w-full lg:max-w-2xl mx-auto animate-in fade-in duration-300">
            <h2 className="text-2xl font-bold mb-6 text-white border-b border-[#3C4A42]/50 pb-4">
              Social Media Thread
            </h2>
            {results.social_draft ? (
              <>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => onApproveChannel("social")}
                    className="px-3 py-2 rounded-md border border-[#10b981]/40 bg-[#10b981]/10 text-[#4edea3] text-xs font-bold uppercase tracking-widest"
                  >
                    <CheckCircle2 className="inline-block mr-2" size={14} />
                    Approve Social
                  </button>
                  <button
                    onClick={() => void onRegenerateChannel("social")}
                    disabled={regeneratingChannel === "social"}
                    className="px-3 py-2 rounded-md border border-[#3C4A42] bg-[#131313] text-[#bbcabf] text-xs font-bold uppercase tracking-widest disabled:opacity-60"
                  >
                    <RefreshCcw
                      className={`inline-block mr-2 ${regeneratingChannel === "social" ? "animate-spin" : ""}`}
                      size={14}
                    />
                    Regenerate Social
                  </button>
                  {channelApprovals.social && (
                    <span className="text-xs font-bold uppercase tracking-widest text-[#4edea3]">
                      Social Approved
                    </span>
                  )}
                </div>

                <div className="bg-[#131313] border border-[#3C4A42]/50 rounded-xl p-6 shadow-xl">
                  <div className="whitespace-pre-wrap text-[#E5E2E1] leading-relaxed">
                    {results.social_draft.split("\n\n").map((post, i) => (
                      <div
                        key={`${i}-${post.slice(0, 8)}`}
                        className="mb-6 pb-6 border-b border-[#3C4A42]/20 last:border-0 last:mb-0 last:pb-0"
                      >
                        <div className="flex gap-4">
                          <div className="w-10 h-10 rounded-full bg-[#3C4A42] flex items-center justify-center shrink-0">
                            <Play className="text-[#4edea3] ml-1" size={16} />
                          </div>
                          <div className="flex-1">
                            <div className="font-bold text-[#E5E2E1]">
                              PrismAI <span className="text-[#86948a] font-normal">@prisma_ai</span>
                            </div>
                            <p className="mt-2 text-[15px]">{post}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-[#86948a] flex items-center gap-2 italic">
                Awaiting draft generation...
              </div>
            )}
          </div>
        )}

        {activeTab === "email" && (
          <div className="max-w-3xl mx-auto animate-in fade-in duration-300">
            <h2 className="text-2xl font-bold mb-6 text-white border-b border-[#3C4A42]/50 pb-4">
              Email Campaign
            </h2>
            {results.email_draft ? (
              <>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => onApproveChannel("email")}
                    className="px-3 py-2 rounded-md border border-[#10b981]/40 bg-[#10b981]/10 text-[#4edea3] text-xs font-bold uppercase tracking-widest"
                  >
                    <CheckCircle2 className="inline-block mr-2" size={14} />
                    Approve Email
                  </button>
                  <button
                    onClick={() => void onRegenerateChannel("email")}
                    disabled={regeneratingChannel === "email"}
                    className="px-3 py-2 rounded-md border border-[#3C4A42] bg-[#131313] text-[#bbcabf] text-xs font-bold uppercase tracking-widest disabled:opacity-60"
                  >
                    <RefreshCcw
                      className={`inline-block mr-2 ${regeneratingChannel === "email" ? "animate-spin" : ""}`}
                      size={14}
                    />
                    Regenerate Email
                  </button>
                  {channelApprovals.email && (
                    <span className="text-xs font-bold uppercase tracking-widest text-[#4edea3]">
                      Email Approved
                    </span>
                  )}
                </div>

                <div className="bg-white text-black p-8 rounded-xl shadow-xl font-sans">
                  <div className="border-b border-gray-200 pb-4 mb-6">
                    <div className="text-gray-500 text-sm mb-1">From: PrismAI Marketing Team</div>
                    <div className="font-bold text-lg">Subject: Transforming Your Strategy...</div>
                  </div>
                  <div className="whitespace-pre-wrap leading-relaxed text-gray-800">
                    {results.email_draft}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-[#86948a] flex items-center gap-2 italic">
                Awaiting draft generation...
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
