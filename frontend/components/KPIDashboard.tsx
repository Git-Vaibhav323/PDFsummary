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
export function ProfitLossKPIs({ data }: { data: any }) {
  const getLatestValue = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    if (years.length === 0) return null;
    const value = fieldData[years[years.length - 1]];
    // Allow all numeric values including 0 and negatives
    return (value !== undefined && value !== null && typeof value === "number") ? value : null;
  };

  const getYoYGrowth = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    if (years.length < 2) return null;
    const latest = fieldData[years[years.length - 1]];
    const previous = fieldData[years[years.length - 2]];
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
        <p className="text-sm">Profit & Loss metrics not disclosed in report</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {kpiCards}
    </div>
  );
}

// Balance Sheet KPIs
export function BalanceSheetKPIs({ data }: { data: any }) {
  const getLatestValue = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    if (years.length === 0) return null;
    const value = fieldData[years[years.length - 1]];
    // Allow all numeric values including 0 and negatives
    return (value !== undefined && value !== null && typeof value === "number") ? value : null;
  };

  const totalAssets = getLatestValue("total_assets");
  const currentLiabilities = getLatestValue("current_liabilities");
  const nonCurrentLiabilities = getLatestValue("non_current_liabilities");
  const totalLiabilities = (currentLiabilities ?? 0) + (nonCurrentLiabilities ?? 0);
  const netWorth = totalAssets !== null ? (totalAssets - totalLiabilities) : null;
  const debtEquityRatio = totalLiabilities > 0 && netWorth !== null && netWorth > 0 
    ? (totalLiabilities / netWorth) 
    : null;

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  if (totalAssets !== null && totalAssets !== undefined) {
    kpiCards.push(
      <KPICard
        key="assets"
        title="Total Assets"
        value={totalAssets}
        icon={<Building2 className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (totalLiabilities > 0) {
    kpiCards.push(
      <KPICard
        key="liabilities"
        title="Total Liabilities"
        value={totalLiabilities}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (netWorth !== null && netWorth !== undefined) {
    kpiCards.push(
      <KPICard
        key="netWorth"
        title="Net Worth"
        value={netWorth}
        icon={<DollarSign className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (debtEquityRatio !== null && debtEquityRatio !== undefined && debtEquityRatio > 0) {
    kpiCards.push(
      <KPICard
        key="debtEquity"
        title="Debt-Equity Ratio"
        value={debtEquityRatio}
        icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
        format="number"
        suffix=":1"
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

// Cash Flow KPIs
export function CashFlowKPIs({ data }: { data: any }) {
  const getLatestValue = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    if (years.length === 0) return null;
    const value = fieldData[years[years.length - 1]];
    return value !== undefined && value !== null ? value : null; // Allow negative values for cash flow
  };

  const operatingCF = getLatestValue("operating_cash_flow");
  const investingCF = getLatestValue("investing_cash_flow");
  const financingCF = getLatestValue("financing_cash_flow");
  const freeCashFlow = operatingCF !== null && investingCF !== null 
    ? operatingCF + investingCF 
    : null; // Simplified FCF calculation

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  if (operatingCF !== null && operatingCF !== undefined) {
    kpiCards.push(
      <KPICard
        key="operating"
        title="Operating CF"
        value={operatingCF}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (investingCF !== null && investingCF !== undefined) {
    kpiCards.push(
      <KPICard
        key="investing"
        title="Investing CF"
        value={investingCF}
        icon={<TrendingDown className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (financingCF !== null && financingCF !== undefined) {
    kpiCards.push(
      <KPICard
        key="financing"
        title="Financing CF"
        value={financingCF}
        icon={<TrendingUp className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
      />
    );
  }
  
  if (freeCashFlow !== null && freeCashFlow !== undefined) {
    kpiCards.push(
      <KPICard
        key="fcf"
        title="Free Cash Flow"
        value={freeCashFlow}
        icon={<DollarSign className="h-5 w-5 text-[#6B7280]" />}
        format="currency"
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

// Accounting Ratios KPIs
export function AccountingRatiosKPIs({ data }: { data: any }) {
  const getLatestValue = (field: string): number | null => {
    const fieldData = data?.[field];
    if (!fieldData || typeof fieldData !== "object") return null;
    const years = Object.keys(fieldData).sort();
    if (years.length === 0) return null;
    const value = fieldData[years[years.length - 1]];
    // Allow all numeric values including 0 and negatives
    return (value !== undefined && value !== null && typeof value === "number") ? value : null;
  };

  const roe = getLatestValue("roe");
  const roce = getLatestValue("roce");
  const operatingMargin = getLatestValue("operating_margin");
  const currentRatio = getLatestValue("current_ratio");
  const netDebtEBITDA = getLatestValue("net_debt_ebitda");

  // Only render cards with valid data - NO N/A VALUES
  const kpiCards = [];
  
  if (roe !== null && roe !== undefined) {
    kpiCards.push(
      <KPICard
        key="roe"
        title="ROE"
        value={roe}
        icon={<Target className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  if (roce !== null && roce !== undefined) {
    kpiCards.push(
      <KPICard
        key="roce"
        title="ROCE"
        value={roce}
        icon={<Target className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  if (operatingMargin !== null && operatingMargin !== undefined) {
    kpiCards.push(
      <KPICard
        key="opMargin"
        title="Operating Margin"
        value={operatingMargin}
        icon={<BarChart3 className="h-5 w-5 text-[#6B7280]" />}
        format="percentage"
      />
    );
  }
  
  if (currentRatio !== null && currentRatio !== undefined && currentRatio > 0) {
    kpiCards.push(
      <KPICard
        key="currentRatio"
        title="Current Ratio"
        value={currentRatio}
        icon={<Activity className="h-5 w-5 text-[#6B7280]" />}
        format="number"
        suffix=":1"
      />
    );
  }
  
  if (netDebtEBITDA !== null && netDebtEBITDA !== undefined) {
    kpiCards.push(
      <KPICard
        key="netDebt"
        title="Net Debt/EBITDA"
        value={netDebtEBITDA}
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

