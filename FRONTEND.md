# FRONTEND.md — Next.js Frontend Specification

> Healthcare-grade UI for the PRS AI Hub.
> Built with Next.js 14, TypeScript, Tailwind CSS, and Framer Motion.
> Design standard: **Clinical precision meets modern clarity** — WCAG 2.1 AA compliant.

---

## Tech Stack

```
Framework:     Next.js 14 (App Router)
Language:      TypeScript 5
Styling:       Tailwind CSS + CSS Variables
Components:    shadcn/ui (base) + custom healthcare components
Animation:     Framer Motion
Forms:         React Hook Form + Zod validation
File Upload:   react-dropzone
HTTP:          Axios + React Query (TanStack)
WebSocket:     native browser WebSocket API
State:         Zustand
Icons:         Lucide React
Fonts:         Geist Sans (display) + IBM Plex Mono (data/code)
Testing:       Jest + React Testing Library + Playwright (E2E)
```

---

## Install

```bash
npx create-next-app@latest prs-frontend --typescript --tailwind --app
cd prs-frontend
npm install framer-motion @tanstack/react-query axios zustand react-dropzone \
            react-hook-form zod @hookform/resolvers lucide-react \
            class-variance-authority clsx tailwind-merge
npx shadcn-ui@latest init
```

---

## Design System

### Color Palette

```css
/* globals.css */
:root {
  /* Brand — deep clinical teal */
  --color-brand-50:  #f0fdfa;
  --color-brand-100: #ccfbf1;
  --color-brand-200: #99f6e4;
  --color-brand-500: #14b8a6;
  --color-brand-600: #0d9488;
  --color-brand-700: #0f766e;
  --color-brand-900: #134e4a;

  /* Status colors */
  --color-pass:    #16a34a;   /* green-600 */
  --color-partial: #d97706;   /* amber-600 */
  --color-fail:    #dc2626;   /* red-600 */
  --color-pending: #6b7280;   /* gray-500 */

  /* Surface */
  --color-surface:     #ffffff;
  --color-surface-alt: #f8fafc;
  --color-border:      #e2e8f0;

  /* Typography */
  --color-text-primary:   #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted:     #94a3b8;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --color-surface:     #0f172a;
    --color-surface-alt: #1e293b;
    --color-border:      #334155;
    --color-text-primary:   #f1f5f9;
    --color-text-secondary: #94a3b8;
  }
}
```

### Typography

```css
/* Use Geist Sans for all UI text */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap');

body {
  font-family: 'Geist', var(--font-sans), system-ui, sans-serif;
}

/* Data values, request IDs, JSON previews */
.font-data {
  font-family: 'IBM Plex Mono', monospace;
}
```

---

## File Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Dashboard / home
│   ├── submit/
│   │   └── page.tsx            # PRS submission wizard
│   ├── results/[id]/
│   │   └── page.tsx            # Validation results page
│   ├── history/
│   │   └── page.tsx            # Submission history
│   └── admin/
│       └── page.tsx            # Admin review queue
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── PageHeader.tsx
│   ├── submission/
│   │   ├── SubmissionWizard.tsx      # Multi-step form
│   │   ├── Step1_Requestor.tsx
│   │   ├── Step2_Vendor.tsx
│   │   ├── Step3_ContractUpload.tsx
│   │   ├── Step4_SKUEntry.tsx
│   │   └── Step5_Review.tsx
│   ├── results/
│   │   ├── ValidationDashboard.tsx   # Main results view
│   │   ├── AgentStatusCard.tsx       # Per-agent result card
│   │   ├── OverallStatusBanner.tsx
│   │   ├── ClauseChecklist.tsx       # Contract clause list
│   │   ├── SKUResultsTable.tsx
│   │   └── RiskFlagsPanel.tsx
│   ├── common/
│   │   ├── StatusBadge.tsx           # pass/fail/partial pill
│   │   ├── ConfidenceBar.tsx         # 0-100% confidence meter
│   │   ├── FileDropzone.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── AgentProgressTracker.tsx  # Live WebSocket progress
│   └── ui/                           # shadcn base components
├── hooks/
│   ├── usePRSSubmit.ts
│   ├── usePRSStatus.ts       # Polling + WebSocket
│   └── usePRSHistory.ts
├── lib/
│   ├── api.ts                # Axios instance + endpoints
│   ├── validations.ts        # Zod schemas
│   └── utils.ts
├── types/
│   └── prs.ts                # TypeScript types matching backend models
└── public/
    └── icons/
```

---

## Key Pages

### 1. Dashboard (`/`)

```tsx
// What to show:
// - Summary stats: Total submissions, Pass rate, Avg processing time
// - Recent submissions table (last 10)
// - Quick action: "Submit New PRS" button
// - Status distribution donut chart (pass/partial/fail)
```

### 2. Submission Wizard (`/submit`)

5-step form wizard with progress indicator.

```tsx
// Step 1 — Requestor Info
// Fields: Requestor Name, Business Unit, Business Owner, Priority (dropdown),
//         Description (textarea), Need By Date (date picker)
// Validation: React Hook Form + Zod, inline errors, no submit until valid

// Step 2 — Vendor Info
// Fields: Vendor Name, Address (line1, line2, county, state dropdown, country),
//         Contact Name, Role, Phone (with country code), Email
// Auto-suggest US state from a typed dropdown

// Step 3 — Document Upload
// Two dropzones: Contract (PDF/DOCX) + SKU Addendum (PDF/DOCX, optional)
// Show file name, size, type icon after upload
// Max 25MB per file

// Step 4 — SKU Entry
// Dynamic table: add/remove rows
// Columns: SKU#, Description, UOM, Unit Price, MSRP, MOQ, Lead Time, Status
// Import from CSV option (parse CSV client-side)

// Step 5 — Review & Submit
// Read-only summary of all entered data
// Show uploaded filenames
// "Submit for Validation" button
// Loading state with agent progress tracker
```

### 3. Validation Results (`/results/[id]`)

The most important page. Shows real-time validation as agents complete.

```tsx
// Layout:
// - Top: Overall Status Banner (PASS / PARTIAL REVIEW NEEDED / FAIL)
// - Left column (60%): Agent results accordion
// - Right column (40%): Risk flags + Next action panel

// Agent cards show:
// - Agent name + icon
// - Status badge (pass/partial/fail)
// - Confidence score bar (0-100%)
// - Expandable details (field errors, clause results, etc.)
// - Timestamp when completed

// Real-time updates via WebSocket:
// - Agents complete one by one
// - Each card animates in when its agent finishes
// - Progress tracker at top shows "4 of 7 agents complete"

// Risk Flags Panel:
// - Red section: Critical blockers (must fix)
// - Amber section: Warnings (review needed)
// - Green section: What passed

// Bottom: Action buttons
// "Download Report (PDF)" | "Send to Requestor" | "Approve for Legal Review"
```

### 4. History (`/history`)

```tsx
// Filterable table:
// Columns: Request ID, Submitted By, Vendor, Date, Status, Actions
// Filters: Status (All/Pass/Partial/Fail), Date range, Requestor BU
// Click row → go to /results/[id]
// Export to CSV button
```

---

## Agent Progress Tracker Component

This is the live WebSocket component shown during processing.

```tsx
// components/common/AgentProgressTracker.tsx

const AGENTS = [
  { id: "requestor_info",         label: "Requestor Info",       group: "Intake" },
  { id: "vendor_info",            label: "Vendor Info",          group: "Intake" },
  { id: "parties_and_definitions",label: "Parties & Definitions",group: "Contract" },
  { id: "commercial_terms",       label: "Commercial Terms",     group: "Contract" },
  { id: "legal_clauses",          label: "Legal Clauses",        group: "Contract" },
  { id: "sku_schedule",           label: "SKU Schedule",         group: "SKU" },
  { id: "sku_policy",             label: "SKU Policy",           group: "SKU" },
]

// Each agent shows:
// ○ Pending (gray dot)
// ⟳ Running (spinning teal dot)
// ✓ Pass (green check)
// ⚠ Partial (amber warning)
// ✗ Fail (red x)

// WebSocket message handler:
// { "event": "agent_complete", "agent": "requestor_info", "status": "pass" }
// → Update that agent's state → animate status change
```

---

## Accessibility Requirements (WCAG 2.1 AA)

- All form inputs have associated `<label>` elements
- Error messages linked to inputs via `aria-describedby`
- Color is never the only indicator of status — always paired with icon + text
- Focus visible on all interactive elements (`focus-visible:ring-2`)
- Keyboard navigation for all features (wizard, tables, modals)
- Screen reader announcements for live validation updates (`aria-live="polite"`)
- Minimum 4.5:1 contrast ratio for all text
- Touch targets minimum 44×44px on mobile

---

## TypeScript Types

```typescript
// types/prs.ts

export type AgentStatus = "pass" | "fail" | "partial" | "pending" | "running"
export type OverallStatus = "pass" | "fail" | "partial"
export type BusinessPriority = "Critical" | "High" | "Medium" | "Low"

export interface AgentResult {
  agent: string
  status: AgentStatus
  confidence_score: number
  summary: string
  [key: string]: any   // Agent-specific fields
}

export interface OrchestratorResult {
  request_id: string
  submitted_at: string
  overall_status: OverallStatus
  requires_human_review: boolean
  agents: Record<string, AgentStatus>
  critical_blockers: string[]
  warnings: string[]
  next_action: string
  review_time_estimate: string
  agent_results: Record<string, AgentResult>
}

export interface PRSSubmission {
  requestor: {
    requestor_name: string
    requestor_business_unit: string
    business_owner: string
    business_unit: string
    business_priority: BusinessPriority
    request_description: string
    need_by_date: string
  }
  vendor: {
    vendor_name: string
    vendor_address_line1: string
    vendor_address_line2?: string
    vendor_address_county?: string
    vendor_address_state: string
    vendor_address_country: string
    vendor_contact_name: string
    vendor_contact_role: string
    vendor_contact_phone_country_code: string
    vendor_contact_phone: string
    vendor_contact_email: string
    vendor_master_id?: string
    prior_contract_number?: string
  }
  sku_items: SKUItem[]
}

export interface SKUItem {
  sku_number: string
  description: string
  unit_of_measure: string
  unit_price: number
  msrp?: number
  min_order_qty: number
  lead_time: string
  status: "Active" | "Inactive" | "Pending" | "Discontinued"
}
```

---

## Environment Variables (Frontend)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=PRS AI Hub
NEXT_PUBLIC_ENVIRONMENT=development
```

---

## Dockerfile

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```
