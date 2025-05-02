"""create forecast status view

Revision ID: d6eee9603f67
Revises: 
Create Date: 2025-04-30 02:19:33.985411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6eee9603f67'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW forecast_status AS
        SELECT hist.stable_id, p.forecast_name, p.start_date, p.end_date, hist.status, submitted_row.insert_ts as start_ts
        FROM (
            SELECT
                stable_id,
                status,
                insert_ts,
                ROW_NUMBER() OVER (PARTITION BY stable_id ORDER BY insert_ts DESC) AS rn
            FROM forecast_status_history
        ) hist
        LEFT JOIN expense_forecast ef
        ON hist.stable_id = ef.stable_forecast_id 
        LEFT JOIN parameter p
        ON ef.parameter_id = p.stable_parameter_id  
        LEFT JOIN ( 
             SELECT
                stable_id,
                status,
                insert_ts,
                ROW_NUMBER() OVER (PARTITION BY stable_id ORDER BY insert_ts ASC) AS rn
            FROM forecast_status_history  
        ) submitted_row
        ON hist.stable_id = submitted_row.stable_id 
        WHERE hist.rn = 1 and submitted_row.rn = 1;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW forecast_status")
