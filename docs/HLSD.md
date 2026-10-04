# High-Level System Design (HLSD)

## Goal and scope
Provide leadership with consistent complaint analytics and an evidence-backed data agent. The implemented scope is the batch data foundation; serving and AI are planned.

## Implemented processing
```mermaid
flowchart TD
    S[Official CFPB downloads] --> I[Colab ZIP inventory and ingestion]
    I --> B[Bronze Parquet with provenance]
    B --> ST[DuckDB source view and dbt staging]
    ST --> SI[Eight silver tables]
    SI --> W[Wide gold metrics and narrative view]
    W --> STAR[Star fact and seven dimensions]
    I --> CP[Drive checkpoints]
    STAR --> CP
    W --> CP
```

Colab supplies remote compute for an iPad-based workflow. DuckDB stores transformed tables. dbt manages dependencies, transformations and assertions. Checkpoints persist files and the closed database after successful stages. They are development backups, not an application-serving design.

## Planned serving and AI
```mermaid
flowchart TD
    U[Leadership dashboard and chat] --> A[Data agent]
    A --> Q[Read-only SQL tool]
    A --> R[Narrative retrieval tool]
    Q --> W[Wide gold]
    Q --> S[Gold star]
    R --> N[Narrative index]
    Q --> E[Answer with calculations and evidence]
    R --> E
    E --> U
```

The agent will choose date grouping and filters under documented metric definitions. SQL calculates quantities; retrieval supplies relevant complaint text. The LLM must not fabricate figures or establish internal root causes from narratives. Model/provider, permanent data hosting, vector index and dashboard hosting have not been selected or provisioned.

## Boundaries
Repository: code, designs and result summaries. Data plane: source archives, bronze files and the DuckDB dataset. Serving plane: planned dashboard, agent and retrieval service. Secrets remain outside the public repository. AI query access will be read-only with schema allowlists, query limits and logged tool outcomes.

## Acceptance goals
Preserve all selected complaints; reconcile both gold structures; reproduce builds from available bronze; support variable date aggregation; cite evidence in narrative answers. Exact AI performance targets will be set before evaluation, not claimed here.

## Current operating limitations
Manual source downloads; full table rebuilds; source availability not continuously monitored; local bronze paths embedded in the source view need rebinding after runtime reset. No orchestration scheduler, hosted endpoint, SLA or production monitoring is implemented.
