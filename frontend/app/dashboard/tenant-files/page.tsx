"use client";

import { useState, useEffect, useCallback, useRef } from "react";
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

const DocumentEditor = React.memo(
  function DocumentEditor({ contract, htmlContent, onInput }: any) {
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
  },
  (prev, next) => {
    return (
      prev.htmlContent === next.htmlContent &&
      prev.contract?.original_filename === next.contract?.original_filename &&
      prev.contract?.markdown_file === next.contract?.markdown_file
    );
  },
);

DocumentEditor.displayName = "DocumentEditor";

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
    Array<{
      id: string;
      question: string;
      answer: string;
      answerHtml: string;
      isPending: boolean;
      isError: boolean;
    }>
  >([]);
  const [pollingActive, setPollingActive] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState<Set<number>>(
    new Set(),
  );
  const qaThreadRef = useRef<HTMLDivElement | null>(null);
  const qaInputRef = useRef<HTMLTextAreaElement | null>(null);

  const renderMarkdownToHtml = useCallback(async (content: string) => {
    try {
      marked.setOptions({
        gfm: true,
        breaks: true,
      });

      const rendered = marked.parse(content);
      const renderedHtml =
        typeof rendered === "string" ? rendered : await rendered;
      return DOMPurify.sanitize(renderedHtml);
    } catch (err) {
      const escaped = DOMPurify.sanitize(content, { ALLOWED_TAGS: [] });
      return `<p>${escaped}</p>`;
    }
  }, []);

  useEffect(() => {
    async function parseMarkdown() {
      const content =
        analysis?.analysis_markdown ||
        "Analysis markdown will appear here once processing is complete.";
      const sanitized = await renderMarkdownToHtml(content);
      setHtmlContent(sanitized);
    }
    parseMarkdown();
  }, [analysis?.analysis_markdown, renderMarkdownToHtml]);

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
    setHasUnsavedChanges((prev) => {
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
    const pendingId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;

    // Move the prompt into the thread immediately and clear composer text.
    setQaInput("");

    setQaHistory((prev) => [
      ...prev,
      {
        id: pendingId,
        question,
        answer: "",
        answerHtml: "",
        isPending: true,
        isError: false,
      },
    ]);

    setQaLoading(true);

    try {
      const response = await apiClient.askContractQuestion(
        contractId,
        question,
      );
      const answerText =
        response?.answer || response?.error || "No answer returned.";
      const answerHtml = await renderMarkdownToHtml(answerText);

      setQaHistory((prev) =>
        prev.map((item) =>
          item.id === pendingId
            ? {
                ...item,
                answer: answerText,
                answerHtml,
                isPending: false,
                isError: false,
              }
            : item,
        ),
      );
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to get AI answer.");
      const errorText = "Request failed. Please try again.";
      const errorHtml = await renderMarkdownToHtml(errorText);

      setQaHistory((prev) =>
        prev.map((item) =>
          item.id === pendingId
            ? {
                ...item,
                answer: errorText,
                answerHtml: errorHtml,
                isPending: false,
                isError: true,
              }
            : item,
        ),
      );
    } finally {
      setQaLoading(false);
    }
  };

  useEffect(() => {
    if (!isChatOpen || !qaThreadRef.current) return;

    qaThreadRef.current.scrollTo({
      top: qaThreadRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [qaHistory, qaLoading, isChatOpen]);

  const quickPrompts = [
    "Rewrite indemnity to be vendor-friendly and capped.",
    "Summarize top 3 negotiation priorities in plain language.",
    "Flag hidden termination and auto-renewal risks.",
  ];

  const handleApplyQuickPrompt = (prompt: string) => {
    setQaInput(prompt);
    qaInputRef.current?.focus();
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
        margin: 0.7,
        filename: `${contract?.company_name?.replace(/\s+/g, "_") || "contract"}_document.pdf`,
        image: { type: "jpeg" as const, quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: {
          unit: "in" as const,
          format: "letter" as const,
          orientation: "portrait" as const,
        },
      };

      await html2pdf()
        .set(opt as any)
        .from(element)
        .save();
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
  const isTemplateGenerationView = searchParams.get("generated") === "true";

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
        <div className="flex-1 min-w-[380px] max-w-[450px] h-full bg-gradient-to-b from-[#F4F7FB] to-[#EEF3FB] shadow-[-10px_0_30px_rgba(0,0,0,0.02)] relative animate-in slide-in-from-right duration-300 border-l border-slate-200/60 flex flex-col">
          <div className="px-6 pt-6 pb-4 border-b border-slate-200/70 bg-white/70 backdrop-blur-xl shrink-0">
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
                <span className="text-[10px] font-bold tracking-[0.15em] text-[#3B5FE5] uppercase inline-flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Analysis Active
                </span>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full bg-white border border-slate-200 text-[10px] font-semibold text-slate-500">
                  {qaHistory.length} turns
                </span>
                <button
                  onClick={() => setIsChatOpen(false)}
                  className="w-10 h-10 rounded-full bg-slate-200/50 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="px-6 pt-4 pb-5 flex-1 min-h-0 flex flex-col gap-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-[11px] font-bold tracking-[0.14em] uppercase text-slate-500">
                Chat
              </span>
              <button
                type="button"
                onClick={() => setQaInput("")}
                className="text-[10px] font-semibold text-slate-400 hover:text-slate-600 transition-colors"
              >
                Clear Input
              </button>
            </div>

            <div
              ref={qaThreadRef}
              className={`flex-1 min-h-0 custom-scrollbar px-1 ${qaHistory.length > 0 ? "overflow-y-auto space-y-6" : "overflow-hidden"}`}
            >
              {qaHistory.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center px-5">
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-sm border border-slate-200 flex items-center justify-center mb-4">
                    <Bot className="w-6 h-6 text-[#3B5FE5]" />
                  </div>
                  <h4 className="text-[15px] font-bold text-slate-800 mb-1.5">
                    How can I help you?
                  </h4>
                  <p className="text-[12px] text-slate-500 mb-8 max-w-[260px] leading-relaxed">
                    Ask questions about clauses, request rewrites, or clarify legal terminology.
                  </p>
                  <div className="flex flex-col gap-2 w-full max-w-[320px]">
                    {quickPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => handleApplyQuickPrompt(prompt)}
                        className="w-full px-4 py-3 rounded-xl bg-white border border-slate-200 hover:border-[#3B5FE5]/30 hover:bg-blue-50/50 text-[11px] font-medium text-slate-600 transition-all text-left shadow-sm flex items-center justify-between group"
                      >
                        <span className="truncate pr-2">{prompt}</span>
                        <div className="w-5 h-5 rounded-md bg-slate-100 flex items-center justify-center group-hover:bg-[#3B5FE5] group-hover:text-white transition-colors shrink-0">
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-5 pb-2">
                  {qaHistory.map((item) => (
                    <React.Fragment key={item.id}>
                      <div className="flex justify-end pl-10">
                        <div className="bg-[#0B1437] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm border border-[#1C2B62]">
                          <p className="text-[13px] leading-relaxed whitespace-pre-wrap">
                            {item.question}
                          </p>
                        </div>
                      </div>

                      <div className="flex justify-start pr-4">
                        <div className="flex gap-3 w-full">
                          <div className="w-7 h-7 rounded-full bg-white border border-slate-200 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                            <Bot className="w-4 h-4 text-[#3B5FE5]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            {item.isPending ? (
                              <div className="flex items-center gap-2 text-[13px] text-slate-500 h-8">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Drafting answer...</span>
                              </div>
                            ) : (
                              <div
                                className={`contract-markdown markdown-body max-w-none text-[13px] leading-relaxed bg-white rounded-2xl rounded-tl-sm px-4 py-3.5 border border-slate-200 shadow-sm ${item.isError ? "text-red-600" : "text-slate-700"}`}
                                dangerouslySetInnerHTML={{
                                  __html: item.answerHtml,
                                }}
                              />
                            )}
                          </div>
                        </div>
                      </div>
                    </React.Fragment>
                  ))}
                </div>
              )}
            </div>

            <div className="shrink-0 flex flex-col gap-3 mt-2">
              {qaHistory.length > 0 && (
                <div className="flex flex-wrap gap-2 px-1">
                  {quickPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => handleApplyQuickPrompt(prompt)}
                      className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-[#3B5FE5]/30 hover:bg-blue-50/50 text-[10px] font-medium text-slate-600 transition-colors shadow-sm"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              )}

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden focus-within:ring-2 focus-within:ring-[#3B5FE5] transition-all">
              <textarea
                ref={qaInputRef}
                placeholder="Ask for edits, risk interpretation, or fallback language..."
                value={qaInput}
                onChange={(e) => setQaInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleAskQuestion();
                  }
                }}
                className="w-full h-[104px] resize-none outline-none text-[13px] text-slate-800 placeholder:text-slate-400 font-medium leading-[1.7] bg-transparent p-5 custom-scrollbar"
              />
              <div className="flex items-center justify-between px-4 pb-4">
                <span className="text-[10px] text-slate-400 font-medium">
                  Enter to send, Shift+Enter for newline
                </span>
                <button
                  onClick={handleAskQuestion}
                  disabled={!contractId || qaLoading || !qaInput.trim()}
                  className="h-10 px-4 rounded-xl bg-[#0B1437] hover:bg-[#152458] disabled:bg-slate-200 disabled:text-slate-400 text-white flex items-center justify-center gap-2 transition-colors text-[12px] font-semibold"
                >
                  {qaLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" strokeWidth={2.5} />
                      Send
                    </>
                  )}
                </button>
              </div>
              </div>
            </div>
          </div>
        </div>
      ) : isTemplateGenerationView || showMockGenerated ? (
        <div className="flex-1 min-w-[380px] max-w-[450px] bg-[#F4F7FB] overflow-y-auto h-full px-8 py-10 space-y-6 custom-scrollbar shadow-[-10px_0_30px_rgba(0,0,0,0.02)] animate-in slide-in-from-right duration-300">
          <div className="bg-white rounded-[24px] p-8 border border-slate-200 shadow-sm">
            <h3 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500 mb-4">
              Template Draft Mode
            </h3>
            <p className="text-[13px] text-slate-700 leading-relaxed">
              This contract was generated from templates. Risk score and
              clause-level analysis are intentionally hidden in this mode.
            </p>
          </div>

          <div className="bg-white rounded-[24px] p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-[11px] font-bold tracking-[0.14em] uppercase text-slate-500">
              Suggested Next Step
            </h4>
            <p className="text-[12px] text-slate-600 leading-relaxed">
              Use the AI Assistant to refine clauses and language. Once saved
              and analyzed as a tracked contract, risk metrics will appear in
              the analysis view.
            </p>
          </div>
        </div>
      ) : (analysis?.overall_risk_score > 0 || (analysis?.clauses && analysis?.clauses.length > 0)) ? (
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
      ) : null}
    </div>
  );
}
