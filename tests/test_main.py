import sqlite3

import numpy as np
import pandas as pd
import pytest

from video_game_sales import (
    calculate_baseline_statistics,
    clean_data,
    query_genre_sales,
    query_regional_sales,
    query_top_games,
    run_pipeline,
    save_to_sqlite,
)


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "Name": ["Game A", "Game B", "Game C"],
            "Platform": ["PC", "Console", "PC"],
            "Year_of_Release": [2020, "2019", None],
            "Genre": ["Action", "Sports", None],
            "Publisher": ["Studio A", None, "Studio C"],
            "NA_Sales": [1.0, 2.0, 0.5],
            "EU_Sales": [0.5, 1.0, 0.2],
            "JP_Sales": [0.1, 0.2, 0.3],
            "Other_Sales": [0.2, 0.3, 0.1],
            "Global_Sales": [1.8, 3.5, 1.1],
            "Critic_Score": [80, None, 70],
            "Critic_Count": [10, None, 5],
            "User_Score": ["8.1", "tbd", "7.2"],
            "User_Count": [100, None, 50],
            "Developer": ["Dev A", "Dev B", "Dev C"],
            "Rating": ["E", "T", "E"],
        }
    )


def test_clean_data_converts_numbers_and_tbd(sample_data):
    cleaned = clean_data(sample_data)
    assert cleaned["Year_of_Release"].dtype.kind in "fi"
    assert cleaned.loc[1, "Year_of_Release"] == 2019
    assert cleaned.loc[1, "User_Score"] != cleaned.loc[1, "User_Score"]  # NaN
    assert cleaned.loc[0, "User_Score"] == pytest.approx(8.1)


def test_clean_data_fills_unknown_categories_and_keeps_rows(sample_data):
    cleaned = clean_data(sample_data)
    assert len(cleaned) == 3
    assert cleaned.loc[2, "Genre"] == "Unknown"
    assert cleaned.loc[1, "Publisher"] == "Unknown"


def test_clean_data_rejects_missing_required_columns(sample_data):
    incomplete = sample_data.drop(columns=["Global_Sales"])
    with pytest.raises(ValueError, match="Global_Sales"):
        clean_data(incomplete)


def test_numpy_baseline_statistics(sample_data):
    cleaned = clean_data(sample_data)
    stats = calculate_baseline_statistics(cleaned)
    assert stats["record_count"] == 3
    assert stats["total_global_sales_millions"] == pytest.approx(6.4)
    assert stats["average_global_sales_millions"] == pytest.approx(6.4 / 3)
    assert stats["maximum_global_sales_millions"] == pytest.approx(3.5)


def test_sql_storage_and_queries(sample_data, tmp_path):
    cleaned = clean_data(sample_data)
    db_path = tmp_path / "test_games.db"
    save_to_sqlite(cleaned, db_path)

    connection = sqlite3.connect(db_path)
    try:
        top = query_top_games(connection, limit=2)
        regions = query_regional_sales(connection)
        genres = query_genre_sales(connection)
    finally:
        connection.close()

    assert top.iloc[0]["Name"] == "Game B"
    assert len(top) == 2
    assert regions.loc[regions["Region"] == "North America", "Total_Sales"].iloc[0] == pytest.approx(3.5)
    action = genres.loc[genres["Genre"] == "Action"].iloc[0]
    assert action["Game_Count"] == 1
    assert action["Total_Global_Sales"] == pytest.approx(1.8)


def test_pipeline_creates_outputs(sample_data, tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_dir = tmp_path / "outputs"
    sample_data.to_csv(csv_path, index=False)

    result = run_pipeline(csv_path, output_dir)

    assert result["statistics"]["record_count"] == 3
    assert result["database_path"].exists()
    assert result["summary_path"].exists()
    assert (output_dir / "regional_sales_summary.csv").exists()
    assert (output_dir / "genre_sales_summary.csv").exists()
    assert (output_dir / "top_10_games.csv").exists()
    assert (output_dir / "data_quality_summary.csv").exists()
    assert len(result["chart_paths"]) == 3
    assert all(path.exists() and path.stat().st_size > 0 for path in result["chart_paths"])
