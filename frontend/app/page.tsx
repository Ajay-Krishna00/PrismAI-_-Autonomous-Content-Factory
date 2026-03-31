"use client";

import DashboardPage from "@/components/dashboard/DashboardPage";
import LandingPage from "@/components/home/LandingPage";
import { useCampaign } from "@/hooks/useCampaign";
import { AnimatePresence, motion } from "framer-motion";

export default function Home() {
  const {
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
  } = useCampaign();

  return (
    <AnimatePresence mode="wait">
      {step === 1 ? (
        <motion.div
          key="launchpad"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <LandingPage
            sourceMaterial={sourceMaterial}
            setSourceMaterial={setSourceMaterial}
            handleStartCampaign={handleStartCampaign}
            hasEditorAlert={hasEditorAlert}
            copywriterMode={copywriterMode}
            setCopywriterMode={setCopywriterMode}
          />
        </motion.div>
      ) : (
        <motion.div
          key="review"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <DashboardPage
            agentStatus={agentStatus}
            chatFeed={chatFeed}
            chatEndRef={chatEndRef}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            results={results}
            channelApprovals={channelApprovals}
            regeneratingChannel={regeneratingChannel}
            onApproveChannel={handleApproveChannel}
            onRegenerateChannel={handleRegenerateChannel}
            onRegenerateAll={handleStartCampaign}
            onExportCampaignKit={handleExportCampaignKit}
            isCampaignRunning={isCampaignRunning}
            isExporting={isExporting}
            copywriterMode={copywriterMode}
            setCopywriterMode={setCopywriterMode}
            sourceMaterial={sourceMaterial}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
