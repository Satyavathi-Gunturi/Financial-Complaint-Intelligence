-- Data test: return violating rows; zero rows means the assertion passes.
select c.complaint_id
from {{ ref('complaints') }} c
join {{ ref('issue_categories') }} i on c.issue_category_id = i.issue_category_id
where c.product_category_id <> i.product_category_id
