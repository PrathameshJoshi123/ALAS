"use client";

import { useState, useEffect, useRef } from "react";
import {
  UploadCloud,
  FileText,
  FileSearch,
  XCircle,
  RefreshCcw,
  ExternalLink,
  Plus,
  Loader2,
} from "lucide-react";
import { apiClient } from "@/services/api";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);
  const [uploading, setUploading] = useState(false);

  const fetchContracts = async () => {
    try {
      setFetching(true);
      const data = await apiClient.getContracts(1, 10);
      setContracts(data.items || []);
    } catch (error) {
      console.error("Failed to fetch contracts", error);
      // toast.error("Failed to load contracts repository.");
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    fetchContracts();
  }, []);

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      toast.error("File size exceeds 50MB limit.");
      return;
    }

    setUploading(true);
    const uploadToast = toast.loading("Uploading and initiating analysis...");

    try {
      await apiClient.uploadContract(file, {
        counterparty_name: "TBD",
        contract_type: "NDA",
      });
      toast.success("Contract uploaded successfully!", { id: uploadToast });
      fetchContracts();
    } catch (error: any) {
      console.error("Upload failed", error);
      toast.error(error.response?.data?.detail || "Failed to upload contract", {
        id: uploadToast,
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleViewDetails = (contractId: string) => {
    router.push(`/dashboard/tenant-files?id=${contractId}`);
  };

  return (
    <div className="p-10 lg:p-14 max-w-[1200px]">
      <input
        type="file"
        className="hidden"
        ref={fileInputRef}
        onChange={handleFileUpload}
        accept=".pdf"
      />

      {/* Header */}
      <div className="mb-10">
        <p className="text-[10px] font-bold tracking-[0.15em] text-slate-400 uppercase mb-3">
          Dashboard / Analytics
        </p>
        <h1 className="text-[32px] font-bold text-slate-900 tracking-tight mb-4">
          Contract Repository
        </h1>
        <p className="text-[14px] text-slate-500 max-w-[700px] leading-relaxed">
          Securely upload and analyze your legal documents. Our AI engine scans
          for liability shifts, term inconsistencies, and regulatory compliance
          in seconds.
        </p>
      </div>

      <div className="flex flex-col xl:flex-row gap-8 mb-16 relative">
        <div className="flex-1 bg-[#F9FAFC] border-[2px] border-dashed border-[#E2E8F0] rounded-[24px] p-12 lg:p-20 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-[#E0E7FF] rounded-2xl flex items-center justify-center mb-6">
            {uploading ? (
              <Loader2
                className="w-8 h-8 text-[#0B1437] animate-spin"
                strokeWidth={2.5}
              />
            ) : (
              <UploadCloud
                className="w-8 h-8 text-[#0B1437]"
                strokeWidth={2.5}
              />
            )}
          </div>
          <h2 className="text-[22px] font-bold text-slate-900 mb-2">
            {uploading ? "Analyzing document..." : "Drop contract to analyze"}
          </h2>
          <p className="text-[13px] text-slate-500 mb-8 font-medium">
            Support for PDF and TXT (Max 50MB)
          </p>
          <div className="flex items-center gap-4">
            <button
              onClick={handleFileSelect}
              disabled={uploading}
              className="bg-[#0B1437] text-white px-6 py-3.5 rounded-lg text-[13px] font-bold flex items-center justify-center gap-2 hover:bg-[#152355] transition shadow-md disabled:bg-slate-400"
            >
              <Plus className="w-4 h-4" />
              Select Files
            </button>
            <button className="bg-white text-slate-700 border border-slate-200 px-6 py-3.5 rounded-lg text-[13px] font-bold flex items-center justify-center hover:bg-slate-50 transition shadow-sm">
              Connect Drive
            </button>
          </div>
        </div>

        <div className="w-full xl:w-[320px] shrink-0 xl:-mr-12 xl:mt-8 z-10 transition-transform hover:-translate-y-1">
          <div className="bg-gradient-to-br from-[#E8EFFF] to-[#D5E1FB] rounded-[24px] p-6 shadow-[0_20px_40px_rgba(59,95,229,0.15)] border border-white">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-[13px] font-bold text-[#1E3A8A]">
                System Health
              </h3>
              <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
            </div>

            <div className="space-y-3 mb-4">
              <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-white/50">
                <p className="text-[9px] font-bold tracking-widest text-[#1E3A8A] opacity-60 uppercase mb-1">
                  Weekly Accuracy
                </p>
                <div className="flex items-baseline gap-2">
                  <span className="text-[24px] font-bold text-slate-900">
                    99.4%
                  </span>
                  <span className="text-[11px] font-bold text-green-500">
                    +0.2%
                  </span>
                </div>
              </div>
              <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-white/50">
                <p className="text-[9px] font-bold tracking-widest text-[#1E3A8A] opacity-60 uppercase mb-1">
                  Average Turnaround
                </p>
                <div className="flex items-baseline gap-2">
                  <span className="text-[24px] font-bold text-slate-900">
                    14s
                  </span>
                  <span className="text-[11px] font-bold text-slate-400">
                    Real-time
                  </span>
                </div>
              </div>
            </div>

            <div className="h-20 bg-gradient-to-t from-slate-800 to-slate-600 rounded-xl overflow-hidden relative mt-4 shadow-inner opacity-90">
              <div className="absolute bottom-0 left-0 right-0 h-full bg-blue-300/10 mix-blend-overlay"></div>
              <svg
                className="absolute inset-0 w-full h-full text-white/30"
                preserveAspectRatio="none"
                viewBox="0 0 100 100"
                fill="none"
              >
                <path
                  d="M0,100 Q10,70 20,80 T40,60 T60,50 T80,20 T100,40 L100,100 Z"
                  fill="currentColor"
                  opacity="0.1"
                />
                <path
                  d="M0,80 Q20,60 40,70 T80,30 T100,10"
                  stroke="rgba(255,255,255,0.7)"
                  strokeWidth="1.5"
                  fill="none"
                />
                <path
                  d="M0,85 Q20,70 40,75 T80,40 T100,30"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="1"
                  fill="none"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-[18px] font-bold text-slate-900 mb-6 tracking-tight">
          Recent Analysis
        </h3>
        <div className="bg-white rounded-[20px] shadow-sm border border-slate-100 overflow-hidden">
          {fetching ? (
            <div className="p-20 flex flex-col items-center justify-center gap-4">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              <p className="text-slate-500 font-medium">
                Loading repository...
              </p>
            </div>
          ) : contracts.length === 0 ? (
            <div className="p-20 text-center">
              <FileText className="w-12 h-12 text-slate-200 mx-auto mb-4" />
              <p className="text-slate-500 font-medium">
                No contracts found. Upload your first document above.
              </p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-8 py-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase w-1/3">
                    Document Name
                  </th>
                  <th className="px-8 py-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase w-1/6">
                    Upload Date
                  </th>
                  <th className="px-8 py-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase w-[15%]">
                    Status
                  </th>
                  <th className="px-8 py-5 text-right w-1/3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {contracts.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-[#F9FAFC] transition-colors group"
                  >
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center`}
                        >
                          <FileText
                            className={`w-4 h-4 text-[#3B5FE5]`}
                            strokeWidth={2.5}
                          />
                        </div>
                        <span
                          onClick={() => handleViewDetails(doc.id)}
                          className="text-[13px] font-bold text-[#0B1437] group-hover:underline cursor-pointer decoration-2 underline-offset-4"
                        >
                          {doc.original_filename || doc.markdown_file}
                        </span>
                      </div>
                    </td>
                    <td className="px-8 py-5 text-[12px] text-slate-500 font-medium">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-1.5 h-1.5 rounded-full ${
                            doc.status === "completed"
                              ? "bg-green-500"
                              : doc.status === "failed"
                                ? "bg-red-500"
                                : doc.status === "processing"
                                  ? "bg-blue-400 animate-pulse"
                                  : "bg-slate-300"
                          }`}
                        ></div>
                        <span
                          className={`text-[10px] font-bold tracking-wider uppercase ${
                            doc.status === "completed"
                              ? "text-green-600"
                              : doc.status === "failed"
                                ? "text-red-600"
                                : "text-slate-500"
                          }`}
                        >
                          {doc.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <div className="flex items-center justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity float-right">
                        <button
                          onClick={() => handleViewDetails(doc.id)}
                          className="flex items-center gap-2 text-slate-400 hover:text-[#0B1437] font-bold text-[11px] uppercase tracking-wider"
                        >
                          View Analysis
                          <ExternalLink
                            className="w-[18px] h-[18px]"
                            strokeWidth={2.5}
                          />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
