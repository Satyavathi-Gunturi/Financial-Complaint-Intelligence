-- Data test: return violating rows; zero rows means the assertion passes.
select complaint_id, tag_id
from {{ ref('complaint_tags') }}
group by complaint_id, tag_id
having count(*) > 1
