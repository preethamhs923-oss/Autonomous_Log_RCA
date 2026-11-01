import os
import getpass
import psycopg
from psycopg import sql

# Database connection
password = getpass.getpass("Enter PostgreSQL password: ")

conn = psycopg.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "autonomous_log_rca"),
    user=os.getenv("DB_USER", "postgres"),
    password=password
)

cur = conn.cursor()

# Get all public tables
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")

tables = cur.fetchall()

print("\nDATABASE RECORD COUNTS")
print("----------------------")

for (table_name,) in tables:
    query = sql.SQL("SELECT COUNT(*) FROM {}").format(
        sql.Identifier(table_name)
    )
    cur.execute(query)
    count = cur.fetchone()[0]
    print(f"{table_name}: {count}")

cur.close()
conn.close()

print("\nDatabase verification completed.")