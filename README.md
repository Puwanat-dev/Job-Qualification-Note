# Job Qualification Database

A small desktop application built with Python, MySQL, and Tkinter.

## Run

1. Install and start MySQL Server.
2. Copy `config.example.py` to `config.py` if the local config file does not exist.
3. Install the Python driver and run:

```powershell
pip install mysql-connector-python
python main.py
```

The app creates the `jobqualificationdb` database and its `jobs` and `qualifications` tables automatically. The default connection is `localhost`, user `root`, password `admin`; update `config.py` for different credentials. Add a job, select it, then add qualification items.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Structure

- `database.py`: MySQL connection, schema, and CRUD operations.
- `ui.py`: Tkinter UI class.
- `main.py`: minimal application entry point.
- `config.py`: local settings, ignored by Git.
- `config.example.py`: shareable settings template.
