"""Tkinter user interface for the job qualification database."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER, WINDOW_GEOMETRY
from database import JobQualificationDatabase


class JobQualificationApp:
    """Provide buttons and fields for managing qualification records."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Job Qualification Database")
        self.root.geometry(WINDOW_GEOMETRY)
        self.database = JobQualificationDatabase(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        self._build_widgets()
        self._load_records()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_widgets(self) -> None:
        form = ttk.LabelFrame(self.root, text="Job")
        form.pack(fill="x", padx=12, pady=12)

        self.company_name = self._add_field(form, "Company name", 0)
        self.position = self._add_field(form, "Position", 1)
        self.min_exp = self._add_field(form, "Min experience (years)", 2)
        self.location = self._add_field(form, "Location", 3)
        self.sub_location = self._add_field(form, "Sub location", 4)

        actions = ttk.Frame(form)
        actions.grid(row=5, column=0, columnspan=2, sticky="e", padx=8, pady=8)
        ttk.Button(actions, text="Add job", command=self._insert_job).pack(side="left", padx=4)
        ttk.Button(actions, text="Clear", command=self._clear_form).pack(side="left", padx=4)

        qualification_form = ttk.LabelFrame(self.root, text="Qualification")
        qualification_form.pack(fill="x", padx=12, pady=(0, 12))
        self.category = self._add_field(qualification_form, "Category", 0)
        self.item_name = self._add_field(qualification_form, "Item name", 1)
        ttk.Button(qualification_form, text="Add to selected job", command=self._add_qualification).grid(
            row=2, column=1, sticky="e", padx=8, pady=8
        )

        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=12)
        ttk.Label(search_frame, text="Search").pack(side="left")
        self.search_text = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_text)
        search_entry.pack(side="left", fill="x", expand=True, padx=8)
        search_entry.bind("<Return>", lambda _event: self._load_records())
        ttk.Button(search_frame, text="Search", command=self._load_records).pack(side="left")

        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.columns = ("job_id", "company_name", "position", "min_exp", "location", "sub_location", "date_note", "qualifications")
        self.table = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        headings = {"job_id": "Job ID", "company_name": "Company", "position": "Position", "min_exp": "Min exp.", "location": "Location", "sub_location": "Sub location", "date_note": "Date note", "qualifications": "Qualifications"}
        widths = {"job_id": 75, "company_name": 150, "position": 150, "min_exp": 70, "location": 100, "sub_location": 100, "date_note": 100, "qualifications": 300}
        for column in self.columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=widths[column], anchor="w")
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.root, text="Delete selected", command=self._delete_selected).pack(anchor="e", padx=12, pady=(0, 12))

    @staticmethod
    def _add_field(parent: ttk.LabelFrame, label: str, row: int) -> tk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        entry = ttk.Entry(parent)
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        parent.columnconfigure(1, weight=1)
        return entry

    def _load_records(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)
        for record in self.database.search(self.search_text.get()):
            self.table.insert("", "end", values=tuple(record[column] or "" for column in self.columns))

    def _delete_selected(self) -> None:
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Delete qualification", "Select a record first.")
            return
        job_id = self.table.item(selection[0], "values")[0]
        if messagebox.askyesno("Delete qualification", "Delete the selected record?"):
            self.database.delete(job_id)
            self._load_records()

    def _clear_form(self) -> None:
        for field in (self.company_name, self.position, self.min_exp, self.location, self.sub_location, self.category, self.item_name):
            field.delete(0, tk.END)

    def _insert_job(self) -> None:
        try:
            min_exp = int(self.min_exp.get() or 0)
            self.database.add_job(
                self.company_name.get(), self.position.get(), min_exp,
                self.location.get(), self.sub_location.get(),
            )
        except (ValueError, TypeError) as error:
            messagebox.showerror("Invalid job", str(error))
            return
        self._clear_form()
        self._load_records()

    def _add_qualification(self) -> None:
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Add qualification", "Select a job first.")
            return
        job_id = self.table.item(selection[0], "values")[0]
        try:
            self.database.add_qualification(job_id, self.category.get(), self.item_name.get())
        except ValueError as error:
            messagebox.showerror("Invalid qualification", str(error))
            return
        self.category.delete(0, tk.END)
        self.item_name.delete(0, tk.END)
        self._load_records()

    def close(self) -> None:
        self.database.close()
        self.root.destroy()
