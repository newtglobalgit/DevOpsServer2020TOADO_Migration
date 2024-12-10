import pandas as pd

def compare_discovery_reports(source_file, target_file, output_file):
    # Load source and target Excel files into DataFrames
    source_df = pd.read_excel(source_file)
    target_df = pd.read_excel(target_file)

    # Standardize column names (if necessary)
    source_df.columns = source_df.columns.str.strip()
    target_df.columns = target_df.columns.str.strip()

    # Add an indicator column to identify rows from source and target
    source_df["Source Status"] = "Exists"
    target_df["Target Status"] = "Exists"

    # Rename columns in source and target to distinguish them
    source_df = source_df.rename(
        columns={
            "project_name": "project_name_Source",
            "file_path": "file_path_Source",
            "size_(bytes)": "size_(bytes)_Source",
            "last_modified": "last_modified_Source",
        }
    )
    target_df = target_df.rename(
        columns={
            "project_name": "project_name_Target",
            "file_path": "file_path_Target",
            "size_(bytes)": "size_(bytes)_Target",
            "last_modified": "last_modified_Target",
        }
    )

    # Merge the source and target data, keeping all columns
    comparison_df = pd.merge(
        source_df, target_df,
        how="outer",
        left_on=["project_name_Source", "file_path_Source", "size_(bytes)_Source", "last_modified_Source"],
        right_on=["project_name_Target", "file_path_Target", "size_(bytes)_Target", "last_modified_Target"],
        indicator=True
    )

    # Add a match status column based on the merge indicator
    comparison_df["Match Status"] = comparison_df["_merge"].apply(
        lambda x: "Match" if x == "both" else "Mismatch"
    )

    # Drop the '_merge' column
    comparison_df.drop(columns=["_merge"], inplace=True)

    # Rearrange columns: source columns, target columns, and then status columns
    source_columns = ["project_name_Source", "file_path_Source", "size_(bytes)_Source", "last_modified_Source"]
    target_columns = ["project_name_Target", "file_path_Target", "size_(bytes)_Target", "last_modified_Target"]
    status_columns = ["Source Status", "Target Status", "Match Status"]

    # Reorder columns
    ordered_columns = source_columns + target_columns + status_columns
    comparison_df = comparison_df[ordered_columns]

    # Write the reconciliation report to an Excel file
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        comparison_df.to_excel(writer, sheet_name="Reconciliation Report", index=False)

    print(f"Reconciliation report saved as {output_file}")

# File paths for source, target, and output files
source_file = "Wiki_Discovery_Report.xlsx"
target_file = "Wiki_Target_Discovery_Report.xlsx"
output_file = "Wiki_Reconciliation_Report.xlsx"

# Run the comparison
compare_discovery_reports(source_file, target_file, output_file)
