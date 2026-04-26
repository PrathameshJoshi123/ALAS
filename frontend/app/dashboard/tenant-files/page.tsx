"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Undo2,
  Redo2,
  Save,
  Info,
  CheckCircle2,
  AlertTriangle,
  Globe,
  Plus,
  MessageSquare,
  Loader2,
  Sparkles,
  Bot,
  Send,
  History,
  X,
  FileText,
  Download,
} from "lucide-react";
import toast from "react-hot-toast";
import { apiClient } from "@/services/api";
import { useSearchParams } from "next/navigation";
import { marked } from "marked";
import DOMPurify from "dompurify";
import React from "react";

const DocumentEditor = React.memo(({ contract, htmlContent, onInput }: any) => {
  return (
    <div
      id="contract-document-content"
      contentEditable
      suppressContentEditableWarning
      onInput={onInput}
      className="outline-none focus:bg-slate-50/50 p-4 -mx-4 rounded-2xl transition-colors"
    >
      <h1 className="text-[32px] font-bold text-[#0B1437] mb-6 tracking-tight">
        {(
          contract?.original_filename ||
          contract?.markdown_file ||
          "MASTER_SERVICE_AGREEMENT"
        )
          ?.split(".")[0]
          ?.replaceAll("_", " ")}
      </h1>

      <div className="contract-markdown markdown-body max-w-none">
        <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
      </div>
    </div>
  );
}, (prev, next) => {
  return prev.htmlContent === next.htmlContent && 
         prev.contract?.original_filename === next.contract?.original_filename &&
         prev.contract?.markdown_file === next.contract?.markdown_file;
});

export default function TenantFilesPage() {
  const searchParams = useSearchParams();
  const contractId = searchParams.get("id");

  const [isGenerating, setIsGenerating] = useState(() => {
    return searchParams.get("generating") === "true";
  });
  const [loadingStep, setLoadingStep] = useState(0);

  const [contract, setContract] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [fetching, setFetching] = useState(!!contractId);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [qaInput, setQaInput] = useState("");
  const [qaLoading, setQaLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState<
    Array<{ question: string; answer: string }>
  >([]);
  const [pollingActive, setPollingActive] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState<Set<number>>(
    new Set(),
  );

  useEffect(() => {
    async function parseMarkdown() {
      const content =
        analysis?.analysis_markdown ||
        "Analysis markdown will appear here once processing is complete.";
      try {
        marked.setOptions({
          gfm: true,
          breaks: true,
        });

        const rendered = marked.parse(content);
        const renderedHtml =
          typeof rendered === "string" ? rendered : await rendered;
        const sanitized = DOMPurify.sanitize(renderedHtml);
        setHtmlContent(sanitized);
      } catch (err) {
        const escaped = DOMPurify.sanitize(content, { ALLOWED_TAGS: [] });
        setHtmlContent(`<p>${escaped}</p>`);
      }
    }
    parseMarkdown();
  }, [analysis?.analysis_markdown]);

  const fetchContractData = useCallback(
    async (isPolling = false) => {
      if (!contractId) return;
      try {
        if (!isPolling) setFetching(true);
        const [contractData, analysisData] = await Promise.all([
          apiClient.getContractDetails(contractId),
          apiClient.getContractAnalysis(contractId),
        ]);
        setContract(contractData);
        setAnalysis(analysisData);

        const shouldPoll =
          contractData?.status !== "completed" ||
          !contractData?.live?.final_analysis_ready ||
          !contractData?.live?.vector_store_ready;
        setPollingActive(Boolean(shouldPoll));
      } catch (error) {
        console.error("Failed to fetch contract data", error);
        // toast.error("Failed to load contract details.");
      } finally {
        setFetching(false);
      }
    },
    [contractId],
  );

  useEffect(() => {
    if (!isGenerating && contractId) {
      fetchContractData(false);
    }
  }, [contractId, isGenerating, fetchContractData]);

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;

    if (!isGenerating && contractId && pollingActive) {
      intervalId = setInterval(() => {
        fetchContractData(true);
      }, 4000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [contractId, isGenerating, fetchContractData, pollingActive]);

  useEffect(() => {
    if (isGenerating) {
      const interval = setInterval(() => {
        setLoadingStep((s) => s + 1);
      }, 1200);

      const timeout = setTimeout(() => {
        clearInterval(interval);
        setIsGenerating(false);
        // Clear generating param and set generated=true
        const url = new URL(window.location.href);
        url.searchParams.delete("generating");
        url.searchParams.set("generated", "true");
        window.history.replaceState(null, "", url.pathname + url.search);
      }, 5500);

      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }
  }, [isGenerating]);

  const handleContentChange = useCallback(() => {
    setHasUnsavedChanges(prev => {
      if (!prev) return true;
      return prev;
    });
  }, []);

  const handleSaveAndAnalyze = async () => {
    if (!contractId) return;

    setIsAnalyzing(true);
    const analysisToast = toast.loading(
      "Analyzing contract with DeepAgents...",
    );

    try {
      // 1. In a real app, we would save the content first.
      // 2. Trigger analysis
      await apiClient.analyzeContract(contractId);
      const result = await apiClient.getContractAnalysis(contractId);
      setAnalysis(result);
      setHasUnsavedChanges(false);
      toast.success("Analysis complete. Risk profile updated!", {
        id: analysisToast,
      });
    } catch (error) {
      console.error("Analysis failed", error);
      toast.error("Failed to re-analyze contract.", { id: analysisToast });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSeverityColor = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case "critical":
        return "text-red-600";
      case "high":
        return "text-orange-600";
      case "medium":
        return "text-amber-600";
      case "low":
        return "text-blue-600";
      case "info":
        return "text-slate-500";
      default:
        return "text-slate-500";
    }
  };

  const getSeverityBg = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case "critical":
        return "bg-red-50";
      case "high":
        return "bg-orange-50";
      case "medium":
        return "bg-amber-50";
      case "low":
        return "bg-blue-50";
      case "info":
        return "bg-slate-50";
      default:
        return "bg-slate-50";
    }
  };

  const handleAskQuestion = async () => {
    if (!contractId || !qaInput.trim() || qaLoading) return;

    const question = qaInput.trim();
    setQaInput("");
    setQaLoading(true);

    try {
      const response = await apiClient.askContractQuestion(
        contractId,
        question,
      );
      setQaHistory((prev) => [
        ...prev,
        {
          question,
          answer: response?.answer || response?.error || "No answer returned.",
        },
      ]);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to get AI answer.");
      setQaHistory((prev) => [
        ...prev,
        {
          question,
          answer: "Request failed. Please try again.",
        },
      ]);
    } finally {
      setQaLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!contractId || !htmlContent) return;

    try {
      const toastId = toast.loading("Preparing PDF for download...");
      const html2pdf = (await import("html2pdf.js")).default;
      
      const element = document.getElementById("contract-document-content");
      if (!element) {
        toast.dismiss(toastId);
        return;
      }

      const opt = {
        margin:       0.7,
        filename:     `${contract?.company_name?.replace(/\s+/g, '_') || 'contract'}_document.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
      };

      await html2pdf().set(opt).from(element).save();
      toast.success("PDF Downloaded successfully!", { id: toastId });
    } catch (e) {
      console.error("PDF Export error:", e);
      toast.error("Failed to generate PDF");
    }
  };

  if (isGenerating) {
    const steps = [
      "Structuring legal frameworks...",
      "Aligning jurisdiction statutes...",
      "Cross-referencing liability caps...",
      "Applying strict compliance...",
      "Finalizing document blueprint...",
    ];

    return (
      <div className="flex w-full h-[calc(100vh-70px)] bg-[#0B1437] items-center justify-center relative overflow-hidden flex-col gap-6">
        <div className="absolute w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] animate-pulse"></div>
        <div
          className="absolute w-[400px] h-[400px] bg-purple-600/20 rounded-full blur-[100px] -translate-x-1/2 translate-y-1/2 animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>

        <div className="relative z-10 w-28 h-28 mb-4">
          <div className="absolute inset-0 border-4 border-blue-500/20 rounded-full"></div>
          <div className="absolute inset-0 border-[5px] border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="absolute inset-3 border-4 border-purple-500/20 rounded-full"></div>
          <div className="absolute inset-3 border-[4px] border-purple-500 border-b-transparent rounded-full animate-[spin_1.5s_linear_infinite_reverse]"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Sparkles
              className="w-8 h-8 text-blue-400 animate-pulse"
              strokeWidth={2}
            />
          </div>
        </div>

        <h2 className="relative z-10 text-[26px] font-bold text-white tracking-tight">
          Drafting Contract Sequence
        </h2>

        <div className="relative z-10 flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
          <p className="text-blue-200 text-[14px] font-medium tracking-wide transition-all min-w-[220px]">
            {steps[Math.min(loadingStep, steps.length - 1)]}
          </p>
        </div>

        <div className="relative z-10 w-72 h-1.5 bg-white/10 rounded-full overflow-hidden mt-6 shadow-[0_0_15px_rgba(59,95,229,0.3)]">
          <div
            className="h-full bg-gradient-to-r from-[#3B5FE5] to-purple-500 rounded-full transition-all duration-[1200ms] ease-out"
            style={{ width: `${Math.min((loadingStep + 1) * 20, 100)}%` }}
          ></div>
        </div>
      </div>
    );
  }

  // Pre-load a mock template if we just finished generating and have no real contractId
  const showMockGenerated =
    !contractId && !fetching && searchParams.get("generated") === "true";

  const toggleClause = (idx: number) => {
    const newSet = new Set(expandedClauses);
    if (newSet.has(idx)) {
      newSet.delete(idx);
    } else {
      newSet.add(idx);
    }
    setExpandedClauses(newSet);
  };

  if (fetching) {
    return (
      <div className="flex w-full h-[calc(100vh-70px)] items-center justify-center bg-white flex-col gap-4">
        <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
        <p className="text-slate-500 font-bold tracking-widest text-[12px] uppercase">
          Retrieving Analysis...
        </p>
      </div>
    );
  }

  return (
    <div className="flex w-full h-[calc(100vh-70px)] text-slate-900 bg-white">
      {/* Main Document Viewer Panel */}
      <div className="flex-[2] flex flex-col h-full border-r border-slate-200 relative">
        {/* Document Header */}
        <div className="flex items-center justify-between px-10 py-5 border-b border-slate-100 bg-white shrink-0">
          <div className="flex items-center gap-4">
            <h2 className="text-[11px] font-bold tracking-widest text-[#0B1437] opacity-60 uppercase">
              DOCUMENT /{" "}
              {contract?.original_filename ||
                contract?.markdown_file ||
                "No Document Selected"}
            </h2>
            <span
              className={`px-2.5 py-1.5 rounded-md text-[9px] font-bold tracking-widest uppercase transition-colors ${
                hasUnsavedChanges
                  ? "bg-amber-100 text-amber-700"
                  : "bg-[#Eef3FE] text-[#3B5FE5]"
              }`}
            >
              {hasUnsavedChanges
                ? "UNSAVED CHANGES"
                : contract?.status || "DRAFT"}
            </span>
            {pollingActive && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[9px] font-bold tracking-widest uppercase bg-blue-100 text-blue-700">
                <Loader2 className="w-3 h-3 animate-spin" /> LIVE POLLING
              </span>
            )}
          </div>
          <div className="flex items-center gap-6">
            <button
              onClick={handleExportPdf}
              disabled={!contractId || !htmlContent}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors disabled:opacity-50"
            >
              <Download className="w-4 h-4" /> Export PDF
            </button>
            <div className="w-px h-6 bg-slate-200"></div>
            <button className="text-slate-400 hover:text-slate-700 transition">
              <Undo2 className="w-4 h-4" />
            </button>
            <button className="text-slate-400 hover:text-slate-700 transition">
              <Redo2 className="w-4 h-4" />
            </button>
            <div className="w-px h-6 bg-slate-200"></div>
            <button
              onClick={handleSaveAndAnalyze}
              disabled={isAnalyzing || !contractId}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-bold shadow-md transition-all ${
                isAnalyzing
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed shadow-none"
                  : hasUnsavedChanges
                    ? "bg-[#3b5fe5] hover:bg-[#2a4ac2] text-white shadow-[0_4px_14px_rgba(59,95,229,0.3)]"
                    : "bg-[#0B1437] hover:bg-[#152458] text-white"
              }`}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" /> Save & Analyze
                </>
              )}
            </button>
          </div>
        </div>

        {/* Interactive Editor */}
        <div className="flex-1 overflow-y-auto px-16 py-12 relative bg-white custom-scrollbar">
          {!contractId ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-10">
              <FileText className="w-16 h-16 text-slate-100 mb-6" />
              <h3 className="text-[20px] font-bold text-slate-900 mb-2">
                No Document Loaded
              </h3>
              <p className="text-slate-500 text-[14px] max-w-sm">
                Please select a contract from your repository to view and
                analyze its content.
              </p>
            </div>
          ) : (
            <div className="max-w-[750px] mx-auto space-y-12">
              <DocumentEditor 
                contract={contract} 
                htmlContent={htmlContent} 
                onInput={handleContentChange} 
              />
              <div className="h-40"></div>
            </div>
          )}

          {!isChatOpen && (
            <button
              onClick={() => setIsChatOpen(true)}
              className="fixed bottom-10 right-[31%] xl:right-[35%] bg-black text-white px-6 py-4.5 rounded-xl flex items-center gap-3 shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:scale-105 transition-transform z-10 group border border-white/10 h-14"
            >
              <div className="w-6 h-6 rounded bg-green-500 flex items-center justify-center shrink-0 group-hover:bg-green-400 transition-colors">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="w-3.5 h-3.5 text-black"
                >
                  <path
                    d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span className="font-bold text-[14px]">Ask AI Jurist</span>
            </button>
          )}
        </div>
      </div>

      {isChatOpen ? (
        /* AI Assistant Right Panel */
        <div className="flex-1 min-w-[380px] max-w-[450px] bg-[#F4F7FB] overflow-y-auto h-full px-8 py-10 space-y-10 custom-scrollbar shadow-[-10px_0_30px_rgba(0,0,0,0.02)] relative animate-in slide-in-from-right duration-300">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#0B1437] flex items-center justify-center shrink-0 shadow-[0_8px_20px_rgba(11,20,55,0.2)]">
                <Bot
                  className="w-[22px] h-[22px] text-white"
                  strokeWidth={2.5}
                />
              </div>
              <div>
                <h3 className="font-extrabold text-[18px] text-slate-900 tracking-tight leading-none mb-1">
                  AI Assistant
                </h3>
                <span className="text-[10px] font-bold tracking-[0.15em] text-[#3B5FE5] uppercase">
                  Analysis Active
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsChatOpen(false)}
              className="w-10 h-10 rounded-full bg-slate-200/50 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-400"></div>
              <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500">
                Strategic Rationale
              </h4>
            </div>

            <div className="bg-white rounded-[20px] p-7 shadow-sm border border-slate-100">
              <p className="text-[13px] text-slate-700 leading-relaxed font-medium mb-6">
                {analysis?.analysis_summary ||
                  "Performing strategic evaluation of document structure..."}
              </p>

              <div className="space-y-3">
                {analysis?.recommended_actions
                  ?.slice(0, 3)
                  .map((rec: string, i: number) => (
                    <div
                      key={i}
                      className="bg-blue-50/80 rounded-xl p-4 border border-blue-100/50"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Info
                          className="w-4 h-4 text-[#3B5FE5]"
                          strokeWidth={2.5}
                        />
                        <span className="text-[10px] font-bold tracking-widest text-[#3B5FE5] uppercase">
                          Recommendation {i + 1}
                        </span>
                      </div>
                      <p className="text-[11.5px] text-blue-900/70 leading-relaxed font-medium ml-6">
                        {rec}
                      </p>
                    </div>
                  ))}
              </div>

              {/* Detailed Tiered Suggestions */}
              {analysis?.detailed_suggestions && (
                <div className="mt-8 pt-8 border-t border-slate-100 space-y-6">
                  <div className="flex items-center justify-between">
                    <h4 className="text-[11px] font-bold tracking-[0.12em] uppercase text-slate-400">
                      Strategic Enhancements
                    </h4>
                    <span className="text-[10px] font-bold text-blue-600">
                      {analysis.detailed_suggestions.improvement_potential}%
                      Potential
                    </span>
                  </div>

                  {[
                    {
                      tier: "tier_1_critical",
                      label: "Tier 1 / Critical",
                      color: "red",
                    },
                    {
                      tier: "tier_2_important",
                      label: "Tier 2 / Important",
                      color: "orange",
                    },
                    {
                      tier: "tier_3_recommended",
                      label: "Tier 3 / Recommended",
                      color: "blue",
                    },
                  ].map((t) => {
                    const items =
                      analysis.detailed_suggestions[
                        t.tier as keyof typeof analysis.detailed_suggestions
                      ];
                    if (!Array.isArray(items) || items.length === 0)
                      return null;

                    return (
                      <div key={t.tier} className="space-y-3">
                        <span
                          className={`text-[9px] font-black uppercase tracking-widest ${
                            t.color === "red"
                              ? "text-red-500"
                              : t.color === "orange"
                                ? "text-orange-500"
                                : "text-blue-500"
                          }`}
                        >
                          {t.label}
                        </span>
                        {items.map((item: any, i: number) => (
                          <div
                            key={i}
                            className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm hover:border-blue-200 transition-colors"
                          >
                            <h5 className="text-[12px] font-bold text-slate-900 mb-1">
                              {item.title}
                            </h5>
                            <p className="text-[11px] text-slate-500 leading-normal">
                              {item.purpose}
                            </p>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500 mb-2">
              Enhance Document
            </h4>

            {qaHistory.length > 0 && (
              <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1 custom-scrollbar">
                {qaHistory.slice(-4).map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-white rounded-xl p-4 border border-slate-200"
                  >
                    <p className="text-[10px] font-bold tracking-wider uppercase text-slate-400 mb-2">
                      Question
                    </p>
                    <p className="text-[12px] text-slate-800 mb-3">
                      {item.question}
                    </p>
                    <p className="text-[10px] font-bold tracking-wider uppercase text-blue-500 mb-2">
                      Answer
                    </p>
                    <p className="text-[12px] text-slate-700 leading-relaxed">
                      {item.answer}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="bg-white rounded-[20px] shadow-sm border border-slate-200 overflow-hidden focus-within:ring-2 focus-within:ring-[#3B5FE5] transition-all">
              <textarea
                placeholder="e.g., 'Make the indemnity clause more favorable to us'..."
                value={qaInput}
                onChange={(e) => setQaInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleAskQuestion();
                  }
                }}
                className="w-full h-[120px] resize-none outline-none text-[13px] text-slate-800 placeholder:text-slate-400 font-medium leading-[1.8] bg-transparent p-6 custom-scrollbar"
              />
              <div className="flex justify-end p-4 pt-0">
                <button
                  onClick={handleAskQuestion}
                  disabled={!contractId || qaLoading || !qaInput.trim()}
                  className="w-10 h-10 rounded-full bg-slate-100 hover:bg-[#3B5FE5] disabled:bg-slate-100 disabled:text-slate-300 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
                >
                  {qaLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send
                      className="w-4 h-4 -ml-0.5 mt-0.5"
                      strokeWidth={2.5}
                    />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Analysis Sidebar Right Panel */
        <div className="flex-1 min-w-[380px] max-w-[450px] bg-[#F4F7FB] overflow-y-auto h-full px-8 py-10 space-y-12 custom-scrollbar shadow-[-10px_0_30px_rgba(0,0,0,0.02)] animate-in slide-in-from-right duration-300">
          <div className="bg-[#0B1437] rounded-[24px] p-8 pb-10 text-white shadow-xl relative overflow-hidden group transition-all">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[60px] -translate-y-1/2 translate-x-1/3 pointer-events-none"></div>
            <div className="relative z-10 flex items-start justify-between mb-8">
              <h3 className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/90 w-2/3 leading-relaxed flex items-center gap-2">
                {isAnalyzing ? (
                  <span className="flex items-center gap-2 text-blue-300">
                    <Loader2 className="w-3 h-3 animate-spin" /> ANALYZING...
                  </span>
                ) : hasUnsavedChanges ? (
                  <span className="flex items-center gap-2 text-amber-300">
                    <AlertTriangle className="w-3 h-3" /> UNSAVED EDITS
                  </span>
                ) : (
                  "Contract Risk Score"
                )}
              </h3>
              <div className="flex items-center gap-2">
                <Info className="w-[18px] h-[18px] text-white/40 cursor-pointer hover:text-white transition-colors" />
              </div>
            </div>

            <div
              className={`relative z-10 transition-opacity duration-300 ${isAnalyzing ? "opacity-30 blur-[2px]" : hasUnsavedChanges ? "opacity-60" : "opacity-100"}`}
            >
              <div className="flex items-baseline gap-2 mb-8">
                <span className="text-[64px] font-bold tracking-tighter leading-none">
                  {analysis?.overall_risk_score || 0}
                </span>
                <span className="text-[15px] font-medium text-white/50 mb-2">
                  / 100
                </span>
              </div>
              <div className="w-full h-1.5 bg-white/10 rounded-full mb-8 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-[2000ms] ease-in-out ${
                    (analysis?.overall_risk_score || 0) > 70
                      ? "bg-red-400"
                      : (analysis?.overall_risk_score || 0) > 40
                        ? "bg-amber-400"
                        : "bg-blue-400"
                  }`}
                  style={{ width: `${analysis?.overall_risk_score || 0}%` }}
                ></div>
              </div>

              {/* Visual Issue Grid */}
              <div className="grid grid-cols-2 gap-3 mb-8">
                <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                  <span className="block text-[10px] font-bold text-white/40 uppercase mb-1">
                    Critical / High
                  </span>
                  <span className="text-[18px] font-bold text-red-300">
                    {(analysis?.critical_issues || 0) +
                      (analysis?.high_issues || 0)}
                  </span>
                </div>
                <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                  <span className="block text-[10px] font-bold text-white/40 uppercase mb-1">
                    Medium / Low
                  </span>
                  <span className="text-[18px] font-bold text-blue-200">
                    {(analysis?.medium_issues || 0) +
                      (analysis?.low_issues || 0)}
                  </span>
                </div>
              </div>

              <p className="text-[12px] text-white/70 leading-[1.6] font-medium w-[90%]">
                {analysis?.overall_risk_score > 60
                  ? "DeepAgents flagged this as high risk. Multiple unfavorable clauses identified requiring negotiation."
                  : "Risk profile appears manageable. Primarily standard market terms detected."}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500">
                Clauses Analysis
              </h3>
              <span className="px-3 py-1.5 bg-[#Edf2FF] text-[#3B5FE5] rounded-md text-[9px] font-bold tracking-widest uppercase">
                {analysis?.clauses?.length || 0} Detected
              </span>
            </div>

            {analysis?.clauses?.map((clause: any, i: number) => {
              const isExpanded = expandedClauses.has(i);

              return (
                <div key={i} className="group/clause flex flex-col space-y-4">
                  <div
                    onClick={() => toggleClause(i)}
                    className="bg-white rounded-[16px] p-6 shadow-sm border border-slate-100 hover:border-blue-200 transition-all duration-300 cursor-pointer"
                  >
                    <div className="flex gap-4">
                      <div
                        className={`w-8 h-8 rounded-full ${clause.severity === "critical" || clause.severity === "high" ? "bg-red-100/50 text-red-500" : "bg-green-100/50 text-green-500"} flex items-center justify-center shrink-0 mt-0.5`}
                      >
                        {clause.severity === "critical" ||
                        clause.severity === "high" ? (
                          <AlertTriangle
                            className="w-4 h-4"
                            strokeWidth={2.5}
                          />
                        ) : (
                          <CheckCircle2 className="w-4 h-4" strokeWidth={2.5} />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2.5 gap-2">
                          <h4 className="font-bold text-[14px] text-slate-900 leading-none capitalize truncate">
                            {clause.clause_type?.replaceAll("_", " ")}
                          </h4>
                          <span
                            className={`px-2 py-1 ${getSeverityBg(clause.severity)} ${getSeverityColor(clause.severity)} rounded text-[9px] font-bold tracking-widest uppercase shrink-0`}
                          >
                            {clause.severity}
                          </span>
                        </div>
                        <p className="text-[12px] text-slate-500 leading-relaxed font-medium line-clamp-1 group-hover/clause:line-clamp-none transition-all">
                          {clause.risk_description || clause.raw_text}
                        </p>

                        {isExpanded && (
                          <div className="mt-6 pt-5 border-t border-slate-50 space-y-6 animate-in fade-in slide-in-from-top-2 duration-300">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                  Deep Reasoning
                                </span>
                                <span className="text-[10px] font-bold text-blue-500">
                                  {clause.confidence_score}% Confidence
                                </span>
                              </div>
                              <div className="bg-slate-50 rounded-xl p-4">
                                <p className="text-[12px] text-slate-700 leading-relaxed font-medium whitespace-pre-line">
                                  {clause.legal_reasoning ||
                                    "No automated reasoning available for this section."}
                                </p>
                              </div>
                            </div>

                            <div className="space-y-2">
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                Grounding
                              </span>
                              <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 rounded-lg border border-blue-100/50">
                                <Globe className="w-3.5 h-3.5 text-blue-500" />
                                <span className="text-[11px] font-bold text-blue-800">
                                  {clause.applicable_statute ||
                                    "Indian Contract Act 1872"}{" "}
                                  / {clause.statute_section}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
