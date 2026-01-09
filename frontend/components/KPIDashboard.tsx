"use client";

import { TrendingUp, TrendingDown, Minus, DollarSign, Activity, BarChart3, PieChart, Users, Newspaper, Building2, Target } from "lucide-react";
import { Card } from "./ui/card";

// KPI Card Component - HIDES if value is null/undefined (no N/A display)
export function KPICard({ 
  title, 
  value, 
  change, 
  icon, 
  format = "number",
  suffix = ""
}: { 
  title: string; 
  value: number | string | null; 
  change?: number | null; 
  icon?: React.ReactNode;
  format?: "number" | "percentage" | "currency";
  suffix?: string;
}) {
  // CRITICAL: Hide card if value is null/undefined/invalid - NO N/A DISPLAY
  if (value === null || value === undefined || value === "N/A") {
    return null;
  }
  
  // If string value is "N/A", hide the card
  if (typeof value === "string" && value.trim() === "N/A") {
    return null;
  }
  
  const formatValue = (val: number | string | null): string => {
    if (val === null || val === undefined) return ""; // Should never reach here due to check above
    if (typeof val === "string") return val;
    // Ensure val is a number before calling number methods
    if (typeof val !== "number" || isNaN(val) || !isFinite(val)) return ""; // Hide invalid numbers
    if (format === "percentage") return `${val.toFixed(1)}%`;
    if (format === "currency") {
      if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
      if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
      return `₹${val.toLocaleString()}`;
    }
    if (val >= 10000000) return `${(val / 10000000).toFixed(1)}Cr`;
    if (val >= 100000) return `${(val / 100000).toFixed(1)}L`;
    return val.toLocaleString();
  };

  const displayValue = formatValue(value) + (suffix && value !== null && value !== "N/A" ? ` ${suffix}` : "");
  
  // Double-check: if formatted value is empty, hide card
  if (!displayValue || displayValue.trim() === "") {
    return null;
  }

  return (
    <Card className="p-4 hover:shadow-md transition-shadow bg-white border border-[#E5E7EB] shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-[#6B7280] mb-1">{title}</p>
          <p className="text-2xl font-bold text-[#111827]">
            {displayValue}
          </p>
          {change !== undefined && change !== null && (
            <div className="flex items-center gap-1 mt-2">
              {change > 0 ? (
                <TrendingUp className="h-4 w-4 text-[#16A34A]" />
              ) : change < 0 ? (
                <TrendingDown className="h-4 w-4 text-[#DC2626]" />
              ) : (
                <Minus className="h-4 w-4 text-[#D97706]" />
              )}
              <span className={`text-xs font-medium ${
                change > 0 ? "text-[#16A34A]" : change < 0 ? "text-[#DC2626]" : "text-[#D97706]"
              }`}>
                {change > 0 ? "+" : ""}{change.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
        {icon && (
          <div className="p-2 bg-[#E0E7FF] rounded-lg">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}

// Profit & Loss KPIs
export function ProfitLossKPIs({ data, hideFY2025 = false }: { data: any; hideFY2025?: boolean }) {
  const getLatestValue = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    // Filter out FY2025 if hideFY2025 is true
    const filteredYears = hideFY2025 ? years.filter(year => !year.includes('2025')) : years;
    if (filteredYears.length === 0) return null;
    const value = fieldData[filteredYears[filteredYears.length - 1]];
    // Allow all numeric values including 0 and negatives
    return (value !== undefined && value !== null && typeof value === "number") ? value : null;
  };

  const getYoYGrowth = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    // Filter out FY2025 if hideFY2025 is true
    const filteredYears = hideFY2025 ? years.filter(year => !year.includes('2025')) : years;
    if (filteredYears.length < 2) return null;
    const latest = fieldData[filteredYears[filteredYears.length - 1]];
    const previous = fieldData[filteredYears[filteredYears.length - 2]];
    if (latest === undefined || latest === null || previous === undefined || previous === null || previous === 0) return null;
    return ((latest - previous) / previous) * 100;
  };

  const revenue = getLatestValue("revenue");
  const ebitda = getLatestValue("ebitda");
  const netProfit = getLatestValue("net_profit");
  const pat = getLatestValue("pat");
  const revenueGrowth = getYoYGrowth("revenue");

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  if (revenue !== null && revenue !== undefined) {
    kpiCards.push(
      <KPICard
        key="revenue"
        title="Total Revenue"
        value={revenue}
        change={revenueGrowth ?? undefined}
        icon={<DollarSign className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (ebitda !== null && ebitda !== undefined) {
    kpiCards.push(
      <KPICard
        key="ebitda"
        title="EBITDA"
        value={ebitda}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (netProfit !== null && netProfit !== undefined) {
    kpiCards.push(
      <KPICard
        key="netProfit"
        title="Net Profit"
        value={netProfit}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (pat !== null && pat !== undefined) {
    kpiCards.push(
      <KPICard
        key="pat"
        title="PAT"
        value={pat}
        icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (revenueGrowth !== null && revenueGrowth !== undefined) {
    kpiCards.push(
      <KPICard
        key="growth"
        title="YoY Growth"
        value={revenueGrowth}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }

  if (kpiCards.length === 0) {
    return (
      <div className="p-4 text-center text-[#6B7280] mb-6">
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {kpiCards}
    </div>
  );
}

// Balance Sheet KPIs - YEAR-WISE with Growth %
export function BalanceSheetKPIs({ data, hideFY2025 = false }: { data: any; hideFY2025?: boolean }) {
  const getYearWiseValues = (field: string): { [year: string]: number } | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const result: { [year: string]: number } = {};
    Object.keys(fieldData).sort().forEach(year => {
      // Filter out FY2025 if hideFY2025 is true
      if (hideFY2025 && year.includes('2025')) return;
      const value = fieldData[year];
      if (value !== undefined && value !== null && typeof value === "number") {
        result[year] = value;
      }
    });
    return Object.keys(result).length > 0 ? result : null;
  };

  const getGrowth = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    // Filter out FY2025 if hideFY2025 is true
    const filteredYears = hideFY2025 ? years.filter(year => !year.includes('2025')) : years;
    if (filteredYears.length < 2) return null;
    const latest = fieldData[filteredYears[filteredYears.length - 1]];
    const previous = fieldData[filteredYears[filteredYears.length - 2]];
    if (latest === undefined || latest === null || previous === undefined || previous === null || previous === 0) return null;
    return ((latest - previous) / previous) * 100;
  };

  const totalAssetsByYear = getYearWiseValues("total_assets");
  const currentLiabilitiesByYear = getYearWiseValues("current_liabilities");
  const nonCurrentLiabilitiesByYear = getYearWiseValues("non_current_liabilities");
  const shareholderEquityByYear = getYearWiseValues("shareholder_equity");
  
  // Calculate total liabilities by year
  const totalLiabilitiesByYear: { [year: string]: number } = {};
  if (currentLiabilitiesByYear || nonCurrentLiabilitiesByYear) {
    const allYears = new Set([
      ...(currentLiabilitiesByYear ? Object.keys(currentLiabilitiesByYear) : []),
      ...(nonCurrentLiabilitiesByYear ? Object.keys(nonCurrentLiabilitiesByYear) : [])
    ]);
    allYears.forEach(year => {
      totalLiabilitiesByYear[year] = 
        (currentLiabilitiesByYear?.[year] || 0) + (nonCurrentLiabilitiesByYear?.[year] || 0);
    });
  }
  
  // Calculate growth percentages
  const assetGrowth = getGrowth("total_assets");
  const liabilityGrowth = getGrowth("total_liabilities");
  const equityGrowth = getGrowth("shareholder_equity");

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  // Total Assets (Year-wise) - show multiple years
  if (totalAssetsByYear && Object.keys(totalAssetsByYear).length > 0) {
    const years = Object.keys(totalAssetsByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="assets"
        title={`Total Assets (${years.length} years)`}
        value={totalAssetsByYear[latestYear]}
        change={assetGrowth ?? undefined}
        icon={<Building2 className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }
  
  // Total Liabilities (Year-wise) - show multiple years
  if (Object.keys(totalLiabilitiesByYear).length > 0) {
    const years = Object.keys(totalLiabilitiesByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="liabilities"
        title={`Total Liabilities (${years.length} years)`}
        value={totalLiabilitiesByYear[latestYear]}
        change={liabilityGrowth ?? undefined}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }
  
  // Shareholders' Equity (Year-wise) - show multiple years
  if (shareholderEquityByYear && Object.keys(shareholderEquityByYear).length > 0) {
    const years = Object.keys(shareholderEquityByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="equity"
        title={`Shareholders' Equity (${years.length} years)`}
        value={shareholderEquityByYear[latestYear]}
        change={equityGrowth ?? undefined}
        icon={<DollarSign className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }
  
  // Asset Growth %
  if (assetGrowth !== null && assetGrowth !== undefined) {
    kpiCards.push(
      <KPICard
        key="assetGrowth"
        title="Asset Growth %"
        value={assetGrowth}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  // Liability Growth %
  if (liabilityGrowth !== null && liabilityGrowth !== undefined) {
    kpiCards.push(
      <KPICard
        key="liabilityGrowth"
        title="Liability Growth %"
        value={liabilityGrowth}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  // Equity Growth %
  if (equityGrowth !== null && equityGrowth !== undefined) {
    kpiCards.push(
      <KPICard
        key="equityGrowth"
        title="Equity Growth %"
        value={equityGrowth}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }

  if (kpiCards.length === 0) {
    return (
      <div className="p-4 text-center text-[#6B7280] mb-6">
        <p className="text-sm">Balance Sheet metrics not disclosed in report</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {kpiCards}
    </div>
  );
}

// Cash Flow KPIs - YEAR-WISE with separate activities
export function CashFlowKPIs({ data, hideFY2025 = false }: { data: any; hideFY2025?: boolean }) {
  const getYearWiseValues = (field: string): { [year: string]: number } | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const result: { [year: string]: number } = {};
    Object.keys(fieldData).sort().forEach(year => {
      // Filter out FY2025 if hideFY2025 is true
      if (hideFY2025 && year.includes('2025')) return;
      const value = fieldData[year];
      if (value !== undefined && value !== null && typeof value === "number") {
        result[year] = value;
      }
    });
    return Object.keys(result).length > 0 ? result : null;
  };

  const operatingCFByYear = getYearWiseValues("operating_cash_flow");
  const investingCFByYear = getYearWiseValues("investing_cash_flow");
  const financingCFByYear = getYearWiseValues("financing_cash_flow");
  const cashEquivalentsByYear = getYearWiseValues("cash_and_equivalents");

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  // Cash flow from Operating Activity (Year-wise)
  if (operatingCFByYear && Object.keys(operatingCFByYear).length > 0) {
    const years = Object.keys(operatingCFByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="operating"
        title={`Cash flow from Operating Activity (${years.length} years)`}
        value={operatingCFByYear[latestYear]}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }
  
  // Cash Flow from Investing Activities (Year-wise)
  if (investingCFByYear && Object.keys(investingCFByYear).length > 0) {
    const years = Object.keys(investingCFByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="investing"
        title={`Investing CF (${years.length} years)`}
        value={investingCFByYear[latestYear]}
        icon={<TrendingDown className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }
  
  // Cash Flow from Financing Activities (Year-wise)
  if (financingCFByYear && Object.keys(financingCFByYear).length > 0) {
    const years = Object.keys(financingCFByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="financing"
        title={`Financing CF (${years.length} years)`}
        value={financingCFByYear[latestYear]}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }
  
  // Cash & Cash Equivalents (Year-wise)
  if (cashEquivalentsByYear && Object.keys(cashEquivalentsByYear).length > 0) {
    const years = Object.keys(cashEquivalentsByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="cashEquivalents"
        title={`Cash & Equivalents (${years.length} years)`}
        value={cashEquivalentsByYear[latestYear]}
        icon={<DollarSign className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
        suffix={`FY${latestYear}`}
      />
    );
  }

  if (kpiCards.length === 0) {
    return (
      <div className="p-4 text-center text-[#6B7280] mb-6">
        <p className="text-sm">Cash Flow metrics not disclosed in report</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {kpiCards}
    </div>
  );
}

// Accounting Ratios KPIs - YEAR-WISE with individual ratios
export function AccountingRatiosKPIs({ data, hideFY2025 = false }: { data: any; hideFY2025?: boolean }) {
  const getYearWiseValues = (field: string): { [year: string]: number } | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const result: { [year: string]: number } = {};
    Object.keys(fieldData).sort().forEach(year => {
      // Filter out FY2025 if hideFY2025 is true
      if (hideFY2025 && year.includes('2025')) return;
      const value = fieldData[year];
      if (value !== undefined && value !== null && typeof value === "number") {
        result[year] = value;
      }
    });
    return Object.keys(result).length > 0 ? result : null;
  };

  const getYearOverYearChange = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    // Filter out FY2025 if hideFY2025 is true
    const filteredYears = hideFY2025 ? years.filter(year => !year.includes('2025')) : years;
    if (filteredYears.length < 2) return null;
    const latest = fieldData[filteredYears[filteredYears.length - 1]];
    const previous = fieldData[filteredYears[filteredYears.length - 2]];
    if (latest === undefined || latest === null || previous === undefined || previous === null || previous === 0) return null;
    return ((latest - previous) / previous) * 100;
  };

  const roeByYear = getYearWiseValues("roe");
  const roceByYear = getYearWiseValues("roce");
  const operatingMarginByYear = getYearWiseValues("operating_margin");
  const currentRatioByYear = getYearWiseValues("current_ratio");
  const netDebtEBITDAByYear = getYearWiseValues("net_debt_ebitda");

  // Calculate year-over-year changes
  const roeChange = getYearOverYearChange("roe");
  const roceChange = getYearOverYearChange("roce");
  const operatingMarginChange = getYearOverYearChange("operating_margin");
  const currentRatioChange = getYearOverYearChange("current_ratio");
  const netDebtEBITDAChange = getYearOverYearChange("net_debt_ebitda");

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  // ROE (Return on Equity) - MANDATORY
  if (roeByYear && Object.keys(roeByYear).length > 0) {
    const years = Object.keys(roeByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="roe"
        title={`ROE – FY${latestYear}`}
        value={roeByYear[latestYear]}
        change={roeChange ?? undefined}
        icon={<Target className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  // ROCE (Return on Capital Employed) - MANDATORY
  if (roceByYear && Object.keys(roceByYear).length > 0) {
    const years = Object.keys(roceByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="roce"
        title={`ROCE – FY${latestYear}`}
        value={roceByYear[latestYear]}
        change={roceChange ?? undefined}
        icon={<Target className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  // Current Ratio - MANDATORY
  if (currentRatioByYear && Object.keys(currentRatioByYear).length > 0) {
    const years = Object.keys(currentRatioByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="currentRatio"
        title={`Current Ratio – FY${latestYear}`}
        value={currentRatioByYear[latestYear]}
        change={currentRatioChange ?? undefined}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="number"
        suffix=":1"
      />
    );
  }
  
  // Debt-to-Equity Ratio - MANDATORY
  if (data?.debt_equity_ratio || data?.debt_to_equity_ratio) {
    const debtToEquityData = getYearWiseValues("debt_equity_ratio") || getYearWiseValues("debt_to_equity_ratio");
    if (debtToEquityData && Object.keys(debtToEquityData).length > 0) {
      const years = Object.keys(debtToEquityData).sort();
      const latestYear = years[years.length - 1];
      const debtToEquityChange = getYearOverYearChange("debt_equity_ratio") || getYearOverYearChange("debt_to_equity_ratio");
      kpiCards.push(
        <KPICard
          key="debtToEquity"
          title={`Debt-to-Equity Ratio – FY${latestYear}`}
          value={debtToEquityData[latestYear]}
          change={debtToEquityChange ?? undefined}
          icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
          format="number"
          suffix=":1"
        />
      );
    }
  }
  
  // Operating Margin - IF AVAILABLE
  if (operatingMarginByYear && Object.keys(operatingMarginByYear).length > 0) {
    const years = Object.keys(operatingMarginByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="operatingMargin"
        title={`Operating Margin – FY${latestYear}`}
        value={operatingMarginByYear[latestYear]}
        change={operatingMarginChange ?? undefined}
        icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  // Net Margin - IF AVAILABLE (check if we have net_margin data)
  const netMarginByYear = getYearWiseValues("net_margin");
  if (netMarginByYear && Object.keys(netMarginByYear).length > 0) {
    const years = Object.keys(netMarginByYear).sort();
    const latestYear = years[years.length - 1];
    const netMarginChange = getYearOverYearChange("net_margin");
    kpiCards.push(
      <KPICard
        key="netMargin"
        title={`Net Margin – FY${latestYear}`}
        value={netMarginByYear[latestYear]}
        change={netMarginChange ?? undefined}
        icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  // Net Debt/EBITDA - IF AVAILABLE
  if (netDebtEBITDAByYear && Object.keys(netDebtEBITDAByYear).length > 0) {
    const years = Object.keys(netDebtEBITDAByYear).sort();
    const latestYear = years[years.length - 1];
    kpiCards.push(
      <KPICard
        key="netDebtEBITDA"
        title={`Net Debt/EBITDA – FY${latestYear}`}
        value={netDebtEBITDAByYear[latestYear]}
        change={netDebtEBITDAChange ?? undefined}
        icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
        format="number"
      />
    );
  }

  if (kpiCards.length === 0) {
    return (
      <div className="p-4 text-center text-[#6B7280] mb-6">
        <p className="text-sm">Accounting ratios not disclosed in report</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {kpiCards}
    </div>
  );
}

// Investor POV KPIs
export function InvestorPOVKPIs({ data }: { data: any }) {
  const trends = data?.trends || {};
  const metrics = data?.metrics || {};  // Single values for KPIs
  const metricsByYear = data?.metrics_by_year || {};  // Year-by-year data
  
  // Extract latest value from year-by-year data if single value not available
  const getLatestValue = (key: string): number | null => {
    // First try single value from metrics
    if (metrics[key] !== undefined && metrics[key] !== null) {
      return typeof metrics[key] === 'number' ? metrics[key] : null;
    }
    
    // Fallback: extract latest from year-by-year data
    const yearData = metricsByYear[key];
    if (yearData && typeof yearData === 'object' && !Array.isArray(yearData)) {
      const years = Object.keys(yearData).sort();
      if (years.length > 0) {
        const latestYear = years[years.length - 1];
        const value = yearData[latestYear];
        return typeof value === 'number' ? value : null;
      }
    }
    
    // Last resort: check trends (but these are strings like "Increasing")
    return null;
  };
  
  // Calculate trend change for display
  const getTrendChange = (key: string): number | undefined => {
    const yearData = metricsByYear[key];
    if (yearData && typeof yearData === 'object' && !Array.isArray(yearData)) {
      const years = Object.keys(yearData).sort();
      if (years.length >= 2) {
        const firstVal = yearData[years[0]];
        const lastVal = yearData[years[years.length - 1]];
        if (typeof firstVal === 'number' && typeof lastVal === 'number' && firstVal > 0) {
          return ((lastVal - firstVal) / firstVal) * 100;
        }
      }
    }
    return undefined;
  };

  const roe = getLatestValue("roe");
  const roce = getLatestValue("roce");
  const dividendPayout = getLatestValue("dividend_payout");
  const fcf = getLatestValue("fcf");
  const cagr = getLatestValue("cagr") || metrics["revenue_cagr"] || metrics["profit_cagr"] || null;

  // Only show cards with actual data (hide if null)
  const kpiCards = [];
  
  if (roe !== null) {
    kpiCards.push(
      <KPICard
        key="roe"
        title="ROE"
        value={roe}
        change={getTrendChange("roe")}
        icon={<Target className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  if (roce !== null) {
    kpiCards.push(
      <KPICard
        key="roce"
        title="ROCE"
        value={roce}
        change={getTrendChange("roce")}
        icon={<Target className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  if (dividendPayout !== null) {
    kpiCards.push(
      <KPICard
        key="dividend"
        title="Dividend Payout"
        value={dividendPayout}
        change={getTrendChange("dividend_payout")}
        icon={<DollarSign className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  if (fcf !== null) {
    kpiCards.push(
      <KPICard
        key="fcf"
        title="Free Cash Flow"
        value={fcf}
        change={getTrendChange("fcf")}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (cagr !== null) {
    kpiCards.push(
      <KPICard
        key="cagr"
        title="CAGR"
        value={cagr}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }

  if (kpiCards.length === 0) {
    return (
      <div className="p-4 text-center text-[#6B7280] mb-6">
        <p className="text-sm">Investor metrics not disclosed in report</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {kpiCards}
    </div>
  );
}

