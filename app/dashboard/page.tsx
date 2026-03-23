"use client";

import { useEffect, useState } from "react";
import { FileText, TrendingUp, AlertCircle, Clock } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { apiClient } from "@/services/api";

interface Contract {
  id: string;
  filename: string;
  counterparty_name: string;
  status: string;
  overall_risk_score: number;
  created_at: string;
}

export default function DashboardPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalContracts: 0,
    analyzing: 0,
    pending: 0,
    highRisk: 0,
  });

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const data = await apiClient.getContracts(1, 5);
        setContracts(data.items || []);

        // Calculate stats
        const totalContracts = data.total || 0;
        const analyzing =
          data.items?.filter((c: Contract) => c.status === "PROCESSING")
            .length || 0;
        const pending =
          data.items?.filter((c: Contract) => c.status === "REVIEW_PENDING")
            .length || 0;
        const highRisk =
          data.items?.filter((c: Contract) => (c.overall_risk_score || 0) > 70)
            .length || 0;

        setStats({
          totalContracts,
          analyzing,
          pending,
          highRisk,
        });
      } catch (error) {
        console.error("Failed to fetch contracts:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchContracts();
  }, []);

  const getRiskColor = (score: number) => {
    if (score >= 70) return "bg-red-100 text-red-800";
    if (score >= 40) return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { bg: string; text: string }> = {
      UPLOADED: { bg: "bg-blue-100", text: "text-blue-800" },
      PROCESSING: { bg: "bg-purple-100", text: "text-purple-800" },
      ANALYZED: { bg: "bg-green-100", text: "text-green-800" },
      REVIEW_PENDING: { bg: "bg-yellow-100", text: "text-yellow-800" },
      APPROVED: { bg: "bg-green-100", text: "text-green-800" },
      REJECTED: { bg: "bg-red-100", text: "text-red-800" },
    };
    const style = statusMap[status] || {
      bg: "bg-slate-100",
      text: "text-slate-800",
    };
    return `${style.bg} ${style.text}`;
  };

  return (
    <div className="p-8 space-y-8">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600 mt-1">
            Manage and analyze your contracts
          </p>
        </div>
        <Link
          href="/dashboard/contracts/upload"
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition"
        >
          + Upload Contract
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Total Contracts */}
        <div className="bg-white rounded-lg shadow p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">
                Total Contracts
              </p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {stats.totalContracts}
              </p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Analyzing */}
        <div className="bg-white rounded-lg shadow p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">
                Now Analyzing
              </p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {stats.analyzing}
              </p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
              <Clock className="w-6 h-6 text-purple-600 animate-spin" />
            </div>
          </div>
        </div>

        {/* Pending Review */}
        <div className="bg-white rounded-lg shadow p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">
                Pending Review
              </p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {stats.pending}
              </p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-yellow-100 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </div>

        {/* High Risk */}
        <div className="bg-white rounded-lg shadow p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">High Risk</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {stats.highRisk}
              </p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-red-100 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Contracts */}
      <div className="bg-white rounded-lg shadow border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">
            Recent Contracts
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-slate-600">Loading contracts...</p>
          </div>
        ) : contracts.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-600">
              No contracts yet. Upload one to get started!
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                    Filename
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                    Counterparty
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-700 uppercase">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {contracts.map((contract) => (
                  <tr
                    key={contract.id}
                    className="hover:bg-slate-50 transition"
                  >
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-900">
                        {contract.filename}
                      </p>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      {contract.counterparty_name}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(contract.status)}`}
                      >
                        {contract.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(contract.overall_risk_score || 0)}`}
                      >
                        {contract.overall_risk_score || 0}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 text-sm">
                      {new Date(contract.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Link
                        href={`/dashboard/contracts/${contract.id}`}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="px-6 py-4 border-t border-slate-200">
          <Link
            href="/dashboard/contracts"
            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
          >
            View all contracts →
          </Link>
        </div>
      </div>
    </div>
  );
}
