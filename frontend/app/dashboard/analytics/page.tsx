"use client";

import { BarChart, LineChart, PieChart } from "lucide-react";

export default function AnalyticsPage() {
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
            Contracts Analyzed
          </p>
          <p className="text-3xl font-bold text-slate-900">24</p>
          <p className="text-xs text-green-600 mt-2">↑ 12% from last month</p>
        </div>

        {/* Average Risk Score */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <p className="text-slate-600 text-sm font-medium mb-2">
            Average Risk Score
          </p>
          <p className="text-3xl font-bold text-slate-900">42%</p>
          <p className="text-xs text-slate-600 mt-2">Across all contracts</p>
        </div>

        {/* High Risk Contracts */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <p className="text-slate-600 text-sm font-medium mb-2">
            High Risk Contracts
          </p>
          <p className="text-3xl font-bold text-red-600">6</p>
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
          <div className="flex items-center justify-center h-64 bg-slate-50 rounded border border-slate-200">
            <div className="text-center">
              <PieChart className="w-16 h-16 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500">Pie chart coming soon</p>
            </div>
          </div>
        </div>

        {/* Contracts by Type */}
        <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">
            Contracts by Type
          </h2>
          <div className="flex items-center justify-center h-64 bg-slate-50 rounded border border-slate-200">
            <div className="text-center">
              <BarChart className="w-16 h-16 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500">Bar chart coming soon</p>
            </div>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4">
          Analysis Trend (Last 30 Days)
        </h2>
        <div className="flex items-center justify-center h-80 bg-slate-50 rounded border border-slate-200">
          <div className="text-center">
            <LineChart className="w-16 h-16 text-slate-300 mx-auto mb-2" />
            <p className="text-slate-500">Line chart coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}
