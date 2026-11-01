
import os
import psycopg


def get_connection():
    """Create and return a PostgreSQL connection."""
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "autonomous_log_rca"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def test_database():
    """Verify the connection and inspect project database tables."""

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT current_database();")
            print("Connected database:", cur.fetchone()[0])

            # Get all available tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            table_rows = cur.fetchall()

            print("\nAvailable tables:")
            for row in table_rows:
                print("-", row[0])

            # Inspect logs and anomalies
            for table in ["logs", "anomalies"]:

                print(f"\n--- {table.upper()} COLUMNS ---")

                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))

                columns = cur.fetchall()

                if columns:
                    for column in columns:
                        print(column)
                else:
                    print("No columns found.")

                print(f"\n--- {table.upper()} CONSTRAINTS ---")

                cur.execute("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'public'
                    AND table_name = %s;
                """, (table,))

                constraints = cur.fetchall()

                for constraint in constraints:
                    print(constraint)


if __name__ == "__main__":
    from getpass import getpass

    os.environ["DB_PASSWORD"] = getpass(
        "Enter PostgreSQL password: "
    )
    test_database()
