"use client";

import { useEffect, useState } from "react";
import { BarChart, LineChart, PieChart, Loader } from "lucide-react";
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

interface AnalyticsMetrics {
  contractsThisMonth: number;
  averageRiskScore: number;
  highRiskCount: number;
  totalContracts: number;
  contractsByType: Record<string, number>;
  riskDistribution: Record<string, number>;
  lastMonthCount: number;
}

export default function AnalyticsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        setLoading(true);

        // Fetch all contracts
        const response = await apiClient.getContracts(1, 1000);
        const allContracts = response.contracts || [];
        setContracts(allContracts);

        // Calculate metrics
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();

        // Contracts analyzed this month
        const contractsThisMonth = allContracts.filter((c) => {
          const contractDate = new Date(c.created_at);
          return (
            contractDate.getMonth() === currentMonth &&
            contractDate.getFullYear() === currentYear
          );
        }).length;

        // Last month count for comparison
        const lastMonthDate = new Date(
          now.getFullYear(),
          now.getMonth() - 1,
          1,
        );
        const lastMonthCount = allContracts.filter((c) => {
          const contractDate = new Date(c.created_at);
          return (
            contractDate.getMonth() === lastMonthDate.getMonth() &&
            contractDate.getFullYear() === lastMonthDate.getFullYear()
          );
        }).length;

        // Average risk score
        const validRiskScores = allContracts
          .filter((c) => c.overall_risk_score !== undefined)
          .map((c) => c.overall_risk_score);
        const averageRiskScore =
          validRiskScores.length > 0
            ? Math.round(
                validRiskScores.reduce((a, b) => a + b, 0) /
                  validRiskScores.length,
              )
            : 0;

        // High risk contracts
        const highRiskCount = allContracts.filter(
          (c) => (c.overall_risk_score || 0) >= 70,
        ).length;

        // Contracts by type
        const contractsByType: Record<string, number> = {};
        allContracts.forEach((c) => {
          const type = c.contract_type || "Unknown";
          contractsByType[type] = (contractsByType[type] || 0) + 1;
        });

        // Risk distribution
        const riskDistribution: Record<string, number> = {
          Critical: allContracts.filter(
            (c) => (c.overall_risk_score || 0) >= 80,
          ).length,
          High: allContracts.filter(
            (c) =>
              (c.overall_risk_score || 0) >= 70 &&
              (c.overall_risk_score || 0) < 80,
          ).length,
          Medium: allContracts.filter(
            (c) =>
              (c.overall_risk_score || 0) >= 50 &&
              (c.overall_risk_score || 0) < 70,
          ).length,
          Low: allContracts.filter((c) => (c.overall_risk_score || 0) < 50)
            .length,
        };

        const monthDifference = contractsThisMonth - lastMonthCount;
        const percentChange =
          lastMonthCount > 0
            ? Math.round((monthDifference / lastMonthCount) * 100)
            : 0;

        setMetrics({
          contractsThisMonth,
          averageRiskScore,
          highRiskCount,
          totalContracts: allContracts.length,
          contractsByType,
          riskDistribution,
          lastMonthCount,
        });
      } catch (error) {
        console.error("Failed to fetch analytics data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const percentChange =
    metrics && metrics.lastMonthCount > 0
      ? Math.round(
          ((metrics.contractsThisMonth - metrics.lastMonthCount) /
            metrics.lastMonthCount) *
            100,
        )
      : 0;

  const changeDirection = percentChange >= 0 ? "↑" : "↓";
  const changeColor = percentChange >= 0 ? "text-green-600" : "text-red-600";

  return (
    <div className="p-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Analytics</h1>
        <p className="text-slate-600 mt-1">
          Track your contract analysis metrics
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Contracts Analyzed This Month */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <p className="text-slate-600 text-sm font-medium mb-2">
            Contracts Analyzed (This Month)
          </p>
          <p className="text-3xl font-bold text-slate-900">
            {metrics?.contractsThisMonth || 0}
          </p>
          <p className={`text-xs ${changeColor} mt-2`}>
            {changeDirection} {Math.abs(percentChange)}% from last month
          </p>
        </div>

        {/* Average Risk Score */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <p className="text-slate-600 text-sm font-medium mb-2">
            Average Risk Score
          </p>
          <p className="text-3xl font-bold text-slate-900">
            {metrics?.averageRiskScore || 0}%
          </p>
          <p className="text-xs text-slate-600 mt-2">
            Across {metrics?.totalContracts || 0} total contracts
          </p>
        </div>

        {/* High Risk Contracts */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <p className="text-slate-600 text-sm font-medium mb-2">
            High Risk Contracts
          </p>
          <p className="text-3xl font-bold text-red-600">
            {metrics?.highRiskCount || 0}
          </p>
          <p className="text-xs text-slate-600 mt-2">Requiring attention</p>
        </div>
      </div>

      {/* Chart Placeholders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">
            Risk Distribution
          </h2>
          {metrics && Object.keys(metrics.riskDistribution).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(metrics.riskDistribution).map(
                ([level, count]) => (
                  <div key={level}>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-slate-700">
                        {level}
                      </span>
                      <span className="text-sm font-bold text-slate-900">
                        {count}
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          level === "Critical"
                            ? "bg-red-600"
                            : level === "High"
                              ? "bg-orange-600"
                              : level === "Medium"
                                ? "bg-yellow-600"
                                : "bg-green-600"
                        }`}
                        style={{
                          width: `${
                            (count / (metrics.totalContracts || 1)) * 100
                          }%`,
                        }}
                      ></div>
                    </div>
                  </div>
                ),
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 bg-slate-50 rounded border border-slate-200">
              <div className="text-center">
                <PieChart className="w-16 h-16 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500">No contracts uploaded yet</p>
              </div>
            </div>
          )}
        </div>

        {/* Contracts by Type */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">
            Contracts by Type
          </h2>
          {metrics && Object.keys(metrics.contractsByType).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(metrics.contractsByType).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">{type}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 bg-slate-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-blue-600"
                        style={{
                          width: `${
                            (count / (metrics.totalContracts || 1)) * 100
                          }%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-bold text-slate-900 w-8">
                      {count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 bg-slate-50 rounded border border-slate-200">
              <div className="text-center">
                <BarChart className="w-16 h-16 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500">No contracts uploaded yet</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
        <h3 className="font-semibold text-slate-900 mb-4">Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-slate-600 mb-1">Total Contracts</p>
            <p className="text-2xl font-bold text-slate-900">
              {metrics?.totalContracts || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">Critical Risk</p>
            <p className="text-2xl font-bold text-red-600">
              {metrics?.riskDistribution.Critical || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">High Risk</p>
            <p className="text-2xl font-bold text-orange-600">
              {metrics?.riskDistribution.High || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">Low Risk</p>
            <p className="text-2xl font-bold text-green-600">
              {metrics?.riskDistribution.Low || 0}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
