"use client";

import { useEffect, useState } from "react";
import { FileText, Filter, Search } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/services/api";

interface Contract {
  id: string;
  filename: string;
  counterparty_name: string;
  contract_type: string;
  status: string;
  overall_risk_score: number;
  created_at: string;
}

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getContracts(page, 10);
        setContracts(data.contracts || []);
        setTotalPages(Math.ceil((data.total || 0) / 10));
      } catch (error) {
        console.error("Failed to fetch contracts:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchContracts();
  }, [page]);

  const filteredContracts = contracts.filter((contract) => {
    const matchesSearch =
      contract.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contract.counterparty_name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "ALL" || contract.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

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
          <h1 className="text-3xl font-bold text-slate-900">Contracts</h1>
          <p className="text-slate-600 mt-1">Manage all your legal contracts</p>
        </div>
        <Link
          href="/dashboard/contracts/upload"
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition"
        >
          + Upload Contract
        </Link>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-lg shadow border border-slate-200 p-6 space-y-4">
        <div className="flex gap-4 flex-col md:flex-row">
          {/* Search Input */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by filename or counterparty..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          >
            <option value="ALL">All Status</option>
            <option value="UPLOADED">Uploaded</option>
            <option value="PROCESSING">Processing</option>
            <option value="ANALYZED">Analyzed</option>
            <option value="REVIEW_PENDING">Review Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-slate-600">Loading contracts...</p>
          </div>
        ) : filteredContracts.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-600">
              No contracts found. Upload one to get started!
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                      Filename
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                      Counterparty
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">
                      Risk
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
                  {filteredContracts.map((contract) => (
                    <tr
                      key={contract.id}
                      className="hover:bg-slate-50 transition"
                    >
                      <td className="px-6 py-4">
                        <p className="font-medium text-slate-900 truncate">
                          {contract.filename}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        {contract.counterparty_name}
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-sm">
                        {contract.contract_type}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(contract.status)}`}
                        >
                          {contract.status.replace(/_/g, " ")}
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
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between">
              <p className="text-sm text-slate-600">
                Showing {filteredContracts.length} of {contracts.length}{" "}
                contracts
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border border-slate-300 rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-3 py-1">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 border border-slate-300 rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
