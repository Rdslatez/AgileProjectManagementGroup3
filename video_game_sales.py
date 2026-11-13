"""Video Game Sales Analytics - Sprint 1 application.

The application loads the project CSV, cleans the data, calculates baseline
statistics with NumPy, stores the cleaned records in SQLite, and exports SQL
analysis results and charts.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Supports running on computers without a display.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATASET_NAME = "Video_Games.csv"
TABLE_NAME = "game_sales"
SALES_COLUMNS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]
REGIONAL_COLUMNS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
REQUIRED_COLUMNS = {
    "Name", "Platform", "Genre", "Global_Sales",
    "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales",
}
COLUMN_ALIASES = {
    "Global Sales": "Global_Sales",
    "NA Sales": "NA_Sales",
    "EU Sales": "EU_Sales",
    "JP Sales": "JP_Sales",
    "Other Sales": "Other_Sales",
    "Year of Release": "Year_of_Release",
    "Year": "Year_of_Release",
}
NUMERIC_COLUMNS = [
    "Year_of_Release", "Critic_Score", "Critic_Count", "User_Score",
    "User_Count", *SALES_COLUMNS,
]


def load_dataset(csv_path: str | Path) -> pd.DataFrame:
    """Load a CSV file and return its rows as a pandas DataFrame."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Keep {DATASET_NAME} beside Main.py "
            "or pass its location with --csv."
        )
    return pd.read_csv(path)


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, clean text, and convert numeric fields.

    Missing game names, genres, and publishers are labelled 'Unknown'. Missing
    scores and release years remain missing (NaN), rather than being invented.
    Values such as the text 'tbd' in User_Score become NaN during conversion.
    """
    cleaned = data.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    cleaned = cleaned.rename(columns=COLUMN_ALIASES)

    missing = sorted(REQUIRED_COLUMNS.difference(cleaned.columns))
    if missing:
        raise ValueError(
            "Dataset is missing required columns: " + ", ".join(missing)
        )

    # Trim surrounding spaces from text values without changing missing values.
    for column in cleaned.select_dtypes(include=["object"]).columns:
        cleaned[column] = cleaned[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    for column in ["Name", "Genre", "Publisher"]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].fillna("Unknown")
            cleaned[column] = cleaned[column].replace("", "Unknown")

    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    return cleaned


def calculate_baseline_statistics(data: pd.DataFrame) -> dict[str, Any]:
    """Calculate baseline sales measures with NumPy."""
    if "Global_Sales" not in data.columns:
        raise ValueError("Global_Sales column is required for baseline statistics.")

    sales = data["Global_Sales"].dropna().to_numpy(dtype=float)
    if sales.size == 0:
        raise ValueError("No valid Global_Sales values are available.")

    return {
        "record_count": int(len(data)),
        "valid_global_sales_count": int(sales.size),
        "missing_global_sales_count": int(data["Global_Sales"].isna().sum()),
        "total_global_sales_millions": float(np.sum(sales)),
        "average_global_sales_millions": float(np.mean(sales)),
        "maximum_global_sales_millions": float(np.max(sales)),
        "missing_year_count": int(data["Year_of_Release"].isna().sum())
        if "Year_of_Release" in data.columns else None,
        "missing_user_score_count": int(data["User_Score"].isna().sum())
        if "User_Score" in data.columns else None,
    }


def summarize_missing_values(data: pd.DataFrame) -> pd.DataFrame:
    """Return missing-value counts and percentages for every column."""
    missing_counts = data.isna().sum()
    percentages = (missing_counts / max(len(data), 1) * 100).round(2)
    return pd.DataFrame({
        "Column": missing_counts.index,
        "Missing_Count": missing_counts.values,
        "Missing_Percent": percentages.values,
    }).sort_values("Missing_Count", ascending=False, ignore_index=True)


def save_to_sqlite(data: pd.DataFrame, database_path: str | Path) -> None:
    """Replace the SQLite game_sales table with the cleaned DataFrame."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        data.to_sql(TABLE_NAME, connection, if_exists="replace", index=False)
        connection.execute(
            f'CREATE INDEX IF NOT EXISTS idx_game_sales_genre ON "{TABLE_NAME}" (Genre)'
        )
        connection.execute(
            f'CREATE INDEX IF NOT EXISTS idx_game_sales_global_sales ON "{TABLE_NAME}" (Global_Sales)'
        )
        connection.commit()
    finally:
        connection.close()


def query_top_games(connection: sqlite3.Connection, limit: int = 10) -> pd.DataFrame:
    """Return the highest-selling games using a SQL query."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    return pd.read_sql_query(
        """
        SELECT Name, Platform, Global_Sales
        FROM game_sales
        WHERE Global_Sales IS NOT NULL
        ORDER BY Global_Sales DESC, Name ASC
        LIMIT ?
        """,
        connection,
        params=(int(limit),),
    )


def query_regional_sales(connection: sqlite3.Connection) -> pd.DataFrame:
    """Return total sales for the four regions from the SQL database."""
    return pd.read_sql_query(
        """
        SELECT 'North America' AS Region, SUM(NA_Sales) AS Total_Sales FROM game_sales
        UNION ALL
        SELECT 'Europe', SUM(EU_Sales) FROM game_sales
        UNION ALL
        SELECT 'Japan', SUM(JP_Sales) FROM game_sales
        UNION ALL
        SELECT 'Other', SUM(Other_Sales) FROM game_sales
        """,
        connection,
    ).fillna({"Total_Sales": 0.0})


def query_genre_sales(connection: sqlite3.Connection) -> pd.DataFrame:
    """Return game count, total sales, and average sales grouped by genre."""
    return pd.read_sql_query(
        """
        SELECT
            Genre,
            COUNT(*) AS Game_Count,
            SUM(Global_Sales) AS Total_Global_Sales,
            AVG(Global_Sales) AS Average_Global_Sales
        FROM game_sales
        GROUP BY Genre
        ORDER BY Total_Global_Sales DESC, Genre ASC
        """,
        connection,
    )


def create_visualizations(
    regional_sales: pd.DataFrame,
    genre_sales: pd.DataFrame,
    top_games: pd.DataFrame,
    output_dir: str | Path,
) -> list[Path]:
    """Save three charts and return their file paths."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    chart_paths: list[Path] = []

    # Chart 1: sales by region.
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(regional_sales["Region"], regional_sales["Total_Sales"], color="#287C87")
    ax.set_title("Video Game Sales by Region", fontsize=16, weight="bold")
    ax.set_ylabel("Sales (millions)")
    ax.set_xlabel("Region")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = output / "regional_sales.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    chart_paths.append(path)

    # Chart 2: total global sales by genre.
    genre_plot = genre_sales.sort_values("Total_Global_Sales", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(genre_plot["Genre"], genre_plot["Total_Global_Sales"], color="#E39B4A")
    ax.set_title("Total Global Sales by Genre", fontsize=16, weight="bold")
    ax.set_xlabel("Global sales (millions)")
    ax.set_ylabel("Genre")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = output / "genre_sales.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    chart_paths.append(path)

    # Chart 3: ten leading games. Game/platform labels distinguish releases.
    top_plot = top_games.sort_values("Global_Sales", ascending=True).copy()
    labels = top_plot["Name"].astype(str) + " (" + top_plot["Platform"].astype(str) + ")"
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(labels, top_plot["Global_Sales"], color="#5966A8")
    ax.set_title("Top 10 Games by Global Sales", fontsize=16, weight="bold")
    ax.set_xlabel("Global sales (millions)")
    ax.set_ylabel("Game")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = output / "top_10_games.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    chart_paths.append(path)

    return chart_paths


def run_pipeline(
    csv_path: str | Path,
    output_dir: str | Path,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the complete Sprint 1 load-clean-store-analyze-export workflow."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    db_path = Path(database_path) if database_path else output / "videogame_sales.db"

    raw_data = load_dataset(csv_path)
    cleaned_data = clean_data(raw_data)
    statistics = calculate_baseline_statistics(cleaned_data)
    missing_summary = summarize_missing_values(cleaned_data)
    save_to_sqlite(cleaned_data, db_path)

    connection = sqlite3.connect(db_path)
    try:
        top_games = query_top_games(connection, limit=10)
        regional_sales = query_regional_sales(connection)
        genre_sales = query_genre_sales(connection)
    finally:
        connection.close()

    regional_sales.to_csv(output / "regional_sales_summary.csv", index=False)
    genre_sales.to_csv(output / "genre_sales_summary.csv", index=False)
    top_games.to_csv(output / "top_10_games.csv", index=False)
    missing_summary.to_csv(output / "data_quality_summary.csv", index=False)
    chart_paths = create_visualizations(
        regional_sales, genre_sales, top_games, output
    )

    summary_lines = [
        "VIDEO GAME SALES ANALYTICS - SPRINT 1 OUTPUT",
        f"Records loaded: {statistics['record_count']:,}",
        f"Total global sales: {statistics['total_global_sales_millions']:,.2f} million",
        f"Average global sales per record: {statistics['average_global_sales_millions']:.3f} million",
        f"Highest global sales for one record: {statistics['maximum_global_sales_millions']:.2f} million",
        "",
        "REGIONAL SALES (millions):",
        regional_sales.to_string(index=False),
        "",
        "TOP 10 GAMES:",
        top_games.to_string(index=False),
        "",
        "GLOBAL SALES BY GENRE:",
        genre_sales.to_string(index=False),
        "",
        "MISSING VALUES AFTER CLEANING:",
        missing_summary.head(10).to_string(index=False),
    ]
    summary_path = output / "analysis_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print("\nSPRINT 1 PIPELINE COMPLETED")
    print(f"Rows processed: {statistics['record_count']:,}")
    print(f"Total global sales: {statistics['total_global_sales_millions']:,.2f} million")
    print(f"Average global sales per game record: {statistics['average_global_sales_millions']:.3f} million")
    print(f"Highest global sales for one record: {statistics['maximum_global_sales_millions']:.2f} million")
    print("\nRegional sales (millions):")
    print(regional_sales.to_string(index=False))
    print("\nTop 10 games:")
    print(top_games.to_string(index=False))
    print("\nGlobal sales by genre:")
    print(genre_sales.to_string(index=False))
    print("\nTop missing-value fields after cleaning:")
    print(missing_summary.head(10).to_string(index=False))
    print(f"\nSQLite database: {db_path}")
    print(f"Results and charts: {output}")

    return {
        "statistics": statistics,
        "regional_sales": regional_sales,
        "genre_sales": genre_sales,
        "top_games": top_games,
        "missing_summary": missing_summary,
        "chart_paths": chart_paths,
        "database_path": db_path,
        "summary_path": summary_path,
    }


def parse_args() -> argparse.Namespace:
    """Parse optional file locations from the command line."""
    project_folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Analyze the Video Game Sales dataset for Sprint 1."
    )
    parser.add_argument(
        "--csv", default=str(project_folder / DATASET_NAME),
        help="Path to Video_Games.csv (default: file beside Main.py).",
    )
    parser.add_argument(
        "--output-dir", default=str(project_folder / "outputs"),
        help="Folder where charts, CSV summaries, and text output are saved.",
    )
    parser.add_argument(
        "--database", default=None,
        help="Optional SQLite database path (default: outputs/videogame_sales.db).",
    )
    return parser.parse_args()


def main() -> None:
    """Run the application from the command line."""
    args = parse_args()
    run_pipeline(args.csv, args.output_dir, args.database)

