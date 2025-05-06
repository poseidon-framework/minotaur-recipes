#!/usr/bin/env python3

## Script originally made by Stephan Schiffels (@stschiff). Edited by Thiseas C. Lamnidis (@TCLamnidis) for specific use in this repository (added empty poseidon_IDs, udg and library_built columns).

import argparse
import sys
import urllib.request


def add_columns_to_ena_table(ena_table_lines, column_names=None, column_value=None, byte_encoding="utf-8"):
    """
    Add columns with given name and value to the ENA table
    """
    ## column_names is required
    if column_names is None:
        raise ValueError("column_names is required")
    ## should be a list
    elif type(column_names) is list:
        columns_to_add = column_names
    ## or a single string
    elif type(column_names) is str:
        columns_to_add = [column_names]
    else:
        raise ValueError("column_names must be a list or a string")
    
    ## column_names is required and a single string
    if column_value is None:
        raise ValueError("column_value is required")
    elif type(column_value) is not str:
        raise ValueError("column_value must be a string")
    
    ## Convert the column names and values to bytes
    added_columns = ("\t".join(columns_to_add) + "\t").encode(byte_encoding)
    added_values  = ("\t".join([column_value] * len(columns_to_add)) + "\t").encode(byte_encoding)
    
    l = ena_table_lines
    ## Add the columns to the start of the header and the values to the start of each line
    l[0] = added_columns+l[0]
    for i in range(1, len(l)):
        l[i] = added_values + l[i]
    
    return l

parser = argparse.ArgumentParser(
    prog = 'get_ena_table',
    description = 'This script downloads a table with '
                    'links to the raw data and metadata provided by '
                    'ENA for a given project accession ID')

parser.add_argument('accession_id', help="Example: PRJEB39316")
parser.add_argument('-o', '--output_file', required=True, help="The name of the output file")

args = parser.parse_args()

ena_cols = [
    "sample_accession", 
    "study_accession", 
    "run_accession", 
    "sample_alias", 
    "secondary_sample_accession", 
    "first_public", 
    "last_updated", 
    "instrument_model", 
    "library_layout", 
    "library_source", 
    "instrument_platform", 
    "library_name", 
    "library_strategy", 
    "fastq_ftp", 
    "fastq_aspera", 
    "fastq_bytes", 
    "fastq_md5", 
    "read_count", 
    "submitted_ftp",
    "submitted_md5",
    ]

additional_cols = ["poseidon_IDs", "udg", "library_built", "notes"]

ena_col_str = ",".join(ena_cols)

url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={args.accession_id}&\
result=read_run&fields={ena_col_str}&format=tsv&limit=0"

# print(url)
print(f"[create_ssf_from_ena_project.py] Attempting to download the ENA table using the following URL: {url}", file=sys.stderr)

result = urllib.request.urlopen(url)

## Try to infer byte encoding from the server. if not provided use utf-8 as default.
byte_encoding = result.headers.get_content_charset()
if byte_encoding is None:
    byte_encoding = "utf-8"

with result:
    l = result.readlines()
    ## Add additional columns to the pulled table
    ##   result.headers.get_content_charset() can be used to get the encoding used from the URL server, however the ENA does not provide that. If provided use that instead of utf-8
    l = add_columns_to_ena_table(l, column_names = additional_cols, column_value = "n/a", byte_encoding = byte_encoding)

with open(args.output_file, "wb") as f:
    f.writelines(l)
