"use client";

import { useState, useRef, useEffect } from "react";
import { 
  Undo2, Redo2, Save, Info, CheckCircle2, AlertTriangle, 
  Globe, Plus, MessageSquare, Loader2, Sparkles, Bot, Send, History, X 
} from "lucide-react";
import toast from "react-hot-toast";

export default function TenantFilesPage() {
  const [isGenerating, setIsGenerating] = useState(() => {
    if (typeof window !== 'undefined') {
      return new URLSearchParams(window.location.search).get('generating') === 'true';
    }
    return false;
  });
  const [loadingStep, setLoadingStep] = useState(0);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    if (isGenerating) {
      const interval = setInterval(() => {
        setLoadingStep(s => s + 1);
      }, 1200);
      
      const timeout = setTimeout(() => {
        clearInterval(interval);
        setIsGenerating(false);
        if (typeof window !== 'undefined') {
          window.history.replaceState(null, '', window.location.pathname);
        }
      }, 5500);

      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }
  }, [isGenerating]);

  const handleContentChange = () => {
    if (!hasUnsavedChanges) {
      setHasUnsavedChanges(true); // Registers that the document was modified but not yet analyzed
    }
  };

  const handleSaveAndAnalyze = () => {
    if (!hasUnsavedChanges) {
      toast.success("Document is already up to date.");
      return;
    }

    setIsAnalyzing(true);
    setHasUnsavedChanges(false);
    
    // Simulate a complex API call to analyze contract risk and clauses
    setTimeout(() => {
      setIsAnalyzing(false);
      toast.success("Analysis complete. Risk score updated!");
    }, 2500);
  };

  if (isGenerating) {
    const steps = [
      "Structuring legal frameworks...",
      "Aligning jurisdiction statutes...",
      "Cross-referencing liability caps...",
      "Applying strict compliance...",
      "Finalizing document blueprint..."
    ];

    return (
      <div className="flex w-full h-[calc(100vh-70px)] bg-[#0B1437] items-center justify-center relative overflow-hidden flex-col gap-6">
        {/* Abstract glowing orbs */}
        <div className="absolute w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute w-[400px] h-[400px] bg-purple-600/20 rounded-full blur-[100px] -translate-x-1/2 translate-y-1/2 animate-pulse" style={{ animationDelay: '1s' }}></div>

        <div className="relative z-10 w-28 h-28 mb-4">
          <div className="absolute inset-0 border-4 border-blue-500/20 rounded-full"></div>
          <div className="absolute inset-0 border-[5px] border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="absolute inset-3 border-4 border-purple-500/20 rounded-full"></div>
          <div className="absolute inset-3 border-[4px] border-purple-500 border-b-transparent rounded-full animate-[spin_1.5s_linear_infinite_reverse]"></div>
          <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-blue-400 animate-pulse" strokeWidth={2}/>
          </div>
        </div>

        <h2 className="relative z-10 text-[26px] font-bold text-white tracking-tight">Drafting Contract Sequence</h2>
        
        <div className="relative z-10 flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
          <p className="text-blue-200 text-[14px] font-medium tracking-wide transition-all min-w-[220px]">
             {steps[Math.min(loadingStep, steps.length - 1)]}
          </p>
        </div>

        <div className="relative z-10 w-72 h-1.5 bg-white/10 rounded-full overflow-hidden mt-6 shadow-[0_0_15px_rgba(59,95,229,0.3)]">
           <div className="h-full bg-gradient-to-r from-[#3B5FE5] to-purple-500 rounded-full transition-all duration-[1200ms] ease-out" style={{ width: `${Math.min((loadingStep + 1) * 20, 100)}%` }}></div>
        </div>
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
            <h2 className="text-[11px] font-bold tracking-widest text-[#0B1437] opacity-60 uppercase">DOCUMENT / MSA_2024_GLOBAL_TECH.PDF</h2>
            <span className={`px-2.5 py-1.5 rounded-md text-[9px] font-bold tracking-widest uppercase transition-colors ${
              hasUnsavedChanges ? 'bg-amber-100 text-amber-700' : 'bg-[#Eef3FE] text-[#3B5FE5]'
            }`}>
              {hasUnsavedChanges ? "UNSAVED CHANGES" : "DRAFT V4"}
            </span>
          </div>
          <div className="flex items-center gap-6">
            <button className="text-slate-400 hover:text-slate-700 transition"><Undo2 className="w-4 h-4" /></button>
            <button className="text-slate-400 hover:text-slate-700 transition"><Redo2 className="w-4 h-4" /></button>
            <div className="w-px h-6 bg-slate-200"></div>
            <button 
              onClick={handleSaveAndAnalyze}
              disabled={isAnalyzing}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-bold shadow-md transition-all ${
                isAnalyzing 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed shadow-none' 
                  : hasUnsavedChanges 
                    ? 'bg-[#3b5fe5] hover:bg-[#2a4ac2] text-white shadow-[0_4px_14px_rgba(59,95,229,0.3)]' 
                    : 'bg-[#0B1437] hover:bg-[#152458] text-white'
              }`}
            >
              {isAnalyzing ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
              ) : (
                <><Save className="w-4 h-4" /> Save & Analyze</>
              )}
            </button>
          </div>
        </div>

        {/* Document Content Scrollable Area (Interactive Editor) */}
        <div className="flex-1 overflow-y-auto px-16 py-12 relative bg-white custom-scrollbar">
          <div className="max-w-[750px] mx-auto space-y-12">
            
            <div 
              contentEditable 
              suppressContentEditableWarning 
              onInput={handleContentChange}
              className="outline-none focus:bg-slate-50/50 p-4 -mx-4 rounded-2xl transition-colors"
            >
              <h1 className="text-[32px] font-bold text-[#0B1437] mb-6 tracking-tight">MASTER SERVICE AGREEMENT</h1>
              <p className="text-[14px] text-slate-600 leading-[1.8] font-medium">
                THIS MASTER SERVICE AGREEMENT (the "Agreement") is dated as of October 24, 2024 (the "Effective Date").
              </p>
            </div>

            <div 
              contentEditable 
              suppressContentEditableWarning 
              onInput={handleContentChange}
              className="outline-none focus:bg-slate-50/50 p-4 -mx-4 rounded-2xl transition-colors"
            >
              <p className="text-[10px] font-bold tracking-[0.15em] text-[#3B5FE5] uppercase mb-4" contentEditable={false}>SECTION 4.2 / LIABILITY</p>
              <p className="text-[15px] text-slate-700 leading-[2] font-medium">
                Neither Party shall be liable to the other for any indirect, incidental, special, or consequential damages, including loss of profits, even if advised of the possibility of such damages. The total cumulative liability of Company under this Agreement shall not exceed the total fees paid by Client during the six (6) months preceding the event giving rise to the claim.
              </p>
            </div>

            <div className={`border-l-[4px] border-green-400 bg-green-50/50 -mx-8 px-8 py-8 rounded-r-2xl shadow-[inset_0_4px_20px_rgba(74,222,128,0.05)] relative transition-all duration-500 ${isAnalyzing ? 'animate-pulse bg-green-100/30 border-green-300' : ''}`}>
              <p className="text-[10px] font-bold tracking-[0.15em] text-[#3B5FE5] uppercase mb-5">SECTION 5.0 / INTELLECTUAL PROPERTY</p>
              <div 
                contentEditable 
                suppressContentEditableWarning 
                onInput={handleContentChange}
                className="outline-none focus:bg-white/60 p-2 -mx-2 rounded-xl transition-colors mb-6"
              >
                <p className="text-[15px] text-slate-800 leading-[2] font-semibold">
                  Any and all Intellectual Property Rights in the Deliverables shall vest in the Company upon creation. Client is granted a non-exclusive, non-transferable license to use the Deliverables solely for its internal business purposes during the term of this Agreement.
                </p>
              </div>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-100/80 text-green-700 text-[9px] font-bold tracking-widest uppercase rounded transition-opacity ${isAnalyzing ? 'opacity-50' : 'opacity-100'}`}>
                {isAnalyzing ? <Loader2 className="w-3 h-3 animate-spin"/> : null}
                AUTO-ANALYSIS: FAVORABLE
              </span>
            </div>

            <div 
              contentEditable 
              suppressContentEditableWarning 
              onInput={handleContentChange}
              className="outline-none focus:bg-slate-50/50 p-4 -mx-4 rounded-2xl transition-colors"
            >
              <p className="text-[10px] font-bold tracking-[0.15em] text-[#3B5FE5] uppercase mb-4" contentEditable={false}>SECTION 8.1 / TERMINATION FOR CONVENIENCE</p>
              <p className="text-[15px] text-slate-700 leading-[2] font-medium">
                Either party may terminate this Agreement without cause, by providing ninety (90) days' written notice to the other party. In the event of such termination, Client shall pay Company for all Services performed up to the termination date.
              </p>
            </div>
            
            <div className="h-40"></div>
            
          </div>

          {/* Floating Ask AI Button (only visible if chat is not already open) */}
          {!isChatOpen && (
            <button 
              onClick={() => setIsChatOpen(true)}
              className="fixed bottom-10 right-[31%] xl:right-[35%] bg-black text-white px-6 py-4.5 rounded-xl flex items-center gap-3 shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:scale-105 transition-transform z-10 group border border-white/10 h-14"
            >
              <div className="w-6 h-6 rounded bg-green-500 flex items-center justify-center shrink-0 group-hover:bg-green-400 transition-colors">
                <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-black">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
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
           
           {/* AI Header */}
           <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[#0B1437] flex items-center justify-center shrink-0 shadow-[0_8px_20px_rgba(11,20,55,0.2)]">
                   <Bot className="w-[22px] h-[22px] text-white" strokeWidth={2.5}/>
                </div>
                <div>
                   <h3 className="font-extrabold text-[18px] text-slate-900 tracking-tight leading-none mb-1">AI Assistant</h3>
                   <span className="text-[10px] font-bold tracking-[0.15em] text-[#3B5FE5] uppercase">Analysis Active</span>
                </div>
              </div>
              <button 
                onClick={() => setIsChatOpen(false)}
                className="w-10 h-10 rounded-full bg-slate-200/50 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
           </div>

           {/* Strategic Rationale */}
           <div className="space-y-4">
              <div className="flex items-center gap-2 mb-2">
                 <div className="w-1.5 h-1.5 rounded-full bg-slate-400"></div>
                 <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500">Strategic Rationale</h4>
              </div>
              
              <div className="bg-white rounded-[20px] p-7 shadow-sm border border-slate-100">
                 <p className="text-[13px] text-slate-700 leading-relaxed font-medium mb-6">
                    This agreement structure strongly protects your core intellectual property while providing a standardized framework for SOW-based engagements. The balanced liability terms reduce friction in closing.
                 </p>

                 <div className="space-y-3">
                    <div className="bg-green-50/80 rounded-xl p-4 border border-green-100/50">
                       <div className="flex items-center gap-2 mb-2">
                          <CheckCircle2 className="w-4 h-4 text-green-600" strokeWidth={2.5}/>
                          <span className="text-[10px] font-bold tracking-widest text-green-700 uppercase">Section 5 • Favorable</span>
                       </div>
                       <p className="text-[11.5px] text-green-900/70 leading-relaxed font-medium ml-6">
                          Retains broad IP rights for pre-existing tools, minimizing future development conflicts.
                       </p>
                    </div>
                    
                    <div className="bg-blue-50/80 rounded-xl p-4 border border-blue-100/50">
                       <div className="flex items-center gap-2 mb-2">
                          <Info className="w-4 h-4 text-[#3B5FE5]" strokeWidth={2.5}/>
                          <span className="text-[10px] font-bold tracking-widest text-[#3B5FE5] uppercase">Section 2 • Pending AI Review</span>
                       </div>
                       <p className="text-[11.5px] text-blue-900/70 leading-relaxed font-medium ml-6">
                          Manual edits detected on payment terms. Analyzing impact on cash flow projections...
                       </p>
                    </div>
                 </div>
              </div>
           </div>

           {/* Enhance Document Chat */}
           <div className="space-y-4">
              <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500 mb-2">Enhance Document</h4>
              
              <div className="bg-white rounded-[20px] shadow-sm border border-slate-200 overflow-hidden focus-within:ring-2 focus-within:ring-[#3B5FE5] transition-all">
                 <textarea 
                    placeholder="e.g., 'Make the indemnity clause more favorable to us' or 'Add a force majeure section...'"
                    className="w-full h-[120px] resize-none outline-none text-[13px] text-slate-800 placeholder:text-slate-400 font-medium leading-[1.8] bg-transparent p-6 custom-scrollbar"
                 />
                 <div className="flex justify-end p-4 pt-0">
                    <button className="w-10 h-10 rounded-full bg-slate-100 hover:bg-[#3B5FE5] text-slate-400 hover:text-white flex items-center justify-center transition-colors">
                       <Send className="w-4 h-4 -ml-0.5 mt-0.5" strokeWidth={2.5}/>
                    </button>
                 </div>
              </div>
           </div>

           {/* Version History */}
           <div className="space-y-8 pt-4 pb-12">
              <div className="flex items-center gap-2 mb-6">
                 <History className="w-[18px] h-[18px] text-slate-500" strokeWidth={2.5}/>
                 <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500">Version History</h4>
              </div>

              <div className="relative pl-[1px] space-y-8">
                 {/* Vertical Line */}
                 <div className="absolute left-[5px] top-4 bottom-4 w-[2px] bg-slate-200/60 rounded-full"></div>

                 {/* Item 1 */}
                 <div className="relative flex gap-5 items-start">
                    <div className="w-[12px] h-[12px] rounded-full bg-white border-[3px] border-[#3B5FE5] shadow-[0_0_0_5px_#F4F7FB] z-10 mt-1 shrink-0"></div>
                    <div>
                       <h5 className="text-[13px] font-bold text-slate-900 mb-1.5 leading-none">Unsaved Edits</h5>
                       <p className="text-[11.5px] text-slate-500 font-medium">Section 2 modified (Payment Terms)</p>
                    </div>
                 </div>

                 {/* Item 2 */}
                 <div className="relative flex gap-5 items-start">
                    <div className="w-[12px] h-[12px] rounded-full bg-white border-[3px] border-slate-200 shadow-[0_0_0_5px_#F4F7FB] z-10 mt-1 shrink-0"></div>
                    <div>
                       <h5 className="text-[13px] font-medium text-slate-600 mb-1.5 leading-none">Initial Generation</h5>
                       <p className="text-[11px] text-slate-400 font-medium">Oct 24, 2023 • 10:42 AM</p>
                    </div>
                 </div>
              </div>
           </div>

        </div>
      ) : (
        /* Analysis Sidebar Right Panel (Old Style) */
        <div className="flex-1 min-w-[380px] max-w-[450px] bg-[#F4F7FB] overflow-y-auto h-full px-8 py-10 space-y-12 custom-scrollbar shadow-[-10px_0_30px_rgba(0,0,0,0.02)] animate-in slide-in-from-right duration-300">
           
           {/* Risk Score Card */}
           <div className="bg-[#0B1437] rounded-[24px] p-8 pb-10 text-white shadow-xl relative overflow-hidden group transition-all">
              <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[60px] -translate-y-1/2 translate-x-1/3 pointer-events-none"></div>
              
              <div className="relative z-10 flex items-start justify-between mb-8">
                 <h3 className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/90 w-2/3 leading-relaxed flex items-center gap-2">
                   {isAnalyzing ? (
                     <span className="flex items-center gap-2 text-blue-300">
                       <Loader2 className="w-3 h-3 animate-spin"/> ANALYZING EDITS...
                     </span>
                   ) : hasUnsavedChanges ? (
                     <span className="flex items-center gap-2 text-amber-300">
                       <AlertTriangle className="w-3 h-3" /> OUT OF SYNC
                     </span>
                   ) : (
                     "Contract Risk Score"
                   )}
                 </h3>
                 <Info className="w-[18px] h-[18px] text-white/40 cursor-pointer hover:text-white transition-colors" />
              </div>

              <div className={`relative z-10 transition-opacity duration-300 ${isAnalyzing ? 'opacity-30 blur-[2px]' : hasUnsavedChanges ? 'opacity-60' : 'opacity-100'}`}>
                <div className="flex items-baseline gap-2 mb-8">
                   <span className="text-[64px] font-bold tracking-tighter leading-none">74</span>
                   <span className="text-[15px] font-medium text-white/50 mb-2">/ 100</span>
                </div>

                <div className="w-full h-1.5 bg-white/10 rounded-full mb-8 overflow-hidden">
                   <div className="h-full bg-green-400 rounded-full transition-all duration-[2000ms] ease-in-out" style={{ width: isAnalyzing ? '0%' : '74%' }}></div>
                </div>

                <p className="text-[12px] text-white/70 leading-[1.6] font-medium w-[90%]">
                   Analysis suggests a <span className="text-green-400 font-bold">Moderate Risk</span> profile due to jurisdictional complexities in Section 12.4.
                </p>
              </div>
           </div>

           {/* Clauses Analysis */}
           <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                 <h3 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500">Clauses Analysis</h3>
                 <span className="px-3 py-1.5 bg-[#Edf2FF] text-[#3B5FE5] rounded-md text-[9px] font-bold tracking-widest uppercase">8 Detected</span>
              </div>

              {/* Clause 1 */}
              <div className="bg-white rounded-[16px] p-7 shadow-sm border border-slate-100 hover:-translate-y-0.5 transition-transform duration-300">
                 <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-green-100/50 flex items-center justify-center shrink-0 mt-0.5">
                       <CheckCircle2 className="w-4 h-4 text-green-500" strokeWidth={2.5} />
                    </div>
                    <div className="flex-1">
                       <div className="flex items-center justify-between mb-3 gap-2">
                          <h4 className="font-bold text-[14px] text-slate-900 leading-none">IP Rights Ownership</h4>
                          <span className="px-2 py-1 bg-green-50 text-green-600 rounded text-[9px] font-bold tracking-widest uppercase shrink-0">Company Favor</span>
                       </div>
                       <p className="text-[12px] text-slate-500 leading-relaxed font-medium">
                          Section 5.0 ensures full ownership of deliverables.
                       </p>
                    </div>
                 </div>
              </div>

              {/* Clause 2 */}
              <div className="bg-white rounded-[16px] p-7 shadow-sm border border-slate-100 hover:-translate-y-0.5 transition-transform duration-300">
                 <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-red-100/50 flex items-center justify-center shrink-0 mt-0.5">
                       <AlertTriangle className="w-4 h-4 text-red-500" strokeWidth={2.5} />
                    </div>
                    <div className="flex-1">
                       <div className="flex items-center justify-between mb-3 gap-2">
                          <h4 className="font-bold text-[14px] text-slate-900 leading-none">Limitation of Liability</h4>
                          <span className="px-2 py-1 bg-red-50 text-red-600 rounded text-[9px] font-bold tracking-widest uppercase shrink-0">Client Favor</span>
                       </div>
                       <p className="text-[12px] text-slate-500 leading-relaxed font-medium">
                          Section 4.2 caps damages at 6 months of fees. Risk of under-coverage.
                       </p>
                    </div>
                 </div>
              </div>
           </div>

           {/* Critical Warnings */}
           <div className="space-y-4">
              <h3 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500 mb-4">Critical Warnings</h3>
              
              <div className="bg-red-50/50 rounded-[16px] p-7 border border-red-100">
                 <div className="flex gap-4 mb-6">
                    <Globe className="w-[18px] h-[18px] text-red-600 shrink-0 mt-0.5" strokeWidth={2.5} />
                    <div>
                       <h4 className="font-bold text-[14px] text-red-600 mb-2.5">Offshore Jurisdiction</h4>
                       <p className="text-[12px] text-red-900/60 leading-relaxed font-medium">
                          Cayman Islands governance may complicate enforcement of non-competes in US territories.
                       </p>
                    </div>
                 </div>
                 <button className="w-full py-3.5 bg-transparent border-[1.5px] border-red-200 hover:border-red-300 rounded-lg text-[10px] font-bold text-red-600 tracking-widest uppercase transition-colors">
                    Draft Amendment
                 </button>
              </div>
           </div>

           {/* Suggested Additions */}
           <div className="space-y-4 pb-12">
              <h3 className="text-[11px] font-bold tracking-[0.15em] uppercase text-slate-500 mb-4">Suggested Additions</h3>
              
              <div className="bg-[#Ecf1fe]/50 rounded-[16px] p-7 border border-[#Ecf1fe] group hover:bg-[#Ecf1fe] transition-colors cursor-pointer">
                 <div className="flex items-center justify-between mb-3">
                    <h4 className="font-bold text-[14px] text-slate-900 group-hover:text-[#3B5FE5] transition-colors">Force Majeure Clause</h4>
                    <div className="w-[22px] h-[22px] rounded-full bg-white flex items-center justify-center shadow-sm">
                       <Plus className="w-3.5 h-3.5 text-slate-500" strokeWidth={2.5} />
                    </div>
                 </div>
                 <p className="text-[12px] text-slate-500 leading-relaxed font-medium">
                    Currently missing standard protections for unforeseeable events.
                 </p>
              </div>
           </div>

        </div>
      )}
    </div>
  );
}
