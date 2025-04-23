#!/usr/bin/env python3

## Script originally made by Stephan Schiffels (@stschiff). Edited by Luca Thale-Bombien (@Kavlahkaff) for specific use in this repository (added empty poseidon_IDs, udg and library_built columns).

import argparse
import io

import requests
import re
import pandas as pd
import openpyxl


headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
VALID_PLATFORMS = [
        "NextSeq 1000",
        "NextSeq 500",
        "NextSeq 550",
        "Illumina NextSeq 1000",
        "Illumina NextSeq 500",
        "Illumina NextSeq 550",
        "Illumina NovaSeq 6000",
        "Illumina MiniSeq",
        "Illumina HiSeq 1000",
        "Illumina HiSeq 1500",
        "Illumina HiSeq 2000",
        "Illumina HiSeq 2500",
        "Illumina HiSeq 3000",
        "Illumina HiSeq 4000",
        "Illumina HiSeq X",
        "HiSeq X Five",
        "HiSeq X Ten",
        "Illumina HiSeq X Five",
        "Illumina HiSeq X Ten",
        "Illumina Genome Analyzer",
        "Illumina Genome Analyzer II",
        "Illumina Genome Analyzer IIx",
        "Illumina HiScanSQ",
        "Illumina MiSeq",
    ]


def extract_release_date(accession_number: str) -> str:
    requests_text = requests.get(f"https://ngdc.cncb.ac.cn/gsa-human/browse/{accession_number}", headers=headers).text
    release_date_match = re.search(r'<b>Release date:</b>\s*</span>\s*</div>\s*<div class="col-md-9">\s*([\d-]+)', requests_text)
    date = release_date_match.group(1) if release_date_match else "n/a"
    return date


def download_xlsx(accession_number: str) -> pd.ExcelFile:
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
    if response.status_code == 200:
        print(f"Successfully downloaded file with url: {download_url}")

        # Load the content into pandas from memory (without saving to disk)
        excel_data = pd.ExcelFile(io.BytesIO(response.content))

        return excel_data  # Return the ExcelFile object
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
        return None

def create_ssf_from_df(df: pd.DataFrame, cols_to_add: dict, output_file: str):
    data = {}
    try:
        for key, value in cols_to_add.items():
            data[key] = ["n/a"] * len(df)
            if key == "study_accession":
                data[key] = [args.accession_id] * len(df)
            elif key =="instrument_model":
                for model in df[value].tolist():
                    if model not in VALID_PLATFORMS:
                        print(f"Invalid instrument model: {model}, stopping ssf creation")
                        return
                data[key] = df[value].tolist()
            elif key == "instrument_platform":
                data[key] = ["Illumina"] * len(df)
            elif key == "first_public" or key == "last_updated":
                data[key] = [RELEASE_DATE] * len(df)
            elif key == "submitted_ftp":
                if df["Run data file type"][0] == "bam":
                    data[key] = df[value].tolist()
                    data["bam_md5"] = df["MD5 checksum 1"].tolist()
                    if not df["DownLoad2"].isnull().all():
                        print(df["DownLoad2"])
                        data[key] = [a_ + b_ for a_, b_ in zip(df[value].tolist(), df["DownLoad2"].tolist())]
                        data["bam_md5"] = [a_ + ";" + b_ for a_, b_ in zip(df["MD5 checksum 1"].tolist(), df["MD5 checksum 2"].tolist())]
                else:
                    data["fastq_ftp"] = df[value].tolist()
                    data["fastq_md5"] = df["MD5 checksum 1"].tolist()
                    if not df["Download2"].isnull().all():
                        data["fastq_ftp"] = [a_ + b_ for a_, b_ in zip(df[value].tolist(), df["DownLoad2"].tolist())]
                        data["fastq_md5"] = [a_ + ";" + b_ for a_, b_ in zip(df["MD5 checksum 1"].tolist(), df["MD5 checksum 2"].tolist())]

            elif value and value in df.columns and not df[value].isnull().all():
                data[key] = df[value].tolist()
    except Exception as e:
        print(f"Failed to create ssf file due to: {e}")


    result_df = pd.DataFrame(data)
    result_df.to_csv(output_file, index=False, sep='\t')
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
    "sample_accession" : "Accession",
    "study_accession": None,
    "run_accession": "Accession_Run",
    "sample_alias": "Individual Name",
    "secondary_sample_accession": None,
    "first_public": "first_public",
    "last_updated": "last_updated",
    "instrument_model": "Platform",
    "library_layout": "Layout",
    "library_source": "Source",
    "instrument_platform": None,
    "library_name": "Library name",
    "library_strategy": "Strategy",
    "fastq_ftp": None,
    "fastq_aspera": None,
    "fastq_bytes": None,
    "fastq_md5": None,
    "read_count": None,
    "bam_md5": None,
    "submitted_ftp": "DownLoad1",
}



RELEASE_DATE = extract_release_date(args.accession_id)
xls = download_xlsx(args.accession_id)

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
        # This takes care of empty cells in original xlsx file
        merged_df.replace('', 'n/a', inplace=True)

create_ssf_from_df(merged_df, gsa_cols, args.output_file)





