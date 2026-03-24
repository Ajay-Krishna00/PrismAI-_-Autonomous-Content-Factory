"use client";

import { useState } from "react";
import {
  Send,
  FileText,
  CheckCircle,
  RefreshCcw,
  AlertTriangle,
} from "lucide-react";

export default function Home() {
  const [sourceMaterial, setSourceMaterial] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    if (!sourceMaterial) return;
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_material: sourceMaterial }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error connecting to backend", error);
      alert("Uh oh! Ensure your FastAPI server (uvicorn) is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-6xl mx-auto font-sans">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold text-blue-900 mb-2">
          Autonomous Content Factory
        </h1>
        <p className="text-slate-500 text-lg">
          Provide a source document, and our AI agents will handle the rest.
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-8">
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 h-fit">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-800">
            <FileText className="text-blue-500" /> Source Material
          </h2>
          <textarea
            value={sourceMaterial}
            onChange={(e) => setSourceMaterial(e.target.value)}
            className="w-full h-64 p-4 border rounded-xl bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none resize-none text-slate-700"
            placeholder="Paste your product specs, raw notes, or a URL here..."
          />
          <button
            onClick={handleGenerate}
            disabled={loading || !sourceMaterial}
            className="mt-6 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-md"
          >
            {loading ? (
              <RefreshCcw className="animate-spin" size={20} />
            ) : (
              <Send size={20} />
            )}
            {loading
              ? "Agents are working (takes ~15-30s)..."
              : "Generate Campaign"}
          </button>
        </section>

        {/* RIGHT COLUMN - AGENT OUTPUTS */}
        <section className="space-y-6">
          {loading && (
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center animate-pulse min-h-64">
              <RefreshCcw
                className="animate-spin text-blue-500 mb-4"
                size={40}
              />
              <p className="text-slate-700 font-medium text-lg">
                The Lead Researcher is analyzing the facts...
              </p>
              <p className="text-sm text-slate-400 mt-2">
                The Copywriter and Editor will argue over the draft shortly.
              </p>
            </div>
          )}

          {result && (
            <>
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <h3 className="text-lg font-bold text-slate-800 mb-3 border-b pb-2 flex items-center gap-2">
                  <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded-md text-xs">
                    AGENT 1
                  </span>
                  Researcher's Fact Sheet
                </h3>
                <div
                  className="prose prose-sm prose-slate"
                  dangerouslySetInnerHTML={{
                    __html: result.facts?.replace(/\n/g, "<br/>") || "",
                  }}
                />
              </div>

              <div
                className={`p-4 rounded-xl border flex items-center gap-4 shadow-sm ${result.approved ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}
              >
                {result.approved ? (
                  <CheckCircle className="text-green-600 shrink-0" size={32} />
                ) : (
                  <AlertTriangle className="text-red-500 shrink-0" size={32} />
                )}
                <div>
                  <h4
                    className={`font-bold flex items-center gap-2 ${result.approved ? "text-green-800" : "text-red-800"}`}
                  >
                    <span
                      className={`px-2 py-0.5 rounded-md text-xs text-white ${result.approved ? "bg-green-600" : "bg-red-600"}`}
                    >
                      AGENT 3
                    </span>
                    Editor-in-Chief Check
                  </h4>
                  <p className="text-sm text-slate-700 mt-1 font-medium italic">
                    {result.editor_notes ||
                      "Perfect draft. No hallucinations detected."}
                  </p>
                </div>
              </div>

              {/* Final Blog Draft */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <h3 className="text-lg font-bold text-slate-800 mb-3 border-b pb-2 flex items-center gap-2">
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-xs">
                    AGENT 2
                  </span>
                  Final Approved Blog Draft
                </h3>
                {/* The content that made it past the editor! */}
                <div className="whitespace-pre-wrap text-slate-700 leading-relaxed font-medium">
                  {result.blog_draft}
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
