
"""Verify the Video Game Sales SQLite database."""

import sqlite3
from pathlib import Path


# Find the database created by Main.py
PROJECT_FOLDER = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_FOLDER / "outputs" / "videogame_sales.db"


def verify_database():
    """Check database contents and run sample SQL queries."""

    if not DATABASE_PATH.exists():
        print("Database not found.")
        print("Please run py Main.py first.")
        return

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("\nVIDEO GAME SALES DATABASE CHECK")
        print("=" * 45)

        # 1. Check that the table exists.
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table';
            """
        ).fetchall()

        print("\nTables in database:")
        for table in tables:
            print("-", table[0])

        # 2. Count all records.
        result = connection.execute(
            "SELECT COUNT(*) FROM game_sales;"
        ).fetchone()

        print("\nTotal records:", result[0])

        # 3. Show the first five games.
        print("\nFIRST FIVE GAMES")

        rows = connection.execute(
            """
            SELECT Name, Platform, Genre, Global_Sales
            FROM game_sales
            ORDER BY Global_Sales DESC
            LIMIT 5;
            """
        ).fetchall()

        for row in rows:
            print(row)

        # 4. Find the top five publishers.
        print("\nTOP FIVE PUBLISHERS")

        publishers = connection.execute(
            """
            SELECT Publisher,
                   SUM(Global_Sales) AS Total_Sales
            FROM game_sales
            WHERE Publisher IS NOT NULL
              AND Publisher != 'Unknown'
            GROUP BY Publisher
            ORDER BY Total_Sales DESC
            LIMIT 5;
            """
        ).fetchall()

        for publisher in publishers:
            print(publisher)

        # 5. Compare sales by platform.
        print("\nTOP FIVE PLATFORMS")

        platforms = connection.execute(
            """
            SELECT Platform,
                   SUM(Global_Sales) AS Total_Sales
            FROM game_sales
            GROUP BY Platform
            ORDER BY Total_Sales DESC
            LIMIT 5;
            """
        ).fetchall()

        for platform in platforms:
            print(platform)

        # 6. Examine sales by release year.
        print("\nSALES BY RELEASE YEAR")

        years = connection.execute(
            """
            SELECT Year_of_Release,
                   SUM(Global_Sales) AS Total_Sales
            FROM game_sales
            WHERE Year_of_Release IS NOT NULL
            GROUP BY Year_of_Release
            ORDER BY Year_of_Release DESC
            LIMIT 10;
            """
        ).fetchall()

        for year in years:
            print(year)

        print("\nDATABASE VERIFICATION COMPLETED")

    except sqlite3.Error as error:
        print("Database error:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    verify_database()
