"""MySQL persistence for jobs and job qualifications."""

from __future__ import annotations

from datetime import date
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection


class JobQualificationDatabase:
    """Create and manage jobs and their qualifications in MySQL."""

    def __init__(
        self,
        host: str = "localhost",
        user: str = "root",
        password: str = "admin",
        database: str = "jobqualificationdb",
    ) -> None:
        self._connection = self._connect(host, user, password, database)
        self._create_table()

    @staticmethod
    def _connect(host: str, user: str, password: str, database: str) -> MySQLConnection:
        connection = mysql.connector.connect(host=host, user=user, password=password)
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        cursor.close()
        connection.close()
        return mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )

    def _create_table(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id VARCHAR(8) PRIMARY KEY,
                company_name VARCHAR(300) NOT NULL,
                position VARCHAR(100) NOT NULL,
                min_exp INT NOT NULL DEFAULT 0,
                location VARCHAR(30),
                sub_location VARCHAR(30),
                date_note DATE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qualifications (
                job_id VARCHAR(8) NOT NULL,
                category VARCHAR(300) NOT NULL,
                item_name VARCHAR(300) NOT NULL,
                PRIMARY KEY (job_id, category, item_name),
                CONSTRAINT fk_qualifications_job
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            )
            """
        )
        cursor.close()
        self._connection.commit()

    def add_job(
        self,
        company_name: str,
        position: str,
        min_exp: int = 0,
        location: str = "",
        sub_location: str = "",
        date_note: date | str | None = None,
    ) -> str:
        """Insert a job and return its formatted primary key."""
        if not company_name.strip() or not position.strip():
            raise ValueError("Company name and position are required.")
        if date_note is None:
            date_note = date.today()
        cursor = self._connection.cursor()
        cursor.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTRING(job_id, 4) AS UNSIGNED)), 0) + 1
            FROM jobs
            """
        )
        job_number = int(cursor.fetchone()[0])
        job_id = f"JOB{job_number:04d}"
        cursor.execute(
            """
            INSERT INTO jobs
                (job_id, company_name, position, min_exp, location, sub_location, date_note)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (job_id, company_name.strip(), position.strip(), min_exp, location.strip(), sub_location.strip(), date_note),
        )
        cursor.close()
        self._connection.commit()
        return job_id

    def add_qualification(self, job_id: str, category: str, item_name: str) -> None:
        """Add one qualification item for an existing job."""
        if not category.strip() or not item_name.strip():
            raise ValueError("Category and item name are required.")
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO qualifications (job_id, category, item_name) VALUES (%s, %s, %s)",
            (job_id, category.strip(), item_name.strip()),
        )
        cursor.close()
        self._connection.commit()

    def get_positions(self) -> list[str]:
        """Return all known job positions for dropdown suggestions."""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT position FROM jobs WHERE position IS NOT NULL AND position != '' ORDER BY position")
        rows = cursor.fetchall()
        cursor.close()
        return [row["position"] for row in rows if row["position"]]

    def get_categories(self) -> list[str]:
        """Return all existing qualification categories for dropdown suggestions."""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT category FROM qualifications WHERE category IS NOT NULL AND category != '' ORDER BY category")
        rows = cursor.fetchall()
        cursor.close()
        return [row["category"] for row in rows if row["category"]]

    def get_item_names(self) -> list[str]:
        """Return all existing qualification item names for dropdown suggestions."""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT item_name FROM qualifications WHERE item_name IS NOT NULL AND item_name != '' ORDER BY item_name")
        rows = cursor.fetchall()
        cursor.close()
        return [row["item_name"] for row in rows if row["item_name"]]

    def category_counts(self) -> list[dict[str, Any]]:
        """Return each category with the count of item names it contains."""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT category, COUNT(item_name) AS item_count
            FROM qualifications
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY category
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def search(self, query: str = "", category: str = "") -> list[dict[str, Any]]:
        """Return records matching the query and optional category filter."""
        search_term = f"%{query.strip()}%"
        query_conditions: list[str] = []
        params: list[str] = []

        if query.strip():
            query_conditions.extend([
                "j.position LIKE %s",
                "j.company_name LIKE %s",
                "j.location LIKE %s",
                "j.sub_location LIKE %s",
                "q.category LIKE %s",
                "q.item_name LIKE %s",
            ])
            params.extend([search_term] * 6)

        category_filter = category.strip() if category else ""
        if category_filter:
            params.append(category_filter)

        sql = """
             SELECT j.job_id, j.company_name, j.position, j.min_exp, j.location,
                 j.sub_location, j.date_note,
                 GROUP_CONCAT(CONCAT(q.category, ':', q.item_name) SEPARATOR ' | ') AS qualifications
            FROM jobs AS j
            LEFT JOIN qualifications AS q ON q.job_id = j.job_id
        """

        where_clauses: list[str] = []
        if query_conditions:
            where_clauses.append("(" + " OR ".join(query_conditions) + ")")
        if category_filter:
            where_clauses.append("q.category = %s")

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " GROUP BY j.job_id ORDER BY j.job_id DESC"

        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def delete(self, qualification_id: str) -> bool:
        """Delete a record by ID and report whether a row was removed."""
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = %s", (qualification_id,))
        self._connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    def delete_all(self) -> None:
        """Delete all jobs and qualifications to reset the database for tests or maintenance."""
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM qualifications")
        cursor.execute("DELETE FROM jobs")
        self._connection.commit()
        cursor.close()

    def close(self) -> None:
        self._connection.close()
