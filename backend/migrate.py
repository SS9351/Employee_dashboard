from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE attendances MODIFY COLUMN os_info VARCHAR(500);"))
    conn.commit()

print("Schema updated successfully!")
