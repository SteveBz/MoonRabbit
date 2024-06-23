import sqlite3
import time
import random
import psutil

class SQLiteDiagnostic:
    def __init__(self, db_path, query=None):
        self.db_path = db_path
        self.query = query

    def trace_callback(self, query):
        print(f"Executing: {query}")

    def get_database_info(self, conn):
        try:
            # Database list and file info
            db_list = conn.execute("PRAGMA database_list").fetchall()
            print(f"Database list: {db_list}")

            # Locking mode
            locking_mode = conn.execute("PRAGMA locking_mode").fetchone()[0]
            print(f"Locking mode: {locking_mode}")

            # WAL checkpoint
            wal_checkpoint = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
            print(f"WAL checkpoint: {wal_checkpoint}")

            # Page count and freelist count
            page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            freelist_count = conn.execute("PRAGMA freelist_count").fetchone()[0]
            print(f"Page count: {page_count}, Freelist count: {freelist_count}")

            # Journal mode
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            print(f"Journal mode: {journal_mode}")

            # Busy timeout
            busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            print(f"Busy timeout: {busy_timeout}")

            # Cache size
            cache_size = conn.execute("PRAGMA cache_size").fetchone()[0]
            print(f"Cache size: {cache_size}")

        except sqlite3.Error as e:
            print(f"Error while getting database info: {e}")

    def get_query_plan(self, conn):
        if self.query:
            try:
                query_plan = conn.execute(f"EXPLAIN QUERY PLAN {self.query}").fetchall()
                print(f"Query plan for `{self.query}`: {query_plan}")
            except sqlite3.Error as e:
                print(f"Error while getting query plan: {e}")

    def monitor_system_performance(self):
        try:
            # Get system-level performance metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            print(f"CPU usage: {cpu_usage}%")
            print(f"Memory info: {memory_info}")
            print(f"Disk I/O: {disk_io}")
        except Exception as e:
            print(f"Error while monitoring system performance: {e}")

    def run_diagnostics(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.set_trace_callback(self.trace_callback)

            print("Starting SQLite diagnostic...")

            # Get database information
            self.get_database_info(conn)

            # Get query execution plan if query is provided
            self.get_query_plan(conn)

            # Monitor system performance
            self.monitor_system_performance()

            conn.close()
            print("SQLite diagnostic completed.")
        except sqlite3.Error as e:
            print(f"Error during diagnostics: {e}")
