import unittest
from datetime import date

import mysql.connector

from database import JobQualificationDatabase


class JobQualificationDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.database = JobQualificationDatabase()
            self.database.delete_all()
        except mysql.connector.Error as error:
            self.skipTest(f"MySQL is unavailable: {error}")

    def tearDown(self) -> None:
        self.database.delete_all()
        self.database.close()

    def test_insert_search_and_delete(self) -> None:
        record_id = self.database.add_job("Example Co", "Python Developer", location="Remote")
        self.database.add_qualification(record_id, "Technology", "Python")

        results = self.database.search("python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["job_id"], record_id)
        self.assertEqual(results[0]["date_note"], date.today())
        self.assertTrue(self.database.delete(record_id))
        self.assertEqual(self.database.search(record_id), [])

    def test_required_fields_are_validated(self) -> None:
        with self.assertRaises(ValueError):
            self.database.add_job("", "Python Developer")

    def test_category_counts_and_filter(self) -> None:
        record_id = self.database.add_job("Example Co", "Python Developer", location="Remote")
        self.database.add_qualification(record_id, "Technology", "Python")
        self.database.add_qualification(record_id, "Technology", "SQL")
        self.database.add_qualification(record_id, "Tools", "Git")

        counts = self.database.category_counts()
        self.assertIn({"category": "Technology", "item_count": 2}, counts)
        self.assertIn({"category": "Tools", "item_count": 1}, counts)
        self.assertEqual(len(self.database.search("", "Technology")), 1)


if __name__ == "__main__":
    unittest.main()
