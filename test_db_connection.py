
import psycopg
from getpass import getpass

def test_connection():
    password = getpass("Enter PostgreSQL password: ")

    try:
        with psycopg.connect(
            host="localhost",
            port=5432,
            dbname="autonomous_log_rca",
            user="postgres",
            password=password,
            connect_timeout=5,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), version();")
                database, version = cur.fetchone()

                cur.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public';
                """)
                table_count = cur.fetchone()[0]

                print("\nDatabase connection successful!")
                print("Database:", database)
                print("Tables found:", table_count)
                print("PostgreSQL:", version.split(",")[0])

    except psycopg.Error as error:
        print("\nDatabase connection failed.")
        print("Error:", error)

if __name__ == "__main__":
    test_connection()
