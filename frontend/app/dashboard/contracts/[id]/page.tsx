"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  AlertCircle,
  CheckCircle,
  Info,
  Loader2,
  ArrowLeft,
  Clock3,
  FileText,
  Database,
  FileSearch,
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { apiClient } from "@/services/api";

interface Clause {
  id: string;
  clause_type: string;
  section_title: string;
  raw_text: string;
  severity: string;
  risk_description: string;
  legal_reasoning: string;
  confidence_score: number;
}

export default function ContractDetailsPage() {
  const params = useParams();
  const contractId = params.id as string;

  const [contract, setContract] = useState<any>(null);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(
    new Set(),
  );
  const [contractMarkdownPreview, setContractMarkdownPreview] = useState("");
  const [finalAnalysisPreview, setFinalAnalysisPreview] = useState("");
  const [pollingActive, setPollingActive] = useState(false);

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;
    let stopped = false;

    const fetchContractData = async (isInitial = false) => {
      try {
        if (isInitial) {
          setLoading(true);
        }

        const [contractRes, analysisRes, markdownListRes] = await Promise.all([
          apiClient.getContractDetails(contractId),
          apiClient.getContractAnalysis(contractId),
          apiClient.listMarkdownFiles(),
        ]);

        setContract(contractRes);
        setClauses(analysisRes.clauses || []);
        setAnalysis(analysisRes);

        const files: string[] = Array.isArray(markdownListRes?.files)
          ? markdownListRes.files
          : [];

        const contractMarkdownName = contractRes?.markdown_file;
        const finalAnalysisName = contractRes?.live?.final_analysis_filename;

        const hasContractMarkdown =
          contractMarkdownName && files.includes(contractMarkdownName);
        const hasFinalAnalysis =
          finalAnalysisName && files.includes(finalAnalysisName);

        if (hasContractMarkdown) {
          const md = await apiClient.getMarkdownContent(contractMarkdownName);
          setContractMarkdownPreview(String(md?.content || "").slice(0, 900));
        }

        if (hasFinalAnalysis) {
          const finalMd = await apiClient.getMarkdownContent(finalAnalysisName);
          setFinalAnalysisPreview(
            String(finalMd?.content || "").slice(0, 1200),
          );
        }

        const shouldContinuePolling =
          contractRes?.status !== "completed" ||
          !contractRes?.live?.result_ready ||
          !contractRes?.live?.final_analysis_ready ||
          !contractRes?.live?.vector_store_ready;

        setPollingActive(shouldContinuePolling);
        if (!shouldContinuePolling && intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
      } catch (error) {
        if (isInitial) {
          toast.error("Failed to load contract details");
        }
      } finally {
        if (isInitial) {
          setLoading(false);
        }
      }
    };

    if (contractId) {
      fetchContractData(true);
      intervalId = setInterval(() => {
        if (!stopped) {
          fetchContractData(false);
        }
      }, 4000);
    }

    return () => {
      stopped = true;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [contractId]);

  const toggleClauseExpand = (clauseId: string) => {
    setExpandedClauses((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(clauseId)) {
        newSet.delete(clauseId);
      } else {
        newSet.add(clauseId);
      }
      return newSet;
    });
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case "HIGH":
        return <AlertCircle className="w-5 h-5 text-orange-600" />;
      case "MEDIUM":
        return <Info className="w-5 h-5 text-yellow-600" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
    }
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return "bg-red-100 text-red-800 border-red-300";
      case "HIGH":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      default:
        return "bg-green-100 text-green-800 border-green-300";
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Loading contract analysis...</p>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="p-8">
        <p className="text-center text-slate-600">Contract not found</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-4">
        <Link
          href="/dashboard/contracts"
          className="text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            {contract.original_filename || contract.markdown_file}
          </h1>
          <p className="text-slate-600 mt-1">
            Counterparty: {contract.counterparty_name || contract.company_name}
          </p>
          <div className="mt-2 flex items-center gap-2 text-xs">
            {pollingActive ? (
              <>
                <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                <span className="text-blue-700 font-medium">
                  Live polling active: waiting for worker updates...
                </span>
              </>
            ) : (
              <>
                <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                <span className="text-green-700 font-medium">
                  Analysis pipeline completed
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Live worker progress */}
      <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4">
          Live Worker Progress
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div
            className={`rounded-lg border p-3 ${contract?.live?.markdown_ready ? "border-green-200 bg-green-50" : "border-slate-200 bg-slate-50"}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <FileText className="w-4 h-4 text-slate-700" />
              <span className="text-xs font-semibold text-slate-700">
                Markdown Parsed
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {contract?.live?.markdown_ready ? "Ready" : "Pending"}
            </p>
          </div>

          <div
            className={`rounded-lg border p-3 ${contract?.live?.result_ready ? "border-green-200 bg-green-50" : "border-slate-200 bg-slate-50"}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <FileSearch className="w-4 h-4 text-slate-700" />
              <span className="text-xs font-semibold text-slate-700">
                Analysis Result JSON
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {contract?.live?.result_ready ? "Ready" : "Pending"}
            </p>
          </div>

          <div
            className={`rounded-lg border p-3 ${contract?.live?.final_analysis_ready ? "border-green-200 bg-green-50" : "border-slate-200 bg-slate-50"}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Clock3 className="w-4 h-4 text-slate-700" />
              <span className="text-xs font-semibold text-slate-700">
                Final Analysis Markdown
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {contract?.live?.final_analysis_ready ? "Ready" : "Pending"}
            </p>
          </div>

          <div
            className={`rounded-lg border p-3 ${contract?.live?.vector_store_ready ? "border-green-200 bg-green-50" : "border-slate-200 bg-slate-50"}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Database className="w-4 h-4 text-slate-700" />
              <span className="text-xs font-semibold text-slate-700">
                Vector Store
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {contract?.live?.vector_store_ready ? "Ready" : "Pending"}
            </p>
          </div>
        </div>
      </div>

      {/* Live markdown previews */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">
            Contract Markdown Preview
          </h3>
          <pre className="whitespace-pre-wrap text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded p-3 max-h-64 overflow-y-auto">
            {contractMarkdownPreview || "Waiting for markdown content..."}
          </pre>
        </div>

        <div className="bg-white rounded-lg shadow border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">
            Final Analysis Preview
          </h3>
          <pre className="whitespace-pre-wrap text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded p-3 max-h-64 overflow-y-auto">
            {finalAnalysisPreview || "Waiting for final analysis markdown..."}
          </pre>
        </div>
      </div>

      {/* Risk Score Card */}
      <div className="bg-white rounded-lg shadow border border-slate-200 p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Overall Risk */}
          <div className="text-center">
            <p className="text-slate-600 text-sm font-medium mb-3">
              Overall Risk Score
            </p>
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-100 to-blue-50 flex items-center justify-center mx-auto mb-3">
              <span
                className={`text-4xl font-bold ${
                  (analysis?.overall_risk_score || 0) >= 70
                    ? "text-red-600"
                    : (analysis?.overall_risk_score || 0) >= 40
                      ? "text-orange-600"
                      : "text-green-600"
                }`}
              >
                {analysis?.overall_risk_score || 0}%
              </span>
            </div>
            <p className="text-sm text-slate-600">Out of 100</p>
          </div>

          {/* Issues Summary */}
          <div>
            <p className="text-slate-600 text-sm font-medium mb-4">
              Issues Found
            </p>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span className="text-slate-700">
                  {analysis?.critical_issues || 0} Critical Issues
                </span>
              </div>
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-orange-600" />
                <span className="text-slate-700">
                  {analysis?.high_issues || 0} High Priority Issues
                </span>
              </div>
              <div className="flex items-center gap-3">
                <Info className="w-5 h-5 text-yellow-600" />
                <span className="text-slate-700">
                  {analysis?.medium_issues || 0} Medium Priority Issues
                </span>
              </div>
            </div>
          </div>

          {/* Contract Details */}
          <div>
            <p className="text-slate-600 text-sm font-medium mb-4">
              Contract Details
            </p>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-slate-500">Type</p>
                <p className="text-slate-900 font-medium">
                  {contract.contract_type}
                </p>
              </div>
              <div>
                <p className="text-slate-500">Status</p>
                <p className="text-slate-900 font-medium">{contract.status}</p>
              </div>
              <div>
                <p className="text-slate-500">Uploaded</p>
                <p className="text-slate-900 font-medium">
                  {new Date(contract.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Clauses Analysis */}
      <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
        <div className="px-8 py-6 border-b border-slate-200">
          <h2 className="text-xl font-bold text-slate-900">
            Clause-by-Clause Analysis
          </h2>
          <p className="text-slate-600 text-sm mt-1">
            {clauses.length} clauses identified
          </p>
        </div>

        <div className="divide-y divide-slate-200">
          {clauses.length === 0 ? (
            <p className="p-8 text-center text-slate-600">
              No clauses analysis available yet
            </p>
          ) : (
            clauses.map((clause) => (
              <div
                key={clause.id}
                className="border-b border-slate-100 last:border-b-0"
              >
                <button
                  onClick={() => toggleClauseExpand(clause.id)}
                  className="w-full px-8 py-4 hover:bg-slate-50 transition text-left flex items-start justify-between gap-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getSeverityIcon(clause.severity)}
                      <span className="font-medium text-slate-900">
                        {clause.section_title}
                      </span>
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold border ${getSeverityBadgeColor(clause.severity)}`}
                      >
                        {clause.severity}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600">
                      Type: {clause.clause_type}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-600">
                      Confidence: {clause.confidence_score}%
                    </p>
                  </div>
                </button>

                {/* Expanded Content */}
                {expandedClauses.has(clause.id) && (
                  <div className="px-8 py-6 bg-slate-50 border-t border-slate-200 space-y-4">
                    {/* Clause Text */}
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">
                        Clause Text
                      </h4>
                      <p className="text-slate-700 text-sm bg-white p-4 rounded border border-slate-200 italic">
                        "{clause.raw_text.substring(0, 300)}..."
                      </p>
                    </div>

                    {/* Risk Description */}
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">
                        Risk Analysis
                      </h4>
                      <p className="text-slate-700 text-sm">
                        {clause.risk_description}
                      </p>
                    </div>

                    {/* Legal Reasoning */}
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">
                        Legal Reasoning
                      </h4>
                      <p className="text-slate-700 text-sm bg-blue-50 p-4 rounded border border-blue-200">
                        {clause.legal_reasoning}
                      </p>
                    </div>

                    {/* Action Items */}
                    <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
                      <h4 className="font-semibold text-slate-900 mb-2">
                        Recommended Action
                      </h4>
                      <ul className="text-sm text-slate-700 space-y-1">
                        <li>• Review this clause with your legal team</li>
                        <li>
                          • Consider negotiating modifications if high risk
                        </li>
                        <li>• Document any approved exceptions</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">Next Steps</h3>
        <ul className="text-sm text-blue-800 space-y-2">
          <li>✓ Review the risk assessment above</li>
          <li>✓ Discuss critical issues with your legal team</li>
          <li>✓ Propose alternative language if needed</li>
          <li>✓ Approve or reject the contract</li>
        </ul>
      </div>
    </div>
  );
}
