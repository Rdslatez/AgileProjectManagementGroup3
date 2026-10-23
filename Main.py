import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# STEP 1: Load Dataset
print("Loading Video Game Sales dataset...")

try:
    df = pd.read_csv("Video_Games.csv")
    print(f"Dataset loaded successfully! Total records: {len(df):,}")
    print(df.head())
except FileNotFoundError:
    print("Error: Video_Games.csv was not found.")
    print("Place the CSV file in the same folder as this script.")
    raise SystemExit(1)

# STEP 2: Data Cleaning and NumPy Analysis
print("\nCleaning data...")

df.columns = df.columns.str.strip()

# Standardize column names
df.rename(columns={
    "Global Sales": "Global_Sales",
    "NA Sales": "NA_Sales",
    "EU Sales": "EU_Sales",
    "JP Sales": "JP_Sales",
    "Other Sales": "Other_Sales",
    "Year of Release": "Year_of_Release"
}, inplace=True)

# Clean release year
if "Year_of_Release" in df.columns:
    df["Year_of_Release"] = pd.to_numeric(
        df["Year_of_Release"], errors="coerce"
    )
elif "Year" in df.columns:
    df["Year"] = pd.to_numeric(
        df["Year"], errors="coerce"
    )

# Fill missing publisher values
if "Publisher" in df.columns:
    df["Publisher"] = df["Publisher"].fillna("Unknown")

# Convert sales columns to numeric
sales_columns = [
    "Global_Sales",
    "NA_Sales",
    "EU_Sales",
    "JP_Sales",
    "Other_Sales"
]

for column in sales_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

# NumPy statistics
if "Global_Sales" in df.columns:
    global_sales_array = df["Global_Sales"].dropna().to_numpy()

    if global_sales_array.size > 0:
        print("\n--- NumPy Baseline Summary ---")
        print(f"Total Global Sales: {np.sum(global_sales_array):,.2f} million")
        print(f"Average Global Sales per Game: {np.mean(global_sales_array):.2f} million")
        print(f"Max Global Sales for a Single Game: {np.max(global_sales_array):.2f} million")
    else:
        print("No valid global sales data available.")
else:
    print("Warning: Global_Sales column not found.")

# STEP 3: Create and Load SQLite Database
print("\nConnecting to SQLite database...")

conn = sqlite3.connect("videogame_sales.db")

try:
    df.to_sql(
        "game_sales",
        conn,
        if_exists="replace",
        index=False
    )

    print("Data successfully loaded into SQL table 'game_sales'!")

    # STEP 4: SQL Queries and Visualizations

    # Query 1: Top 10 Games by Global Sales
    required_columns = {"Name", "Platform", "Global_Sales"}

    if required_columns.issubset(df.columns):
        query_top10 = """
            SELECT Name, Platform, Global_Sales
            FROM game_sales
            WHERE Global_Sales IS NOT NULL
            ORDER BY Global_Sales DESC
            LIMIT 10;
        """

        top10_df = pd.read_sql_query(query_top10, conn)

        print("\n--- Top 10 Games by Global Sales ---")
        print(top10_df.to_string(index=False))
    else:
        print("Cannot run top 10 query: required columns are missing.")

    # Query 2: Regional Sales Totals
    regional_columns = [
        "NA_Sales",
        "EU_Sales",
        "JP_Sales",
        "Other_Sales"
    ]

    if all(column in df.columns for column in regional_columns):
        query_regional = """
            SELECT
                SUM(NA_Sales) AS Total_NA,
                SUM(EU_Sales) AS Total_EU,
                SUM(JP_Sales) AS Total_JP,
                SUM(Other_Sales) AS Total_Other
            FROM game_sales;
        """

        regional_df = pd.read_sql_query(query_regional, conn)

        print("\n--- Regional Sales Totals ---")
        print(regional_df.to_string(index=False))

        # Create regional sales chart
        regions = [
            "North America",
            "Europe",
            "Japan",
            "Other"
        ]

        totals = regional_df.iloc[0].fillna(0).to_numpy(dtype=float)

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(8, 5))

        sns.barplot(
            x=regions,
            y=totals,
            hue=regions,
            palette="viridis",
            legend=False
        )

        plt.title("Total Video Game Sales by Region")
        plt.ylabel("Sales (Millions)")
        plt.xlabel("Region")
        plt.tight_layout()

        plt.savefig(
            "regional_sales_summary.png",
            dpi=300,
            bbox_inches="tight"
        )

        print("\nChart saved as 'regional_sales_summary.png'")
        plt.show()

    else:
        print("Cannot create chart: regional sales columns are missing.")

finally:
    conn.close()

print("\nETL Pipeline Executed Successfully!")
