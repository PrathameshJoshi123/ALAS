"use client";

import { useState } from "react";
import { UploadCloud, FileText, FileSearch, XCircle, RefreshCcw, ExternalLink, Plus } from "lucide-react";

export default function DashboardPage() {
  // Hardcoded UI demo for accurate replication
  const [contracts] = useState([
    { id: 1, name: "Service_Agreement_v4.pdf", date: "Oct\n24,\n2023", status: "ANALYZED", icon: FileText, color: "text-[#3B5FE5]", bg: "bg-blue-100" },
    { id: 2, name: "NDA_Tesla_Motors_Draft.docx", date: "Oct\n25,\n2023", status: "PROCESSING", extra: "CALCULATING...", icon: FileText, color: "text-[#3B5FE5]", bg: "bg-blue-100" },
    { id: 3, name: "Commercial_Lease_Final.pdf", date: "Oct\n25,\n2023", status: "FAILED", extra: "INVALID FORMAT", icon: XCircle, color: "text-red-600", bg: "bg-red-100" },
    { id: 4, name: "Vendor_Master_Policy.docx", date: "Oct\n22,\n2023", status: "ANALYZED", extra: "HIGH", icon: FileText, color: "text-[#3B5FE5]", bg: "bg-blue-100" },
  ]);

  return (
    <div className="p-10 lg:p-14 max-w-[1200px]">
      
      {/* Header */}
      <div className="mb-10">
        <p className="text-[10px] font-bold tracking-[0.15em] text-slate-400 uppercase mb-3">
          Dashboard / Analytics
        </p>
        <h1 className="text-[32px] font-bold text-slate-900 tracking-tight mb-4">
          Contract Repository
        </h1>
        <p className="text-[14px] text-slate-500 max-w-[700px] leading-relaxed">
          Securely upload and analyze your legal documents. Our AI engine scans for liability shifts, term inconsistencies, and regulatory compliance in seconds.
        </p>
      </div>

      {/* Main Grid: Upload Area & System Health */}
      <div className="flex flex-col xl:flex-row gap-8 mb-16 relative">
        
        {/* Upload Zone */}
        <div className="flex-1 bg-[#F9FAFC] border-[2px] border-dashed border-[#E2E8F0] rounded-[24px] p-12 lg:p-20 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-[#E0E7FF] rounded-2xl flex items-center justify-center mb-6">
            <UploadCloud className="w-8 h-8 text-[#0B1437]" strokeWidth={2.5} />
          </div>
          <h2 className="text-[22px] font-bold text-slate-900 mb-2">
            Drop contract to analyze
          </h2>
          <p className="text-[13px] text-slate-500 mb-8 font-medium">
            Support for PDF, DOCX, and RTF (Max 50MB)
          </p>
          <div className="flex items-center gap-4">
            <button className="bg-[#0B1437] text-white px-6 py-3.5 rounded-lg text-[13px] font-bold flex items-center justify-center gap-2 hover:bg-[#152355] transition shadow-md">
              <Plus className="w-4 h-4" />
              Select Files
            </button>
            <button className="bg-white text-slate-700 border border-slate-200 px-6 py-3.5 rounded-lg text-[13px] font-bold flex items-center justify-center hover:bg-slate-50 transition shadow-sm">
              Connect Drive
            </button>
          </div>
        </div>

        {/* System Health Card (Floating illusion via layout) */}
        <div className="w-full xl:w-[320px] shrink-0 xl:-mr-12 xl:mt-8 z-10 transition-transform hover:-translate-y-1">
          <div className="bg-gradient-to-br from-[#E8EFFF] to-[#D5E1FB] rounded-[24px] p-6 shadow-[0_20px_40px_rgba(59,95,229,0.15)] border border-white">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-[13px] font-bold text-[#1E3A8A]">System Health</h3>
              <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
            </div>
            
            <div className="space-y-3 mb-4">
              <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-white/50">
                <p className="text-[9px] font-bold tracking-widest text-[#1E3A8A] opacity-60 uppercase mb-1">Weekly Accuracy</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-[24px] font-bold text-slate-900">99.4%</span>
                  <span className="text-[11px] font-bold text-green-500">+0.2%</span>
                </div>
              </div>
              <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-white/50">
                <p className="text-[9px] font-bold tracking-widest text-[#1E3A8A] opacity-60 uppercase mb-1">Average Turnaround</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-[24px] font-bold text-slate-900">14s</span>
                  <span className="text-[11px] font-bold text-slate-400">Real-time</span>
                </div>
              </div>
            </div>

            {/* Faux graph bottom */}
            <div className="h-20 bg-gradient-to-t from-slate-800 to-slate-600 rounded-xl overflow-hidden relative mt-4 shadow-inner opacity-90">
              <div className="absolute bottom-0 left-0 right-0 h-full bg-blue-300/10 mix-blend-overlay"></div>
              <svg className="absolute inset-0 w-full h-full text-white/30" preserveAspectRatio="none" viewBox="0 0 100 100" fill="none">
                <path d="M0,100 Q10,70 20,80 T40,60 T60,50 T80,20 T100,40 L100,100 Z" fill="currentColor" opacity="0.1"/>
                <path d="M0,80 Q20,60 40,70 T80,30 T100,10" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" fill="none" />
                <path d="M0,85 Q20,70 40,75 T80,40 T100,30" stroke="rgba(255,255,255,0.2)" strokeWidth="1" fill="none" />
              </svg>
            </div>
          </div>
        </div>

      </div>

      {/* Recent Analysis Table */}
      <div>
        <h3 className="text-[18px] font-bold text-slate-900 mb-6 tracking-tight">Recent Analysis</h3>
        <div className="bg-white rounded-[20px] shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="px-8 py-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase w-1/3">Document Name</th>
                <th className="px-8 py-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase w-1/6">Upload Date</th>
                <th className="px-8 py-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase w-[15%]">Status</th>
                <th className="px-8 py-5 text-right w-1/3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {contracts.map((doc, i) => (
                <tr key={i} className="hover:bg-[#F9FAFC] transition-colors group">
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg ${doc.bg} flex items-center justify-center`}>
                        <doc.icon className={`w-4 h-4 ${doc.color}`} strokeWidth={2.5}/>
                      </div>
                      <span className="text-[13px] font-bold text-[#0B1437] group-hover:underline cursor-pointer decoration-2 underline-offset-4">{doc.name}</span>
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    <div className="text-[12px] text-slate-500 font-medium whitespace-pre-line leading-[1.3]">
                      {doc.date}
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-2">
                       <div className={`w-1.5 h-1.5 rounded-full ${
                         doc.status === 'ANALYZED' ? 'bg-green-500' :
                         doc.status === 'FAILED' ? 'bg-red-500' : 'bg-slate-300'
                       }`}></div>
                       <span className={`text-[10px] font-bold tracking-wider uppercase ${
                         doc.status === 'ANALYZED' ? 'text-green-600' :
                         doc.status === 'FAILED' ? 'text-red-600' : 'text-slate-500'
                       }`}>
                         {doc.status}
                       </span>
                    </div>
                  </td>
                  <td className="px-8 py-5 text-right">
                    <div className="flex items-center justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity float-right">
                      {doc.status === 'PROCESSING' && (
                         <div className="flex items-center gap-3">
                           <span className="text-[9px] font-bold tracking-widest text-slate-500 uppercase">{doc.extra}</span>
                           <FileSearch className="w-4 h-4 text-slate-400 animate-pulse" />
                         </div>
                      )}
                      {doc.status === 'FAILED' && (
                         <div className="flex items-center gap-3">
                           <span className="text-[9px] font-bold tracking-widest text-red-500 uppercase">{doc.extra}</span>
                           <RefreshCcw className="w-4 h-4 text-red-500 cursor-pointer hover:rotate-180 transition-transform" />
                         </div>
                      )}
                      {doc.status === 'ANALYZED' && doc.extra === 'HIGH' && (
                         <div className="flex items-center gap-4">
                           <div className="flex items-end gap-1 mb-0.5">
                              <div className="w-6 h-1 bg-red-500 rounded-full"></div>
                              <div className="w-6 h-1 bg-red-600 rounded-full"></div>
                              <div className="w-6 h-1 bg-red-700 rounded-full"></div>
                           </div>
                           <ExternalLink className="w-[18px] h-[18px] text-slate-400 hover:text-[#0B1437] cursor-pointer" strokeWidth={2.5} />
                         </div>
                      )}
                      {doc.status === 'ANALYZED' && !doc.extra && (
                         <div className="flex items-center gap-4">
                           <ExternalLink className="w-[18px] h-[18px] text-slate-400 hover:text-[#0B1437] cursor-pointer" strokeWidth={2.5} />
                         </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
    </div>
  );
}
