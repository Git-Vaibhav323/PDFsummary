"use client";

import { useState, useEffect } from "react";
import { X, TrendingUp, TrendingDown, Minus, Loader2, LayoutDashboard, ChevronDown, ChevronUp, DollarSign, Activity, BarChart3, PieChart, Users, Newspaper, Building2, Target, AlertCircle, Maximize2 } from "lucide-react";
import { Card } from "./ui/card";
import { ProfitLossKPIs, BalanceSheetKPIs, CashFlowKPIs, AccountingRatiosKPIs, InvestorPOVKPIs, KPICard } from "./KPIDashboard";
import SimpleChart from "./SimpleChart";
import FullDashboard from "./FullDashboard";
import { apiClient } from "@/lib/api";

interface FinancialDashboardProps {
  documentIds: string[];
  companyName?: string;
  dashboardData?: any;
  isGenerating?: boolean;
  isReady?: boolean;
  onClose: () => void;
}

interface DashboardData {
  sections: {
    profit_loss?: {
      data: any;
      charts: any[];
      insights: string[];
      summary?: string;
    };
    balance_sheet?: {
      data: any;
      charts: any[];
      insights: string[];
      summary?: string;
    };
    cash_flow?: {
      data: any;
      charts: any[];
      insights: string;
      summary?: string;
    };
    accounting_ratios?: {
      data: any;
      charts: any[];
      insights: string[];
      summary?: string;
    };
    management_highlights?: {
      insights: Array<{ title: string; summary: string; category: string; emphasis?: string }>;
      summary: string;
      source?: string;
    };
    latest_news?: {
      news: Array<{ headline: string; summary: string; source: string; date: string }>;
      source: string;
      source_badge?: string;
      summary?: string;
    };
    competitors?: {
      competitors: Array<{ name: string; insight: string; source: string }>;
      source: string;
      source_badge?: string;
      summary?: string;
    };
    investor_pov?: {
      trends: any;
      summary: string;
      bull_case: string[];
      risk_factors: string[];
      charts: any[];
    };
    error?: string;
  };
  error?: string;
}

export default function FinancialDashboard({
  documentIds,
  companyName,
  dashboardData: propDashboardData,
  isGenerating = false,
  isReady = false,
  onClose,
}: FinancialDashboardProps) {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    propDashboardData ? (propDashboardData as DashboardData) : null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFullDashboard, setShowFullDashboard] = useState(false);
  
  // Track which sections are expanded - ALL EXPANDED BY DEFAULT
  const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
    // ALWAYS start with all sections expanded
    const allSections = new Set([
      'profit_loss',
      'balance_sheet',
      'cash_flow',
      'accounting_ratios',
      'management_highlights',
      'latest_news',
      'competitors',
      'investor_pov'
    ]);
    console.log('📊 Initializing dashboard with all sections expanded:', allSections);
    return allSections;
  });
  
  const toggleSection = (sectionKey: string) => {
    console.log(`📊 Toggling section: ${sectionKey}`);
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionKey)) {
        newSet.delete(sectionKey);
        console.log(`   ⬇️ Collapsed: ${sectionKey}`);
      } else {
        newSet.add(sectionKey);
        console.log(`   ⬆️ Expanded: ${sectionKey}`);
      }
      console.log(`   Total expanded: ${newSet.size}/8`);
      return newSet;
    });
  };

  // Update dashboard data when prop changes
  useEffect(() => {
    if (propDashboardData) {
      setDashboardData(propDashboardData);
      setIsLoading(false);
    }
  }, [propDashboardData]);

  // Load dashboard if not provided and not generating
  useEffect(() => {
    const loadDashboard = async () => {
      if (propDashboardData || isGenerating || documentIds.length === 0) {
        return;
      }
      
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.generateFinancialDashboard(documentIds, companyName);
        setDashboardData(data);
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard");
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboard();
  }, [documentIds, companyName, propDashboardData, isGenerating]);

  // Show loading state only if generating AND no data/error exists
  if ((isGenerating || isLoading) && !propDashboardData && !dashboardData && !error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-[#2563EB]" />
          <p className="text-lg font-semibold text-[#111827]">Generating Financial Dashboard...</p>
          <p className="text-sm text-[#6B7280] mt-2">Analyzing documents and fetching market data</p>
          <p className="text-xs text-[#6B7280] mt-4">This may take a few moments...</p>
          {isGenerating && (
            <p className="text-xs text-[#6B7280] mt-2">If this takes too long, the dashboard may timeout. Try with fewer documents.</p>
          )}
        </div>
      </div>
    );
  }

  if (error || dashboardData?.error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F8FAFC]">
        <Card className="p-6 max-w-md bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
          <div className="text-center">
            <p className="text-lg font-semibold text-[#DC2626] mb-2">Error Loading Dashboard</p>
            <p className="text-sm text-[#6B7280] mb-4">{error || dashboardData?.error}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#2563EB] text-white rounded-xl hover:bg-[#1D4ED8] transition-colors"
            >
              Close
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // Show error state if there's an error and no data
  if ((error || dashboardData?.error) && !dashboardData) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F8FAFC]">
        <Card className="p-6 max-w-md bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
          <div className="text-center">
            <p className="text-lg font-semibold text-[#DC2626] mb-2">Error Loading Dashboard</p>
            <p className="text-sm text-[#6B7280] mb-4">{error || dashboardData?.error}</p>
            <p className="text-xs text-[#6B7280] mb-4">
              The dashboard generation timed out or failed. This may happen with very large documents.
              Try selecting fewer documents or simpler PDFs.
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#2563EB] text-white rounded-xl hover:bg-[#1D4ED8] transition-colors"
            >
              Close
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // If no data and not generating/loading, show empty state
  if (!dashboardData && !isGenerating && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center text-[#6B7280]">
          <LayoutDashboard className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-semibold mb-2 text-[#111827]">Dashboard Not Ready</p>
          <p className="text-sm text-[#6B7280]">Please wait for dashboard generation to complete.</p>
          <p className="text-xs mt-2 text-[#6B7280]">Check the Dashboard tab for status indicator.</p>
        </div>
      </div>
    );
  }

  // If we have error in dashboardData but also have some data, show the data with error banner
  if (dashboardData?.error && dashboardData) {
    // Continue to render dashboard but show error banner
  }

  if (!dashboardData) {
    return null;
  }

  // Show full dashboard if requested
  if (showFullDashboard) {
    return (
      <FullDashboard
        dashboardData={dashboardData}
        companyName={companyName}
        onClose={() => setShowFullDashboard(false)}
      />
    );
  }

  // Helper to get section summary - ALWAYS show summary if available, even without charts
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

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC]" style={{ position: 'relative', minHeight: '100vh', paddingBottom: '80px' }}>
      <div className="container mx-auto max-w-7xl p-6 pb-20" style={{ position: 'relative' }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6 sticky top-0 bg-white/95 backdrop-blur-sm py-4 border-b border-[#E5E7EB] z-10" style={{ position: 'sticky', top: 0 }}>
          <div>
            <h1 className="text-3xl font-bold text-[#111827]">Financial Dashboard</h1>
            {companyName && (
              <p className="text-[#6B7280] mt-1">{companyName}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors text-[#6B7280]"
            aria-label="Close dashboard"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Error Banner - Show if there's an error but we still have some data */}
        {(dashboardData?.error || error) && (
          <div className="mb-6 p-4 bg-[#FEF2F2] border border-[#FECACA] rounded-lg">
            <div className="flex items-start gap-3">
              <div className="text-[#DC2626] mt-0.5">
                <AlertCircle className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-[#DC2626] mb-1">Dashboard Generation Warning</p>
                <p className="text-sm text-[#6B7280]">
                  {dashboardData?.error || error}
                </p>
                <p className="text-xs text-[#6B7280] mt-2">
                  Some sections may be incomplete. The dashboard may have timed out during generation.
                  Try selecting fewer documents or simpler PDFs for better results.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Sections - ALWAYS SHOW ALL 8 SECTIONS */}
        <div className="space-y-4" style={{ position: 'relative', clear: 'both' }}>
          {/* DEBUG: Show section count */}
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              📊 Sections loaded: {Object.keys(dashboardData?.sections || {}).length}/8 | 
              Expanded: {expandedSections.size}/8
            </p>
          </div>
          
          {/* 1. Profit & Loss Dashboard */}
          <CollapsibleSection
            sectionKey="profit_loss"
            title="Profit & Loss"
            icon={<BarChart3 className="h-6 w-6" />}
            isExpanded={expandedSections.has("profit_loss")}
            onToggle={toggleSection}
            summary={getSectionSummary(
              dashboardData.sections.profit_loss,
              `${dashboardData.sections.profit_loss?.charts?.length || 0} chart(s) showing Revenue, Expenses, EBITDA, Net Profit, PAT, and Margin trends`
            )}
          >
            {/* KPI Cards */}
            <ProfitLossKPIs data={dashboardData.sections.profit_loss?.data} hideFY2025={true} />
            
            {/* Charts */}
            {dashboardData.sections.profit_loss?.charts && dashboardData.sections.profit_loss.charts.length > 0 ? (
              <div className="space-y-8" style={{ position: 'relative', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections.profit_loss.charts.map((chart, idx) => (
                  <ChartCard key={idx} chart={chart} />
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Extracting financial data from documents...</p>
                <p className="text-xs mt-2">Please wait while we analyze the financial statements.</p>
              </div>
            )}
            
            {/* Summary AFTER visualizations */}
            {dashboardData.sections.profit_loss?.summary && (
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {dashboardData.sections.profit_loss.summary}
                </p>
              </div>
            )}
            
            {dashboardData.sections.profit_loss?.insights && dashboardData.sections.profit_loss.insights.length > 0 && (
              <div className="mt-4 p-4 bg-[#F8FAFC] border-l-4 border-[#2563EB] rounded-lg">
                <p className="text-sm text-[#111827]">{dashboardData.sections.profit_loss.insights.join(" ")}</p>
              </div>
            )}
          </CollapsibleSection>

          {/* 2. Balance Sheet Dashboard */}
          <CollapsibleSection
            sectionKey="balance_sheet"
            title="Balance Sheet"
            icon={<Building2 className="h-6 w-6" />}
            isExpanded={expandedSections.has("balance_sheet")}
            onToggle={toggleSection}
            summary={getSectionSummary(
              dashboardData.sections.balance_sheet,
              `${dashboardData.sections.balance_sheet?.charts?.length || 0} chart(s) showing Total Assets, Current vs Non-Current Assets, Current vs Non-Current Liabilities, and Shareholder structure`
            )}
          >
            {/* KPI Cards */}
            <BalanceSheetKPIs data={dashboardData.sections.balance_sheet?.data} hideFY2025={true} />
            
            {/* Charts */}
            {dashboardData.sections.balance_sheet?.charts && dashboardData.sections.balance_sheet.charts.length > 0 ? (
              <div className="space-y-8" style={{ position: 'relative', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections.balance_sheet.charts.map((chart, idx) => (
                  <ChartCard key={idx} chart={chart} />
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Extracting balance sheet data from documents...</p>
                <p className="text-xs mt-2">Analyzing assets, liabilities, and equity information.</p>
              </div>
            )}
            
            {/* Summary AFTER visualizations */}
            {dashboardData.sections.balance_sheet?.summary && (
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {dashboardData.sections.balance_sheet.summary}
                </p>
              </div>
            )}
            
            {dashboardData.sections.balance_sheet?.insights && dashboardData.sections.balance_sheet.insights.length > 0 && (
              <div className="mt-4 p-4 bg-[#F8FAFC] border-l-4 border-[#2563EB] rounded-lg">
                <p className="text-sm text-[#111827]">{dashboardData.sections.balance_sheet.insights.join(" ")}</p>
              </div>
            )}
          </CollapsibleSection>

          {/* 3. Cash Flow */}
          <CollapsibleSection
            sectionKey="cash_flow"
            title="Cash Flow"
            isExpanded={expandedSections.has("cash_flow")}
            onToggle={toggleSection}
            summary={getSectionSummary(
              dashboardData.sections.cash_flow,
              `${dashboardData.sections.cash_flow?.charts?.length || 0} chart(s) showing Operating, Investing, and Financing Cash Flow trends`
            )}
          >
            {dashboardData.sections.cash_flow?.charts && dashboardData.sections.cash_flow.charts.length > 0 ? (
              <div className="space-y-8" style={{ position: 'relative', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections.cash_flow.charts.map((chart, idx) => (
                  <ChartCard key={idx} chart={chart} />
                ))}
                {/* Summary AFTER visualizations */}
                {dashboardData.sections.cash_flow?.summary && (
                  <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                    <p className="text-sm text-[#6B7280] leading-relaxed">
                      {dashboardData.sections.cash_flow.summary}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Extracting cash flow data from documents...</p>
                <p className="text-xs mt-2">Analyzing operating, investing, and financing activities.</p>
              </div>
            )}
            {dashboardData.sections.cash_flow?.insights && (
              <div className="mt-4 p-4 bg-[#F8FAFC] border-l-4 border-[#2563EB] rounded-lg">
                <p className="text-sm text-[#111827]">{Array.isArray(dashboardData.sections.cash_flow.insights) ? dashboardData.sections.cash_flow.insights.join(" ") : dashboardData.sections.cash_flow.insights}</p>
              </div>
            )}
          </CollapsibleSection>

          {/* 4. Accounting Ratios Dashboard */}
          <CollapsibleSection
            sectionKey="accounting_ratios"
            title="Accounting Ratios"
            icon={<Target className="h-6 w-6" />}
            isExpanded={expandedSections.has("accounting_ratios")}
            onToggle={toggleSection}
            summary={getSectionSummary(
              dashboardData.sections.accounting_ratios,
              `${dashboardData.sections.accounting_ratios?.charts?.length || 0} chart(s) showing Current Ratio, ROE, ROCE, Operating Margin, and other key ratios`
            )}
          >
            {/* KPI Cards */}
            <AccountingRatiosKPIs data={dashboardData.sections.accounting_ratios?.data} hideFY2025={true} />
            
            {/* Charts */}
            {dashboardData.sections.accounting_ratios?.charts && dashboardData.sections.accounting_ratios.charts.length > 0 ? (
              <div className="space-y-8" style={{ position: 'relative', zIndex: 1, isolation: 'isolate' }}>
                {dashboardData.sections.accounting_ratios.charts.map((chart, idx) => (
                  <ChartCard key={idx} chart={chart} />
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Computing accounting ratios from financial data...</p>
                <p className="text-xs mt-2">Calculating ROE, ROCE, margins, and liquidity ratios.</p>
              </div>
            )}
            
            {/* Summary AFTER visualizations */}
            {dashboardData.sections.accounting_ratios?.summary && (
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed">
                  {dashboardData.sections.accounting_ratios.summary}
                </p>
              </div>
            )}
            
            {dashboardData.sections.accounting_ratios?.insights && dashboardData.sections.accounting_ratios.insights.length > 0 && (
              <div className="mt-4 p-4 bg-[#F8FAFC] border-l-4 border-[#2563EB] rounded-lg">
                <p className="text-sm text-[#111827]">{dashboardData.sections.accounting_ratios.insights.join(" ")}</p>
              </div>
            )}
          </CollapsibleSection>

          {/* 5. Management Highlights */}
          <CollapsibleSection
            sectionKey="management_highlights"
            title="Management & Business Highlights"
            isExpanded={expandedSections.has("management_highlights")}
            onToggle={toggleSection}
            summary={
              dashboardData.sections.management_highlights?.summary || 
              (dashboardData.sections.management_highlights?.insights && dashboardData.sections.management_highlights.insights.length > 0
                ? `${dashboardData.sections.management_highlights.insights.length} insight card(s) covering Management commentary, Strategy, and Key initiatives`
                : "Management highlights extracted from annual report and MD&A sections")
            }
          >
            {dashboardData.sections.management_highlights?.insights && dashboardData.sections.management_highlights.insights.length > 0 ? (
              <div className="space-y-4">
                {/* High Emphasis Insights */}
                {dashboardData.sections.management_highlights.insights
                  .filter(insight => insight.emphasis === 'high')
                  .map((insight, idx) => (
                    <Card key={`high-${idx}`} className="p-4 bg-gradient-to-r from-[#FEF3C7] to-[#F59E0B] border-2 border-[#F59E0B] shadow-lg rounded-xl">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-white rounded-lg">
                          <Target className="h-6 w-6 text-[#F59E0B]" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold mb-2 text-[#111827] text-lg">{insight.title}</h4>
                          <p className="text-sm text-[#374151] leading-relaxed">{insight.summary}</p>
                          <span className="text-xs text-[#F59E0B] mt-2 inline-block px-2 py-1 bg-[#F59E0B]/20 rounded-full font-semibold">
                            HIGH PRIORITY
                          </span>
                        </div>
                      </div>
                    </Card>
                  ))}
                
                {/* Medium Emphasis Insights */}
                {dashboardData.sections.management_highlights.insights
                  .filter(insight => insight.emphasis === 'medium')
                  .map((insight, idx) => (
                    <Card key={`medium-${idx}`} className="p-4 bg-gradient-to-r from-[#DBEAFE] to-[#BFDBFE] border border-[#3B82F6] shadow-md rounded-xl">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-white rounded-lg">
                          <BarChart3 className="h-5 w-5 text-[#3B82F6]" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-2 text-[#111827]">{insight.title}</h4>
                          <p className="text-sm text-[#374151] leading-relaxed">{insight.summary}</p>
                          <span className="text-xs text-[#3B82F6] mt-2 inline-block px-2 py-1 bg-[#3B82F6]/20 rounded-full font-medium">
                            MEDIUM PRIORITY
                          </span>
                        </div>
                      </div>
                    </Card>
                  ))}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Extracting management highlights from documents...</p>
                <p className="text-xs mt-2">Analyzing MD&A, CEO message, and strategic initiatives.</p>
              </div>
            )}
            
            {/* Summary AFTER visualizations */}
            {dashboardData.sections.management_highlights?.summary && (
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed whitespace-pre-line">
                  {dashboardData.sections.management_highlights.summary}
                </p>
              </div>
            )}
          </CollapsibleSection>

          {/* 6. Latest News */}
          <CollapsibleSection
            sectionKey="latest_news"
            title="Latest News"
            source={dashboardData.sections.latest_news?.source || "Document + Web Search"}
            isExpanded={expandedSections.has("latest_news")}
            onToggle={toggleSection}
            summary={
              dashboardData.sections.latest_news?.summary ||
              (dashboardData.sections.latest_news?.news && dashboardData.sections.latest_news.news.length > 0
                ? `${dashboardData.sections.latest_news.news.length} news article(s) from ${dashboardData.sections.latest_news.source || 'document and web search'} covering recent earnings, analyst commentary, and regulatory updates`
                : "Latest news and market updates extracted from documents and web sources")
            }
          >
            {/* Highlighted Section */}
            <div className="mb-4 p-3 bg-gradient-to-r from-[#FEF3C7] to-[#F59E0B] border border-[#F59E0B] rounded-lg">
              <div className="flex items-center gap-2">
                <Newspaper className="h-5 w-5 text-[#F59E0B]" />
                <span className="text-sm font-semibold text-[#111827]">📰 Latest News - Market Updates</span>
              </div>
            </div>
            
            {/* Source Badge - Prominently show data source */}
            {dashboardData.sections.latest_news?.source_badge && (
              <div className="mb-4 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-[#DBEAFE] text-[#1D4ED8] border border-[#2563EB]">
                {dashboardData.sections.latest_news.source_badge}
              </div>
            )}
            
            {dashboardData.sections.latest_news?.news && dashboardData.sections.latest_news.news.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.sections.latest_news.news.map((item, idx) => (
                  <Card key={idx} className="p-4 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl hover:shadow-lg transition-shadow">
                    <h4 className="font-semibold mb-2 text-[#111827]">{item.headline}</h4>
                    <p className="text-sm text-[#6B7280] mb-2">{item.summary}</p>
                    <div className="flex items-center justify-between text-xs">
                      {item.source && item.source !== "Document" && item.source.startsWith("http") ? (
                        <a
                          href={item.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#2563EB] hover:underline"
                        >
                          {new URL(item.source).hostname}
                        </a>
                      ) : (
                        <span className="text-[#6B7280]">{item.source || "Document"}</span>
                      )}
                      <span className="text-[#6B7280]">{item.date || "Recent"}</span>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Searching for latest news and market updates...</p>
                <p className="text-xs mt-2">Analyzing earnings reports, analyst commentary, and regulatory filings.</p>
              </div>
            )}
            
            {/* Summary AFTER visualizations */}
            {dashboardData.sections.latest_news?.summary && (
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed whitespace-pre-line">
                  {dashboardData.sections.latest_news.summary}
                </p>
              </div>
            )}
          </CollapsibleSection>

          {/* 7. Competitors */}
          <CollapsibleSection
            sectionKey="competitors"
            title="Competitors"
            source={dashboardData.sections.competitors?.source || "Document + Web Search"}
            isExpanded={expandedSections.has("competitors")}
            onToggle={toggleSection}
            summary={
              dashboardData.sections.competitors?.summary ||
              (dashboardData.sections.competitors?.competitors && dashboardData.sections.competitors.competitors.length > 0
                ? `${dashboardData.sections.competitors.competitors.length} competitor(s) identified from ${dashboardData.sections.competitors.source || 'document and web search'} with market positioning and comparative insights`
                : "Competitive landscape analysis from documents and market research")
            }
          >
            {/* Source Badge - Prominently show data source */}
            {dashboardData.sections.competitors?.source_badge && (
              <div className="mb-4 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-[#DBEAFE] text-[#1D4ED8] border border-[#2563EB]">
                {dashboardData.sections.competitors.source_badge}
              </div>
            )}
            
            {dashboardData.sections.competitors?.competitors && dashboardData.sections.competitors.competitors.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dashboardData.sections.competitors.competitors.map((comp, idx) => (
                  <Card key={idx} className="p-4 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
                    <h4 className="font-semibold mb-2 text-[#111827]">{comp.name}</h4>
                    <p className="text-sm text-[#6B7280] mb-2">{comp.insight}</p>
                    {comp.source && comp.source.startsWith("http") ? (
                      <a
                        href={comp.source}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-[#2563EB] hover:underline"
                      >
                        Source
                      </a>
                    ) : (
                      <span className="text-xs text-[#6B7280]">{comp.source || "Document"}</span>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Identifying competitors and market positioning...</p>
                <p className="text-xs mt-2">Analyzing competitive landscape from documents and market data.</p>
              </div>
            )}
            
            {/* Summary AFTER visualizations */}
            {dashboardData.sections.competitors?.summary && (
              <div className="mt-6 pt-6 border-t border-[#E5E7EB]">
                <p className="text-sm text-[#6B7280] leading-relaxed whitespace-pre-line">
                  {dashboardData.sections.competitors.summary}
                </p>
              </div>
            )}
          </CollapsibleSection>

          {/* 8. Investor POV Dashboard */}
          <CollapsibleSection
            sectionKey="investor_pov"
            title="Investor Perspective"
            icon={<Target className="h-6 w-6" />}
            isExpanded={expandedSections.has("investor_pov")}
            onToggle={toggleSection}
            summary={
              dashboardData.sections.investor_pov?.summary ||
              (dashboardData.sections.investor_pov?.charts && dashboardData.sections.investor_pov.charts.length > 0
                ? `${dashboardData.sections.investor_pov.charts.length} chart(s) showing ROE, ROCE, Dividend payout, Creditors, Debenture holders, FCF, and CAGR trends`
                : "Investor perspective analysis based on financial metrics and trends from the annual report")
            }
          >
            {dashboardData.sections.investor_pov ? (
              <div className="space-y-6">
                {/* KPI Cards */}
                <InvestorPOVKPIs data={dashboardData.sections.investor_pov} />
                
                {/* Charts */}
                {dashboardData.sections.investor_pov.charts && dashboardData.sections.investor_pov.charts.length > 0 ? (
                  <div className="space-y-8" style={{ position: 'relative', zIndex: 1, isolation: 'isolate' }}>
                    {dashboardData.sections.investor_pov.charts.map((chart, idx) => (
                      <ChartCard key={idx} chart={chart} />
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-center text-[#6B7280]">
                    <p className="text-sm">Analyzing investor metrics and trends...</p>
                    <p className="text-xs mt-2">Computing ROE, ROCE, dividend trends, and cash flow analysis.</p>
                  </div>
                )}
                
                {/* Trend Analysis */}
                {Object.keys(dashboardData.sections.investor_pov.trends || {}).length > 0 ? (
                  <div>
                    <h4 className="font-semibold mb-4 text-[#111827]">Trend Analysis</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.entries(dashboardData.sections.investor_pov.trends).map(([key, value]: [string, any]) => (
                        <Card key={key} className="p-4 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
                          <p className="text-sm text-[#6B7280] mb-1">{key.toUpperCase().replace(/_/g, ' ')}</p>
                          <div className="flex items-center gap-2">
                            {typeof value === 'string' && value.includes("Increasing") && <TrendingUp className="h-4 w-4 text-[#16A34A]" />}
                            {typeof value === 'string' && value.includes("Decreasing") && <TrendingDown className="h-4 w-4 text-[#DC2626]" />}
                            {typeof value === 'string' && value.includes("Stable") && <Minus className="h-4 w-4 text-[#D97706]" />}
                            <span className="font-semibold text-[#111827]">{value}</span>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* Summary */}
                {dashboardData.sections.investor_pov.summary ? (
                  <Card className="p-4 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
                    <h4 className="font-semibold mb-2 text-[#111827]">What This Means for Investors</h4>
                    <p className="text-sm text-[#6B7280]">{dashboardData.sections.investor_pov.summary}</p>
                  </Card>
                ) : null}

                {/* Bull Case */}
                {dashboardData.sections.investor_pov.bull_case?.length > 0 ? (
                  <Card className="p-4 bg-[#F0FDF4] border border-[#BBF7D0] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
                    <h4 className="font-semibold mb-3 text-[#16A34A]">Bull Case</h4>
                    <ul className="space-y-2">
                      {dashboardData.sections.investor_pov.bull_case.map((point, idx) => (
                        <li key={idx} className="text-sm flex items-start gap-2 text-[#111827]">
                          <span className="text-[#16A34A] mt-1">✓</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                ) : null}

                {/* Risk Factors */}
                {dashboardData.sections.investor_pov.risk_factors?.length > 0 ? (
                  <Card className="p-4 bg-[#FEF2F2] border border-[#FECACA] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
                    <h4 className="font-semibold mb-3 text-[#DC2626]">Risk Factors</h4>
                    <ul className="space-y-2">
                      {dashboardData.sections.investor_pov.risk_factors.map((risk, idx) => (
                        <li key={idx} className="text-sm flex items-start gap-2 text-[#111827]">
                          <span className="text-[#DC2626] mt-1">⚠</span>
                          <span>{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                ) : null}
              </div>
            ) : (
              <div className="p-4 text-center text-[#6B7280]">
                <p className="text-sm">Generating investor perspective analysis...</p>
                <p className="text-xs mt-2">Analyzing financial trends and investment outlook.</p>
              </div>
            )}
          </CollapsibleSection>

          {/* Show Full Dashboard Button */}
          <div className="mt-8 mb-8 flex justify-center" style={{ paddingBottom: '20px' }}>
            <button
              onClick={() => setShowFullDashboard(true)}
              className="flex items-center gap-2 px-6 py-3 bg-[#2563EB] text-white rounded-xl hover:bg-[#1D4ED8] transition-colors font-semibold shadow-[0_1px_3px_rgba(0,0,0,0.08)] z-20 relative"
              style={{ position: 'relative', zIndex: 20 }}
            >
              <Maximize2 className="h-5 w-5" />
              Show Full Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function CollapsibleSection({
  sectionKey,
  title,
  icon,
  source,
  isExpanded,
  onToggle,
  summary,
  children,
}: {
  sectionKey: string;
  title: string;
  icon?: React.ReactNode;
  source?: string;
  isExpanded: boolean;
  onToggle: (key: string) => void;
  summary: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="overflow-visible bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" style={{ position: 'relative', clear: 'both', minHeight: '100px', zIndex: 1 }}>
      <button
        onClick={() => onToggle(sectionKey)}
        className="w-full flex items-center justify-between p-6 hover:bg-[#F3F4F6] transition-colors text-left"
      >
        <div className="flex items-center gap-3 flex-1">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-[#6B7280]" />
            ) : (
              <ChevronDown className="h-5 w-5 text-[#6B7280]" />
            )}
            {icon && <div className="text-[#6B7280]">{icon}</div>}
            <h2 className="text-2xl font-bold text-[#111827]">{title}</h2>
          </div>
          {source && (
            <span className="text-xs px-2 py-1 bg-[#DBEAFE] rounded-md text-[#1D4ED8]">
              {source}
            </span>
          )}
        </div>
      </button>
      
      {!isExpanded && (
        <div className="px-6 pb-4">
          <p className="text-sm text-[#6B7280]">{summary}</p>
        </div>
      )}
      
      {isExpanded && (
        <div className="px-6 pb-6 pt-2 border-t border-[#E5E7EB]">
          {children}
        </div>
      )}
    </Card>
  );
}

// Helper to check if value is valid number
const isValidNumber = (val: any): boolean => {
  return val !== null && 
         val !== undefined && 
         val !== "N/A" && 
         typeof val === "number" && 
         !isNaN(val) && 
         isFinite(val);
};

function ChartCard({ chart }: { chart: any }): JSX.Element | null {
  // CRITICAL: Validate chart has valid data before rendering - NO EMPTY CHARTS
  if (!chart) {
    return null;
  }
  
  // Convert chart format to SimpleChart format
  const chartProps: any = {
    type: chart.type || chart.chart_type || "bar",
    title: chart.title,
    labels: chart.labels || [],
    values: chart.values || [],
    xAxis: chart.xAxis,
    yAxis: chart.yAxis,
  };

  // Handle grouped/stacked bar charts
  if (chart.groups) {
    chartProps.type = "stacked_bar";
    chartProps.groups = chart.groups;
  } else if (chart.datasets && Array.isArray(chart.datasets) && chart.datasets.length > 0) {
    // Multi-line or multi-bar chart
    chartProps.type = chart.type === "line" ? "line" : "bar";
    // For now, use first dataset - can enhance SimpleChart to support multiple datasets
    chartProps.labels = chart.labels || [];
    // Ensure data exists and is an array
    const datasetData = chart.datasets[0]?.data;
    chartProps.values = Array.isArray(datasetData) ? datasetData : [];
  }

  // Final validation: ensure values is always an array
  if (!Array.isArray(chartProps.values)) {
    chartProps.values = [];
  }
  if (!Array.isArray(chartProps.labels)) {
    chartProps.labels = [];
  }
  
  // CRITICAL: Hide chart if no valid data - NO EMPTY CHARTS
  if (chartProps.labels.length === 0 || chartProps.values.length === 0) {
    return null;
  }
  
  // CRITICAL: Hide chart if all values are invalid (NaN, null, undefined, or all zeros)
  const validValues = chartProps.values.filter(isValidNumber);
  
  if (validValues.length === 0) {
    return null; // Hide chart if no valid values
  }
  
  // Ensure labels and values arrays match length
  const minLength = Math.min(chartProps.labels.length, validValues.length);
  chartProps.labels = chartProps.labels.slice(0, minLength);
  chartProps.values = validValues.slice(0, minLength);
  chartProps.values = validValues.slice(0, minLength);

  return (
    <Card 
      className="p-6 mb-6 bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl" 
      style={{ 
        position: 'relative', 
        overflow: 'visible', 
        minHeight: '450px',
        zIndex: 1,
        isolation: 'isolate'
      }}
    >
      <div 
        style={{ 
          width: '100%', 
          height: '100%', 
          overflow: 'visible',
          position: 'relative',
          zIndex: 2
        }}
      >
        <SimpleChart {...chartProps} />
      </div>
    </Card>
  );
}

