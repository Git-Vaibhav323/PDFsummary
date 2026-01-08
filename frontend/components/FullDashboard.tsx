"use client";

import { useState } from "react";
import { X, ArrowLeft, Maximize2, Minimize2 } from "lucide-react";
import { Card } from "./ui/card";
import { ProfitLossKPIs, BalanceSheetKPIs, CashFlowKPIs, AccountingRatiosKPIs, InvestorPOVKPIs } from "./KPIDashboard";
import SimpleChart from "./SimpleChart";

// Helper function to convert chart format - handles ALL chart types
function convertChartForSimpleChart(chart: any) {
  const chartProps: any = {
    type: chart.type || chart.chart_type || "bar",
    title: chart.title,
    labels: chart.labels || [],
    values: chart.values || [],
    xAxis: chart.xAxis,
    yAxis: chart.yAxis,
  };

  // Handle PIE charts (special format: labels + values)
  if (chart.type === "pie" && chart.values && Array.isArray(chart.values)) {
    chartProps.type = "pie";
    chartProps.labels = chart.labels || [];
    chartProps.values = chart.values;
    return chartProps;
  }

  // Handle grouped/stacked bar charts
  if (chart.groups) {
    chartProps.type = "stacked_bar";
    chartProps.groups = chart.groups;
  } else if (chart.datasets && Array.isArray(chart.datasets)) {
    // Multi-dataset charts (line, bar, stacked)
    if (chart.datasets.length === 1) {
      // Single dataset - use simple format
      chartProps.type = chart.type || "bar";
      chartProps.labels = chart.labels || [];
      const datasetData = chart.datasets[0]?.data;
      chartProps.values = Array.isArray(datasetData) ? datasetData : [];
    } else {
      // Multiple datasets - keep as groups for SimpleChart
      chartProps.type = chart.type === "stacked_bar" ? "stacked_bar" : (chart.type || "bar");
      chartProps.labels = chart.labels || [];
      // Convert datasets to groups format expected by SimpleChart
      chartProps.groups = chart.datasets.map((ds: any) => ({
        label: ds.label || "Data",
        data: Array.isArray(ds.data) ? ds.data : []
      }));
    }
  }

  // Final validation: ensure values and labels are always arrays
  if (!Array.isArray(chartProps.values)) {
    chartProps.values = [];
  }
  if (!Array.isArray(chartProps.labels)) {
    chartProps.labels = [];
  }

  return chartProps;
}

interface FullDashboardProps {
  dashboardData: any;
  companyName?: string;
  onClose: () => void;
}

export default function FullDashboard({ dashboardData, companyName, onClose }: FullDashboardProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["profit_loss", "balance_sheet", "cash_flow", "accounting_ratios", "management_highlights", "latest_news", "competitors", "investor_pov"])
  );

  const toggleSection = (sectionKey: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionKey)) {
        newSet.delete(sectionKey);
      } else {
        newSet.add(sectionKey);
      }
      return newSet;
    });
  };

  const getSectionSummary = (section: any, defaultText: string) => {
    // Priority: 1) Section summary, 2) Default text if charts exist, 3) Generic message
    if (section?.summary && section.summary.trim() !== "") {
      return section.summary;
    }
    if (section?.charts?.length > 0) {
      return defaultText;
    }
    // Even if no charts, show a generic message instead of "Data Not Available"
    return section?.data && Object.keys(section.data).length > 0 
      ? "Financial data extracted from documents. Analysis available."
      : "Data extraction in progress. Please check back shortly.";
  };

  if (!dashboardData) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop overlay - clean and non-blurred */}
      <div 
        className="fixed inset-0 bg-[#F8FAFC]"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Full-screen header - fixed position */}
      <div className="fixed top-0 left-0 right-0 bg-white border-b border-[#E5E7EB] z-50 shadow-[0_1px_3px_rgba(0,0,0,0.08)]">
        <div className="container mx-auto max-w-[95%] px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onClose}
                className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors text-[#6B7280]"
                aria-label="Close full dashboard"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-[#111827]">Full Financial Dashboard</h1>
                {companyName && (
                  <p className="text-[#6B7280] mt-1">{companyName}</p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors text-[#6B7280]"
              aria-label="Close"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Full dashboard content - PowerBI style with proper spacing */}
      <div className="relative z-40 pt-20 pb-20 overflow-y-auto h-full bg-[#F8FAFC]" style={{ position: 'relative', overflowY: 'auto', overflowX: 'hidden', paddingBottom: '80px' }}>
        <div className="container mx-auto max-w-[95%] px-6 py-6 pb-12" style={{ position: 'relative', paddingBottom: '60px' }}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" style={{ position: 'relative', clear: 'both' }}>
          {/* 1. Profit & Loss - Full Width */}
          <div className="lg:col-span-2" style={{ position: 'relative', clear: 'both', minHeight: '400px' }}>
            <Card className="p-6 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'visible' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Profit & Loss</h2>
              <ProfitLossKPIs data={dashboardData.sections?.profit_loss?.data} />
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6" style={{ position: 'relative', clear: 'both', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections?.profit_loss?.charts?.map((chart: any, idx: number) => (
                  <div key={idx} className="h-auto" style={{ position: 'relative', overflow: 'visible', minHeight: '450px', maxHeight: '600px', zIndex: 2 }}>
                    <SimpleChart {...convertChartForSimpleChart(chart)} />
                  </div>
                ))}
              </div>
              {/* Summary AFTER visualizations */}
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {getSectionSummary(
                    dashboardData.sections?.profit_loss,
                    "Revenue, Expenses, EBITDA, Net Profit, PAT, and Margin trends"
                  )}
                </p>
              </div>
            </Card>
          </div>

          {/* 2. Balance Sheet */}
          <div className="lg:col-span-2" style={{ position: 'relative', clear: 'both', minHeight: '400px' }}>
            <Card className="p-6 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'visible' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Balance Sheet</h2>
              <BalanceSheetKPIs data={dashboardData.sections?.balance_sheet?.data} />
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6" style={{ position: 'relative', clear: 'both', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections?.balance_sheet?.charts?.map((chart: any, idx: number) => (
                  <div key={idx} className="h-auto" style={{ position: 'relative', overflow: 'visible', minHeight: '450px', maxHeight: '600px', zIndex: 2 }}>
                    <SimpleChart {...convertChartForSimpleChart(chart)} />
                  </div>
                ))}
              </div>
              {/* Summary AFTER visualizations */}
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {getSectionSummary(
                    dashboardData.sections?.balance_sheet,
                    "Assets, Liabilities, and Shareholders' Equity"
                  )}
                </p>
              </div>
            </Card>
          </div>

          {/* 3. Cash Flow */}
          <div className="lg:col-span-2" style={{ position: 'relative', clear: 'both', minHeight: '400px' }}>
            <Card className="p-6 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'visible' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Cash Flow</h2>
              <CashFlowKPIs data={dashboardData.sections?.cash_flow?.data} />
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6" style={{ position: 'relative', clear: 'both', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections?.cash_flow?.charts?.map((chart: any, idx: number) => (
                  <div key={idx} className="h-auto" style={{ position: 'relative', overflow: 'visible', minHeight: '450px', maxHeight: '600px', zIndex: 2 }}>
                    <SimpleChart {...convertChartForSimpleChart(chart)} />
                  </div>
                ))}
              </div>
              {/* Summary AFTER visualizations */}
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {getSectionSummary(
                    dashboardData.sections?.cash_flow,
                    "Operating, Investing, and Financing Cash Flow"
                  )}
                </p>
              </div>
            </Card>
          </div>

          {/* 4. Accounting Ratios */}
          <div className="lg:col-span-2" style={{ position: 'relative', clear: 'both', minHeight: '400px' }}>
            <Card className="p-6 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'visible' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Accounting Ratios</h2>
              <AccountingRatiosKPIs data={dashboardData.sections?.accounting_ratios?.data} />
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6" style={{ position: 'relative', clear: 'both', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections?.accounting_ratios?.charts?.map((chart: any, idx: number) => (
                  <div key={idx} className="h-auto" style={{ position: 'relative', overflow: 'visible', minHeight: '450px', maxHeight: '600px', zIndex: 2 }}>
                    <SimpleChart {...convertChartForSimpleChart(chart)} />
                  </div>
                ))}
              </div>
              {/* Summary AFTER visualizations */}
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {getSectionSummary(
                    dashboardData.sections?.accounting_ratios,
                    "Current Ratio, ROE, ROCE, Operating Margin, and other key ratios"
                  )}
                </p>
              </div>
            </Card>
          </div>

          {/* 5. Management Highlights */}
          <div className="lg:col-span-1" style={{ position: 'relative', clear: 'both', minHeight: '300px' }}>
            <Card className="p-6 h-full bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'hidden' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Management Highlights</h2>
              <p className="text-[#6B7280] mb-6">
                {getSectionSummary(
                  dashboardData.sections?.management_highlights,
                  "Key business highlights and strategic initiatives"
                )}
              </p>
              {dashboardData.sections?.management_highlights?.insights?.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData.sections?.management_highlights?.insights?.map((insight: any, idx: number) => (
                    <div key={idx} className="p-3 bg-[#F8FAFC] border-l-4 border-[#2563EB] rounded-lg">
                      <p className="text-sm font-semibold mb-1 text-[#111827]">{insight.title || `Highlight ${idx + 1}`}</p>
                      <p className="text-sm text-[#6B7280]">{insight.summary || insight}</p>
                      {insight.category && (
                        <span className="text-xs text-[#2563EB] mt-2 inline-block">{insight.category}</span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6B7280]">Extracting management highlights from documents...</p>
              )}
            </Card>
          </div>

          {/* 6. Latest News */}
          <div className="lg:col-span-1" style={{ position: 'relative', clear: 'both', minHeight: '300px' }}>
            <Card className="p-6 h-full bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'hidden' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Latest News</h2>
              <p className="text-[#6B7280] mb-6">
                {getSectionSummary(
                  dashboardData.sections?.latest_news,
                  "Recent earnings, analyst commentary, and regulatory updates"
                )}
              </p>
              {dashboardData.sections?.latest_news?.news?.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData.sections?.latest_news?.news?.map((item: any, idx: number) => (
                    <div key={idx} className="p-3 bg-white border border-[#E5E7EB] rounded-lg">
                      <p className="text-sm font-semibold mb-1 text-[#111827]">{item.headline}</p>
                      <p className="text-xs text-[#6B7280]">{item.summary}</p>
                      {item.source && (
                        <p className="text-xs text-[#6B7280] mt-1">Source: {item.source}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6B7280]">Searching for latest news and market updates...</p>
              )}
            </Card>
          </div>

          {/* 7. Competitors */}
          <div className="lg:col-span-1" style={{ position: 'relative', clear: 'both', minHeight: '300px' }}>
            <Card className="p-6 h-full bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'hidden' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Competitors</h2>
              <p className="text-[#6B7280] mb-6">
                {getSectionSummary(
                  dashboardData.sections?.competitors,
                  "Competitive landscape and market positioning"
                )}
              </p>
              {dashboardData.sections?.competitors?.competitors?.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData.sections?.competitors?.competitors?.map((comp: any, idx: number) => (
                    <div key={idx} className="p-3 bg-white border border-[#E5E7EB] rounded-lg">
                      <p className="text-sm font-semibold mb-1 text-[#111827]">{comp.name}</p>
                      <p className="text-xs text-[#6B7280]">{comp.positioning || comp.insight}</p>
                      {comp.comparison && (
                        <p className="text-xs text-[#6B7280] mt-1">{comp.comparison}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6B7280]">Identifying competitors and market positioning...</p>
              )}
            </Card>
          </div>

          {/* 8. Investor Perspective */}
          <div className="lg:col-span-1" style={{ position: 'relative', clear: 'both', minHeight: '400px' }}>
            <Card className="p-6 h-full bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', overflow: 'hidden' }}>
              <h2 className="text-2xl font-bold mb-4 text-[#111827]">Investor Perspective</h2>
              <p className="text-[#6B7280] mb-6">
                {dashboardData.sections?.investor_pov?.summary || "Investment analysis and risk assessment"}
              </p>
              <InvestorPOVKPIs data={dashboardData.sections?.investor_pov} />
              {dashboardData.sections?.investor_pov?.charts && dashboardData.sections?.investor_pov?.charts.length > 0 && (
                <div className="mt-6 grid grid-cols-1 gap-6" style={{ position: 'relative', clear: 'both', zIndex: 1, isolation: 'isolate' }}>
                  {dashboardData.sections?.investor_pov?.charts?.map((chart: any, idx: number) => (
                    <div key={idx} className="h-auto" style={{ position: 'relative', overflow: 'visible', minHeight: '450px', maxHeight: '600px', zIndex: 2 }}>
                      <SimpleChart {...convertChartForSimpleChart(chart)} />
                    </div>
                  ))}
                </div>
              )}
              {dashboardData.sections?.investor_pov?.bull_case?.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-3 text-[#16A34A]">Bull Case</h3>
                  <ul className="space-y-2">
                    {dashboardData.sections?.investor_pov?.bull_case?.map((point: string, idx: number) => (
                      <li key={idx} className="text-sm flex items-start gap-2 text-[#111827]">
                        <span className="text-[#16A34A] mt-1">✓</span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {dashboardData.sections?.investor_pov?.risk_factors?.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-3 text-[#DC2626]">Risk Factors</h3>
                  <ul className="space-y-2">
                    {dashboardData.sections?.investor_pov?.risk_factors?.map((risk: string, idx: number) => (
                      <li key={idx} className="text-sm flex items-start gap-2 text-[#111827]">
                        <span className="text-[#DC2626] mt-1">⚠</span>
                        <span>{risk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

