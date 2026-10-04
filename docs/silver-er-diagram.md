# Silver ER diagram

**Relational view:** normalized complaint records, optional narratives and the many-to-many tag bridge.

![Technical design diagram](../assets/diagrams/silver-relational-model.svg)

[Download editable draw.io file](../assets/diagrams/silver-relational-model.drawio) · [Open the full-size diagram](../assets/diagrams/silver-relational-model.svg) · [Project walkthrough](project-walkthrough.md) · [Metric definitions](metric-definitions.md)

---

These links describe dbt-tested relationships, not enforced DuckDB DDL constraints. One complaint has one company, product combination, issue combination and channel; it may have no narrative or multiple tags.

<details>
<summary>View the editable Mermaid definition</summary>

```mermaid
erDiagram
    companies ||--o{ complaints : company_id
    product_categories ||--o{ complaints : product_category_id
    issue_categories ||--o{ complaints : issue_category_id
    submission_channels ||--o{ complaints : submission_channel_id
    product_categories ||--o{ issue_categories : product_category_id
    complaints ||--o| complaint_narratives : complaint_id
    complaints ||--o{ complaint_tags : complaint_id
    tags ||--o{ complaint_tags : tag_id
    complaints {
        string complaint_id PK
        string company_id FK
        string product_category_id FK
        string issue_category_id FK
        string submission_channel_id FK
        date date_received
        date date_sent_to_company
        string zip_code
        boolean timely_response
    }
    companies {
        string company_id PK
        string company_name
    }
    product_categories {
        string product_category_id PK
        string product
        string sub_product
    }
    issue_categories {
        string issue_category_id PK
        string product_category_id FK
        string issue
        string sub_issue
    }
    submission_channels {
        string submission_channel_id PK
        string submission_channel
    }
    complaint_narratives {
        string complaint_id PK,FK
        string narrative
    }
    tags {
        string tag_id PK
        string tag_name
    }
    complaint_tags {
        string complaint_id PK,FK
        string tag_id PK,FK
    }
```

</details>

Complaint–tag pairs form a composite logical key. Complaints also retain state, response categories, narrative availability and ingestion provenance. The SQL files provide the complete column definitions.
