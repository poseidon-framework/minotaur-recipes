#!/usr/bin/env python3

## Script originally made by Stephan Schiffels (@stschiff). Edited by Luca Thale-Bombien (@Kavlahkaff) for specific use in this repository (added empty poseidon_IDs, udg and library_built columns).

import argparse
import requests
import re
import pandas as pd
import openpyxl

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
def download_xlsx(accession_number: str):
    requests_text = requests.get(f"https://ngdc.cncb.ac.cn/gsa-human/browse/{accession_number}", headers=headers).text
    base_url = "https://ngdc.cncb.ac.cn"

    action_match = re.search(r"f\.action\s*=\s*[\"']([^\"']+)[\"']", requests_text)
    study_id_match = re.search(r"var study_id\s*=\s*'(\d+)'", requests_text)
    request_flag_match = re.search(r"var requestFlag\s*=\s*'(\d+)'", requests_text)
    file_path_match = re.search(r"downHumanExcel\('(.+?)'\)", requests_text)

    if file_path_match:
        file_name = file_path_match.group(1)
    else:
        print("File path not found.")

    action = action_match.group(1) + "exportExcelFile" if action_match else None
    study_id = study_id_match.group(1) if study_id_match else None
    request_flag = request_flag_match.group(1) if request_flag_match else None
    file_path = f"{action}?fileName={file_name}&study_id={study_id}&requestFlag={request_flag}"

    # Construct the full URL
    download_url = base_url + file_path
    # Send GET request to download the file
    print(f"attempting to download file with url: {download_url}")
    response = requests.get(download_url, stream=True)

    # Check if request was successful
    if response.status_code == 200:
        print(f"Successfully downloaded file with url: {download_url}, now writing to file")
        with open("HRA008755.xlsx", "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print("Download complete and file saved as: HRA008755.xlsx")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")


def create_ssf_from_df(df: pd.DataFrame, cols_to_add: dict, output_file: str):
    data = {}
    for key, value in cols_to_add.items():
        if key == "instrument_platform" and value in df.columns and not df[value].isna().all():
            data[key] = df[value].apply(lambda x: x.split(" ")[0] if isinstance(x, str) else "n/a").tolist()
        elif value and value in df.columns and not df[value].isnull().all():
            data[key] = df[value].tolist()
        else:
            data[key] = ["n/a"] * len(df)

    result_df = pd.DataFrame(data)
    result_df.to_csv(output_file, index=False)
    print(f"'{output_file}' created successfully.")


parser = argparse.ArgumentParser(
    prog='get_gsa_table',
    description='This script downloads a table with '
                'links to the raw data and metadata provided by '
                'GSA for a given project accession ID')

parser.add_argument('accession_id', help="Example: HRA008755")
parser.add_argument('-o', '--output_file', required=True, help="The name of the output file")

args = parser.parse_args()

gsa_cols = {
    "poseidon_IDs": None,
    "udg": None,
    "library_built": None,
    "notes": None,
    "sample_accession" : "Accession_Sample",
    "study_accession": "Accession_Experiment",
    "run_accession": "Accession_Run",
    "sample_alias": "Individual Name",
    "secondary_sample_accession": None,
    "first_public": "first_public",
    "last_updated": "last_updated",
    "instrument_model": "Platform",
    "library_layout": "Layout",
    "library_source": "Source",
    "instrument_platform": "Platform",
    "library_name": "Library name",
    "library_strategy": "Strategy",
    "fastq_ftp": "DownLoad1",
    "fastq_aspera": None,
    "fastq_bytes": None,
    "fastq_md5": None,
    "read_count": None,
    "submitted_ftp": None,
}

download_xlsx(args.accession_id)

xls = pd.ExcelFile(f"./{args.accession_id}.xlsx")

column_mappings = {
    "Individual": "Individual Name",
    "Sample": "Sample Name",
    "Experiment": "Experiment title",
    "Run": "Run title"
}

# Read all sheets and rename the column for consistency
dfs = {}
for sheet, col_name in column_mappings.items():
    df = xls.parse(sheet)
    df.rename(columns={col_name: "Individual Name"}, inplace=True)  # Standardized column name
    dfs[sheet] = df

# Merge all DataFrames on standardized column 'Individual Name' using an outer join
merged_df = None
for sheet_name, df in dfs.items():
    if merged_df is None:
        merged_df = df  # Initialize with the first sheet
    else:
        merged_df = merged_df.merge(df, on="Individual Name", how="outer", suffixes=("", "_"+sheet_name))

create_ssf_from_df(merged_df, gsa_cols, args.output_file)





