### Q: What do we need to figure out about their database?

**A:** We need to know where their **real data** lives and what **one row** means. Right now our demo uses JSON files on disk. In production, agents need to read and write the same tables their teams already use.

Ask Mark:

- Is the main database **SQL Server** (as in the technical doc), or is Postgres OK for a pilot?
- Is one record a **full PRS form submission**, or one **invoice line** from the monthly upload (like the Excel rows)?
- After **Contract Intelligence** runs, where do the **extracted contract terms** get stored? (Table name, who updates it.)
- How do we get **contract text** — full document in the DB, file storage, or only look up by contract number?
- Where is **vendor master data** (vendor ID, address, contacts)?
- Where is **workflow status** (which step: intake → contract → CCR → cash)?
- Where do we save **CCR decisions** and **who approved** them?
- How do **invoices** link to **bank payments** for cash reconciliation?
- Where is the **exception queue** when something fails?
- How are **emails to suppliers** tracked (draft, approved, sent)?
- Do approvals happen in **ServiceNow** (or similar) or only inside our app?
- Any **HIPAA / privacy** rules on which fields we can send to an LLM?
- Does **Databricks** hold history we must read (e.g. “this supplier always pays late”)?

**Simple summary:** “We need a map of their tables and IDs so agents aren’t guessing from Excel exports forever.”

---

## 2. Observability tools — what can we suggest?

### Q: They listed Agno, LangGraph, AutoGen, Phoenix, LangSmith, Helicone — what should we recommend?

**A:**

| Tool | Plain answer |
|------|----------------|
| **LangSmith** | **Yes, suggest this first.** We already use LangGraph. LangSmith shows each agent step, prompts, errors, and helps test before go-live. Best match for developers. |
| **OpenTelemetry + Azure Monitor** | **Yes for production** if they’re a Microsoft shop (the doc mentions Azure and SQL Server). Standard way ops teams see latency, errors, and cost in one place. |
| **Arize Phoenix** | **Yes for quality checks.** Good for “did the agent give the right answer?” compared to test cases in the Excel files. |
| **Helicone** | **Optional.** Extra layer to log Groq API usage and cost; nice if they want billing visibility fast. |
| **LangGraph** | **Already using it.** It runs the workflow; it’s not a monitoring product by itself. |
| **Microsoft AutoGen** | **Don’t suggest switching.** Different framework; we’d rebuild everything. |
| **Agno** | **Skip for now.** Smaller tool; doesn’t match the enterprise “governed platform” story as well. |

**One sentence for Mark:** “Use **LangSmith** while we build, **Azure OpenTelemetry** when we go live, and **Phoenix** if we want a dedicated quality-testing lane.”

---

## 3. Phase 1 PRS end-to-end — does PRS get the contract from Contract Intelligence?

### Q: Internally, does PRS pull the contract from the Contract Intelligence agent?

**A (target design):** **Yes, that’s the plan.** Contract Intelligence reads the contract once, pulls out the important terms (dates, payment rules, limits), and other steps use that structured info.

**A (what we built today):** **Not fully yet.**

- On **Submit PRS**, the user (or a test fixture) **pastes or uploads the full contract text**. Three “contract” agents check that text — they act like Contract Intelligence, but there is **no separate CIA database** other agents read from.
- On **CCR**, we look up contract text **by contract number** from text files in a folder, not from a CIA table.
- On **Intake pilot**, we only check the **invoice row** (amount, email, dates, etc.) — **no contract** is loaded there yet.

**Plain summary:** “In the vision, PRS uses CIA output. In the demo, PRS uses contract text you attach at submit time. Connecting to their real CIA store is a next step.”

---

## 4. Missing fields — suggestions vs routing to other agents or humans?

### Q: If their database is missing fields, do agents suggest values or send work elsewhere?

**A (partially yes):**

**What works today:**

- Agents **flag** missing or bad fields (`missing_fields`, `field_errors`, warnings in JSON).
- Bad or unclear submissions get **pass / partial / fail**.
- **Humans** can review in the **Approvals** page (PRS failures, intake failures, hard CCR exceptions, supplier email drafts).
- **Supplier** page can **draft** a correction email (does not send automatically).

**What we don’t do yet:**

- **Look up** missing info from **their SQL Server / vendor master** and auto-fill suggestions.
- **Automatically** call the Supplier agent when intake fails — you go to Supplier manually today.
- **Smart routing** like “missing contract terms → call CIA again” — the flow is fixed: intake → contract → SKU, every time.

**Plain summary:** “We catch problems and queue humans (and draft supplier emails). We don’t yet plug into their master data to suggest the right missing values automatically.”

**Good question for Mark:** “When something’s missing, do you want lookup from master data, an email to the supplier, or always a human ticket?”

---

## 5. Do all PRS agents run at the same time or one after another?

### Q: Are the seven agents parallel or sequential?

**A:** **Both — in three batches, one batch after another.**

1. **Batch 1 (together):** Requestor check + Vendor check — **at the same time**.
2. **Batch 2 (one by one):** Parties → Commercial terms → Legal clauses — **one after another** (to avoid overloading the AI API).
3. **Batch 3 (together):** SKU line items + SKU policies — **at the same time**.

Then everything is **merged** into one overall pass / partial / fail result.

**Plain summary:** “Not all seven at once. Usually 2, then 3, then 2 — about one to two minutes total on Submit.”