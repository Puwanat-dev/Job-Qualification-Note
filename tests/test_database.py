import unittest
from datetime import date

import mysql.connector

from database import JobQualificationDatabase


class JobQualificationDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.database = JobQualificationDatabase()
        except mysql.connector.Error as error:
            self.skipTest(f"MySQL is unavailable: {error}")

    def tearDown(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
