# Production-Grade Financial Dashboard Refactor

## Status: IN PROGRESS

This document tracks the comprehensive refactor to implement production-grade financial dashboard with:
- Multi-stage extraction pipeline (Raw → OCR → Normalization → JSON Schema)
- Document-scoped dashboards (no stale data)
- Strict section requirements
- JSON schema validation (≥90% metrics populated)

## Implementation Plan

### ✅ Completed
1. Multi-document bug fix: Clear cache on new upload
2. API route updated to force fresh extraction

### 🔄 In Progress
1. Multi-stage extraction pipeline enhancement
2. Section-specific updates per strict requirements
3. JSON schema validation

### 📋 Pending
1. Frontend updates for document-scoped dashboards
2. Full dashboard view improvements

## Critical Requirements

### 1. Multi-Stage Extraction Pipeline
- Stage 1: Raw Ingestion (text + table + layout)
- Stage 2: OCR Fallback (if tables missing/incomplete)
- Stage 3: Financial Normalization (synonym mapping)
- Stage 4: JSON Financial Schema (structured output)

### 2. Section Requirements

#### Profit & Loss
- ✅ Year-wise ONLY (no single values)
- ✅ Specific metrics: Revenue, Expenses, EBITDA, Net Profit, PAT
- ✅ Margin trends: Gross, Operating, Net
- ✅ Individual charts for each metric

#### Balance Sheet
- ❌ Remove "Net Worth" terminology
- ✅ Use: Total Assets, Total Liabilities, Shareholders' Equity
- ✅ Charts: Assets growth, Liabilities growth, Equity growth, Stacked comparison

#### Cash Flow
- ❌ Remove "Free Cash Flow" KPI
- ✅ Extract: Operating CF, Investing CF, Financing CF, Cash & Cash Equivalents
- ✅ Separate charts for each activity

#### Accounting Ratios
- ❌ No generic "Return Ratio Trend"
- ✅ Individual: ROE, ROCE, Current Ratio, Debt-Equity, Operating Margin
- ✅ Each ratio gets own chart

#### Management Highlights
- ✅ Document-only (no web search)
- ✅ LLM extraction: Strategy, Capex, Expansion, Risks, Tone
- ✅ Bullet points (no paragraphs)

#### Latest News & Competitors
- ✅ Web search ONLY
- ✅ Clear labeling if LLM-generated fallback

#### Investor Perspective
- ✅ Year-wise trends: ROE, ROCE, Dividend, FCF, CAGR
- ✅ Derived metrics from document data
- ✅ Trend charts + summary

### 3. JSON Schema Validation
- Validate ≥90% metrics populated before render
- Retry extraction if section empty
- Never silently fail

## Next Steps
1. Enhance `_forced_extraction_pipeline` with proper multi-stage flow
2. Update each section generator per requirements
3. Add JSON schema validation method
4. Update frontend to handle document-scoped state

