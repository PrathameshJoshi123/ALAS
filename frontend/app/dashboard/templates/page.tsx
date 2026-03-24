"use client";

import { Sparkles, Paperclip, ArrowRight, History, FileText, Gavel, Lightbulb, Command, X } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function TemplatesPage() {
  const [prompt, setPrompt] = useState("");
  const [showTip, setShowTip] = useState(true);
  const router = useRouter();

  const popularStartingPoints = [
    "SaaS Terms of Service",
    "Commercial Lease",
    "Consulting Agreement",
    "Master Services Agreement",
    "IP Assignment"
  ];

  return (
    <div className="flex-1 w-full h-[calc(100vh-70px)] bg-[#F8FAFC] overflow-y-auto px-10 py-12 custom-scrollbar">
      <div className="max-w-[1100px] mx-auto pb-20">
        
        {/* Header Section */}
        <div className="mb-12 text-center flex flex-col items-center">
          <span className="inline-block px-3.5 py-1.5 bg-[#E8EFFF] text-[#3B5FE5] rounded-full text-[10px] font-bold tracking-widest uppercase mb-6 shadow-sm">
            Drafting Engine V2.4
          </span>
          <h1 className="text-[46px] font-extrabold text-[#0B1437] tracking-tight mb-5">
            What are we <span className="text-[#3B5FE5] italic font-serif pr-2">drafting</span> today?
          </h1>
          <p className="text-[16px] text-slate-500 font-medium max-w-[650px] leading-relaxed">
            Use our AI-powered architect to generate legally sound, structurally precise contracts in seconds.
          </p>
        </div>

        {/* Main Prompt Card Area */}
        <div className="flex flex-col xl:flex-row gap-8 mb-20 relative">
          
          <div className="flex-1 bg-white rounded-[24px] shadow-[0_12px_40px_rgba(0,0,0,0.04)] border border-slate-100 overflow-hidden relative z-10 flex flex-col min-h-[340px]">
            
            {/* Input Header */}
            <div className="px-10 pt-10 pb-5 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#0B1437] flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-[11px] font-bold tracking-[0.15em] text-[#0B1437] uppercase">Contract Blueprint</span>
            </div>

            {/* Text Area */}
            <div className="px-10 pb-4 relative flex-1">
              <textarea 
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the contract you want to generate (e.g., 'A software licensing agreement for a SaaS company based in Delaware')."
                className="w-full h-[180px] resize-none outline-none text-[18px] text-slate-800 placeholder:text-slate-300 font-medium leading-[1.8] bg-transparent"
              />
              <div className="absolute right-10 bottom-6 flex items-center gap-2 text-slate-300 pointer-events-none">
                <Command className="w-4 h-4" />
                <span className="text-[12px] font-bold">Enter to generate</span>
              </div>
            </div>

            {/* Bottom Actions Bar */}
            <div className="bg-[#F8FAFC] border-t border-slate-100 px-10 py-5 flex items-center justify-between">
              
              <div className="flex items-center gap-8 shadow-sm">
                <button className="flex items-center gap-2.5 text-slate-500 hover:text-slate-800 transition-colors">
                  <Paperclip className="w-[18px] h-[18px]" strokeWidth={2.5}/>
                  <span className="text-[13px] font-bold">Attach Sample Contract</span>
                </button>
                <div className="w-px h-6 bg-slate-200"></div>
                <div className="flex gap-2">
                  <span className="px-3 py-1.5 bg-white shadow-sm border border-slate-200/50 text-slate-600 rounded-lg text-[10px] font-bold tracking-widest uppercase">US-LAW</span>
                  <span className="px-3 py-1.5 bg-white shadow-sm border border-slate-200/50 text-slate-600 rounded-lg text-[10px] font-bold tracking-widest uppercase">STRICT-COMPLIANCE</span>
                </div>
              </div>

              <button 
                onClick={() => router.push("/dashboard/tenant-files?generating=true")}
                className="flex items-center gap-2.5 bg-[#152458] hover:bg-[#0B1437] text-white px-7 py-3.5 rounded-xl text-[13px] font-bold shadow-[0_8px_20px_rgba(21,36,88,0.2)] transition-all transform hover:-translate-y-0.5 z-20"
              >
                Generate Contract <ArrowRight className="w-4 h-4" strokeWidth={2.5}/>
              </button>

            </div>
          </div>

          {/* Pro Architect Tip Bubble (Overlapping layout trick) */}
          {showTip && (
            <div className="hidden xl:flex absolute right-[-40px] top-1/2 -translate-y-[45%] flex-col w-[320px] bg-gradient-to-br from-[#Eef3FE] to-[#D5E1FB] rounded-[24px] p-8 shadow-[0_20px_40px_rgba(59,95,229,0.15)] border border-white shrink-0 z-10 hover:shadow-[0_25px_50px_rgba(59,95,229,0.2)] transition-shadow">
              <div className="flex items-center justify-between mb-5">
                <h4 className="text-[11px] font-bold tracking-[0.1em] text-[#1E3A8A] uppercase">Pro Architect Tip</h4>
                <div className="flex items-center gap-3">
                  <Lightbulb className="w-5 h-5 text-[#3B5FE5] opacity-40 shrink-0" strokeWidth={2.5} />
                  <button onClick={() => setShowTip(false)} className="text-[#3B5FE5] opacity-40 hover:opacity-100 transition-opacity outline-none">
                    <X className="w-4 h-4" strokeWidth={3} />
                  </button>
                </div>
              </div>
              <p className="text-[13px] text-slate-700 leading-[1.8] font-medium mb-7">
                For higher accuracy, include specific <span className="font-bold text-[#1E3A8A]">jurisdictions</span> and <span className="font-bold text-[#1E3A8A]">liability caps</span> in your prompt. Our engine will cross-reference these with local statutes automatically.
              </p>
              <div className="bg-white/70 backdrop-blur-md rounded-xl py-2.5 px-4 flex items-center gap-3 w-fit shadow-sm border border-white/50">
                <div className="flex -space-x-2">
                   <div className="w-6 h-6 rounded-full bg-slate-300 border-2 border-white"></div>
                   <div className="w-6 h-6 rounded-full bg-slate-400 border-2 border-white"></div>
                   <div className="w-6 h-6 rounded-full bg-slate-500 border-2 border-white"></div>
                </div>
                <span className="text-[9px] font-bold tracking-widest text-slate-500 uppercase mt-0.5">Verified by 12K+ Pros</span>
              </div>
            </div>
          )}

        </div>

        {/* Recent Blueprints */}
        <div className="mb-20 max-w-[850px]">
          <div className="flex items-center gap-3 mb-8 text-slate-700">
            <History className="w-5 h-5" strokeWidth={2.5} />
            <h3 className="text-[15px] font-bold text-[#0B1437]">Recent Blueprints</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Card 1 */}
            <div className="bg-white/80 rounded-[24px] p-8 shadow-sm border border-slate-100 hover:shadow-lg hover:bg-white transition-all cursor-pointer group">
              <div className="flex items-center justify-between mb-6">
                <div className="w-10 h-10 rounded-xl bg-[#E8EFFF] group-hover:bg-[#3B5FE5] transition-colors flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[#3B5FE5] group-hover:text-white transition-colors" strokeWidth={2.5} />
                </div>
                <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">2H AGO</span>
              </div>
              <h4 className="font-bold text-[16px] text-slate-900 mb-2.5 group-hover:text-[#3B5FE5] transition-colors">Non-Disclosure Agreement</h4>
              <p className="text-[13px] text-slate-500 leading-relaxed font-medium">Standard mutual NDA for tech consultancy partnerships in EMEA...</p>
            </div>

            {/* Card 2 */}
            <div className="bg-white/80 rounded-[24px] p-8 shadow-sm border border-slate-100 hover:shadow-lg hover:bg-white transition-all cursor-pointer group">
              <div className="flex items-center justify-between mb-6">
                <div className="w-10 h-10 rounded-xl bg-slate-100 group-hover:bg-[#0B1437] transition-colors flex items-center justify-center">
                  <Gavel className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" strokeWidth={2.5} />
                </div>
                <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">YESTERDAY</span>
              </div>
              <h4 className="font-bold text-[16px] text-slate-900 mb-2.5 group-hover:text-[#0B1437] transition-colors">Employment Offer Letter</h4>
              <p className="text-[13px] text-slate-500 leading-relaxed font-medium">Executive-level offer with stock option vesting schedules...</p>
            </div>
          </div>
        </div>

        {/* Popular Starting Points */}
        <div className="text-center pt-8 border-t border-slate-200/60 max-w-[850px]">
          <p className="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase mb-8">Popular Starting Points</p>
          <div className="flex flex-wrap items-center justify-center gap-4 max-w-[800px] mx-auto">
            {popularStartingPoints.map(point => (
              <button 
                key={point} 
                onClick={() => setPrompt(point)} 
                className="px-6 py-3 bg-[#Eef3FE]/40 hover:bg-[#E8EFFF] text-[#3B5FE5] rounded-full text-[13px] font-bold hover:shadow-sm hover:-translate-y-0.5 transition-all outline-none"
              >
                {point}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
