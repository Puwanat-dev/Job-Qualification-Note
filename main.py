"""Application entry point."""

import tkinter as tk

from ui import JobQualificationApp


if __name__ == "__main__":
    root = tk.Tk()
    JobQualificationApp(root)
    root.mainloop()
