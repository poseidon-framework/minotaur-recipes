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

SSF_COLUMNS = {
    "poseidon_IDs": "Individual Name",
    "udg": None,
    "library_built": None,
    "notes": None,
    "run_accession": "Run accession",
    "study_accession": None,
    "sample_accession" : "Individual accession",
    "sample_alias": "Individual Name",
    "secondary_sample_accession": None,
    "first_public": "first_public",
    "last_updated": "last_updated",
    "instrument_model": "Platform",
    "library_layout": "Layout",
    "library_source": "Source",
    "instrument_platform": "Platform",
    "library_name": "Experiment title",
    "library_strategy": "Strategy",
    "fastq_ftp": "DownLoad1;DownLoad2",
    "fastq_aspera": None,
    "fastq_bytes": None,
    "fastq_md5": "MD5 checksum 1;MD5 checksum 2",
    "read_count": None,
    "submitted_ftp": "DownLoad1",
    "submitted_md5": "MD5 checksum 1",
}

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

def merge_sheets_by_accessions(xls: pd.ExcelFile, accession_col_name: str) -> pd.DataFrame:
    """Merges all sheets in the GSA Excel file into one large pandas dataframe, based on the accession number in each sheet.

    Args:
        xls (pd.ExcelFile): The Excel file object containing the sheets to be merged.
        accession_col_name (str): The name of the column containing the accession numbers in each sheet.
            This should be the same for all sheets, and should be the accession of the row in the current sheet (i.e. the Run Accession for the Runs sheet).

    Returns:
        pd.DataFrame: A merged pandas dataframe containing all the data from the sheets, merged by their corresponding accession numbers.
    """
    ## Rename "Accession" column of each sheet to include sheet name.
    dfs = {}
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, dtype=str)
        df.rename(columns={"Accession": f"{sheet} accession"}, inplace=True)  # Standardized column name
        dfs[sheet] = df
    ## One additional rename for the Experiment sheet
    dfs["Experiment"].rename(columns={"BioSample accession": "Sample accession"}, inplace=True)
    ## One additional rename for the Sample sheet (seems not standardised capitalisation in the GSA file)
    dfs["Sample"].rename(columns={"Individual Accession": "Individual accession"}, inplace=True)
    
    ## Merge dataframes in hierarchical order
    merged_df = None
    ## dfs.keys = ['Individual', 'Sample', 'Experiment', 'Run'], as is the order in the excel file.
    for sheet_name, df in dfs.items():
        if merged_df is None:
            merged_df = df  # Initialize with the first sheet (Individual)
        else:
            merged_df = merged_df.merge(df, on=f"{last_sheet_name} accession", how="outer", suffixes=("", "_"+sheet_name))
            # This takes care of empty cells in original xlsx file
            merged_df.replace('', 'n/a', inplace=True)
        ## Keep track of the last sheet name for the next iteration
        last_sheet_name = sheet_name
    
    ## This takes care of empty cells in original xlsx file
    merged_df.fillna('n/a', inplace=True)
    return merged_df

## Helper formatter to combine values in the two provided columns if the file_type value DOES NOT match the type_matches value.
def combine_values(file_type:str, type_matches: str, value1: str, value2: str) -> str:
    if file_type == type_matches:
        result = 'n/a'
    elif value2 == "n/a":
        result = f"{value1}"
    else:
        result = f"{value1};{value2}"
    return result

def df_to_ssf_df(df: pd.DataFrame, cols_to_add: dict, accession_number: str) -> pd.DataFrame:
    data = {}
    try:
        for key, value in cols_to_add.items():
            data[key] = ["n/a"] * len(df)
            if key == "study_accession":
                data[key] = [accession_number] * len(df)
            elif key =="instrument_model":
                for model in df[value].tolist():
                    if model not in VALID_PLATFORMS:
                        print(f"Invalid instrument model: {model}, stopping ssf creation")
                        return
                data[key] = df[value].tolist()
            elif key == "instrument_platform":
                data[key] = ["ILLUMINA"] * len(df)
            elif key == "first_public" or key == "last_updated":
                data[key] = [extract_release_date(accession_number)] * len(df)
            elif key == "fastq_ftp":
                data[key] = df.apply(lambda row: combine_values(row['Run data file type'], 'bam', row['DownLoad1'], row['DownLoad2']), axis=1)
            elif key == "fastq_md5":
                data[key] = df.apply(lambda row: combine_values(row['Run data file type'], 'bam', row['MD5 checksum 1'], row['MD5 checksum 2']), axis=1)
            elif value and value in df.columns and not df[value].isnull().all():
                data[key] = df[value].tolist()
    except Exception as e:
        print(f"Failed to create ssf file due to: {e}")
    result_df = pd.DataFrame(data)
    print(f"Created ssf file with {len(result_df)} rows and {len(result_df.columns)} columns.")
    return result_df

def save_ssf_to_file(df: pd.DataFrame, output_file: str) -> None:
    df.to_csv(output_file, index=False, sep='\t')
    print(f"'{output_file}' created successfully.")

def main(accession_number: str = None, output_file: str = None) -> None:
    ## TODO: work out how to see if the data gets updated after initial release.
    xls          = download_xlsx(accession_number)
    merged_df    = merge_sheets_by_accessions(xls, "Accession")
    ssf          = df_to_ssf_df(merged_df, SSF_COLUMNS, accession_number)

    ## Save SSF to file.
    save_ssf_to_file(ssf, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    prog='get_gsa_table',
    description='This script downloads a table with '
                'links to the raw data and metadata provided by '
                'GSA for a given project accession ID')

    parser.add_argument('accession_number', help="Example: HRA008755")
    parser.add_argument('-o', '--output_file', required=True, help="The name of the output file")

    args = parser.parse_args()
    main(args.accession_number, args.output_file)