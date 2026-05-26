# Process Diagram Components

This document lists the main system components and the current email or notification handling that can be used in process diagrams.

## Core System Components

| Component Name | Type | Description |
| --- | --- | --- |
| Frontend UI | Next.js app | User-facing app for PRS submit, results, and supplier draft review |
| FastAPI Gateway | API layer | Main backend entry point for requests, status, and routing |
| LangGraph Orchestrator | Workflow engine | Runs PRS validation flow and merges agent outputs |
| Intake Agent | AI service | Validates requestor and vendor details |
| Contract Agent | AI service | Reviews parties, commercial terms, and legal clauses |
| SKU Agent | AI service | Validates SKU schedule and SKU policy content |
| Supplier Message Queue | Data source | Stores supplier communication records used for drafting |
| Supplier Interaction Agent | AI service | Drafts outbound supplier emails or messages for review |
| Approval Queue | Human review | Holds items that need operator approval |
| WebSocket Status Manager | Realtime updates | Pushes in-app progress and completion events |
| Database | Persistence | Stores submissions, results, approvals, and run logs |
| Groq API | LLM provider | Model backend used by the agents |

## Email And Notification Handling

| Use Case | Component(s) | Current Behavior | Status |
| --- | --- | --- | --- |
| Outbound supplier emails | Supplier Message Queue -> Supplier Interaction Agent -> Approval Queue | Drafts supplier emails for human review | Implemented, draft-only |
| Notification emails | None found | No email notification service exists in the codebase | Not implemented |
| Inbound emails | None found | No mailbox reader or inbound email processing exists | Not implemented |
| Vendor email as input | Frontend UI + Intake/Vendor validation | Captures and validates vendor contact email | Implemented |
| Realtime notifications | WebSocket Status Manager | Sends in-app progress updates | Implemented, not email |

## Summary

The current email-related component is the `Supplier Interaction Agent`, but it only prepares outbound drafts. There is no live email sending service and no inbound email handling in the current implementation.
