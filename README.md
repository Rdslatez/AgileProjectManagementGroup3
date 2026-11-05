# AgileProjectManagement
Final Project


# Video Game Sales Analytics - Sprint 1

## Project goal
Build a Python data analytics application that loads the video game sales CSV, cleans selected fields, calculates baseline statistics with NumPy, stores the cleaned data in SQLite, and exports initial SQL summaries and charts.

## Dataset
`Video_Games.csv` contains 16,719 game/platform records and 16 fields in the copy supplied to the team. Sales columns are expressed in millions. Keep the dataset beside `Main.py`. Add the dataset's original public source URL here before submitting the final project materials.

## Requirements
- Python 3.10 or newer recommended
- pandas
- NumPy
- matplotlib
- pytest (for unit tests)
- SQLite is included with Python

## Setup (Windows / VS Code)
1. Open this project folder in VS Code.
2. Open Terminal -> New Terminal.
3. Create a virtual environment: `python -m venv .venv`
4. Activate it: `.\.venv\Scripts\Activate.ps1`
5. Install packages: `python -m pip install -r requirements.txt`

## Run the application
From the project folder, run:

```powershell
python Main.py
```

The application entry point is `Main.py`; the reusable data functions are in `video_game_sales.py`. The application uses the CSV beside `Main.py` by default. It creates an `outputs` folder containing:
- `videogame_sales.db` - SQLite database with table `game_sales`
- `regional_sales.png` - regional sales bar chart
- `genre_sales.png` - global sales by genre chart
- `top_10_games.png` - top ten games chart
- `regional_sales_summary.csv`, `genre_sales_summary.csv`, `top_10_games.csv`, and `data_quality_summary.csv`
- `analysis_summary.txt` - readable run summary

Optional custom paths:

```powershell
py Main.py --csv "C:\path\to\Video_Games.csv" --output-dir "C:\path\to\outputs"
```

## Run the tests

```powershell
python -m pytest -q
```

## What the initial analysis does and does not claim
The program also exports missing-value counts and percentages. In this copy, numeric conversion changes the `tbd` entries in `User_Score` into missing values, leaving 9,129 missing user scores (54.60%). The program compares historical sales totals across regions and genres and lists the highest-selling game/platform records. These are descriptive comparisons. They do not prove that a genre, rating, publisher, or platform causes higher sales, and they do not predict future game success.

## Sprint 1 scope
- Load and clean the selected CSV with pandas.
- Convert sales and score fields to numeric values; text such as `tbd` in user scores becomes missing rather than being treated as a number.
- Calculate baseline global-sales statistics with NumPy.
- Store cleaned records in SQLite.
- Query top games, regional totals, and genre totals from SQLite.
- Export the three initial charts, four CSV summaries, and a readable text summary.

## Team
- Riley Slater - Project Leader
- Nour Tamam - Scrum Product Owner
- Hala Alshantoot - Scrum Master
