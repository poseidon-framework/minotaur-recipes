#!/usr/bin/env python

# MIT License (c) 2023 Thiseas C. Lamnidis

VERSION = "0.3.0dev"

import os
import sys
import errno
import argparse
import re


def read_ssf_file(file_path, required_fields=None, error_counter=0):
    file_name = os.path.basename(file_path.name)
    l = file_path.readlines()
    headers = l[0].split()
    global SSF_HEADER  ## Pull header out of function scope
    SSF_HEADER = headers
    if required_fields:
        for field in required_fields:
            if field not in headers:
                error_counter = print_error(
                    "[Missing required field] Required field '{}' not found in header! Cannot validate non-existing entries.".format(
                        field
                    ),
                    "",
                    "",
                    error_counter,
                    file_name,
                )
        if error_counter > 0:
            print(
                "[Formatting check] {} column existence error(s) were detected in the input SSF file. Ensure all required columns are present and retry validation.\nRequired columns:\n\t{}".format(
                    error_counter, "\n\t".join(required_fields)
                )
            )
            sys.exit(1)
    return map(lambda row: dict(zip(headers, row.strip().split("\t"))), l[1:])


def isNAstr(var):
    x = False
    if isinstance(var, str) and var == "n/a":
        x = True
    return x


def parse_args(args=None):
    Description = (
        "Validate a poseidon-formatted SSF file for use by the Minotaur pipeline."
    )
    Epilog = "Example usage: python ssf_validator.py <FILE_IN>"

    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    parser.add_argument("FILE_IN", help="Input SSF file.")
    return parser.parse_args(args)


def make_dir(path):
    if len(path) > 0:
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise exception


def print_error(error, context="Line", context_str="", error_counter=0, file_name=""):
    if file_name == "":
        raise ValueError("fn cannot be empty!")
    if isinstance(context_str, str):
        context_str = "'{}'".format(context_str.strip())
    error_str = "[ssf_validator.py] [File: {}] Error in SSF file: {}".format(
        file_name, error
    )
    if context != "" and context_str != "":
        error_str = (
            "[ssf_validator.py] [File: {}] Error in SSF file @ {} {}: {}".format(
                file_name, context.strip(), context_str, error
            )
        )
    print(error_str)
    error_counter += 1
    return error_counter


def complain_about_spaces(row_entries, error_counter, line_num, file_name):
    for key in row_entries.keys():
        if row_entries[key].startswith(" ") or row_entries[key].endswith(" "):
            error_counter = print_error(
                "[Spacing found in TSV entries] SSF entries cannot start or end with whitespace.",
                "Line",
                line_num,
                error_counter,
                file_name,
            )
    return error_counter


def validate_poseidon_ids(poseidon_ids, error_counter, line_num, file_name):
    ## Poseidon IDs should not end in ';'
    ##   If a list, the `;` will be within the field, not at the end or start. If a single value, it should not have `;` at all.
    if poseidon_ids.endswith(";") or poseidon_ids.startswith(";"):
        error_counter = print_error(
            "[Invalid poseidon_IDs formatting] poseidon_ids cannot start or end in ';'.",
            "Line",
            line_num,
            error_counter,
            file_name,
        )

    ## Poseidon IDs cannot be missing or 'n/a'
    if not poseidon_ids:
        error_counter = print_error(
            "[Poseidon_ID missing] poseidon_ids entry has not been specified!",
            "Line",
            line_num,
            error_counter,
            file_name,
        )
    elif isNAstr(poseidon_ids):
        error_counter = print_error(
            "[Poseidon_ID missing] poseidon_ids cannot be 'n/a'!",
            "Line",
            line_num,
            error_counter,
            file_name,
        )

    return error_counter


def validate_date_field(date_field, field_name, error_counter, line_num, file_name):
    # Define the regex pattern for "YYYY-MM-DD" format
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    # Check if the date string matches the pattern
    if not re.match(pattern, date_field):
        error_counter = print_error(
            f"[Invalid date formatting] {field_name} '{date_field}' is not valid. Date fields must be in YYYY-MM-DD format.",
            "Line",
            line_num,
            error_counter,
            file_name,
        )
    return error_counter


def validate_instrument_model(instrument_model, error_counter, line_num, file_name):
    two_chem_seqs = [
        "NextSeq 1000",
        "NextSeq 500",
        "NextSeq 550",
        "Illumina NovaSeq 6000",
        "Illumina MiniSeq",
    ]
    four_chem_seqs = [
        "Illumina HiSeq 1000",
        "Illumina HiSeq 1500",
        "Illumina HiSeq 2000",
        "Illumina HiSeq 2500",
        "Illumina HiSeq 3000",
        "Illumina HiSeq 4000",
        "Illumina HiSeq X",
        "HiSeq X Five",
        "HiSeq X Ten",
        "Illumina Genome Analyzer",
        "Illumina Genome Analyzer II",
        "Illumina Genome Analyzer IIx",
        "Illumina HiScanSQ",
        "Illumina MiSeq",
    ]

    if instrument_model not in two_chem_seqs + four_chem_seqs:
        error_counter = print_error(
            "[Invalid instrument_model formatting] instrument_model '{}' is not recognised as one that can be processed with nf-core/eager. Accepted values: {}".format(
                instrument_model, ", ".join(two_chem_seqs + four_chem_seqs)
            ),
            "Line",
            line_num,
            error_counter,
            file_name,
        )
    return error_counter


def validate_ssf(file_in):
    """
    This function checks that the SSF file contains all the expected columns, and validated the entries in the columns needed for Minotaur processing.
    """

    file_name = os.path.basename(file_in)
    error_counter = 0
    with open(file_in, "r") as fin:
        ## Check header
        MIN_COLS = 7  ## Minimum number of non missing columns
        HEADER = [
            "poseidon_IDs",  ## Required
            "udg",  ## Required
            "library_built",  ## Required
            "sample_accession",
            "study_accession",
            "run_accession",
            "sample_alias",
            "secondary_sample_accession",
            "first_public",
            "last_updated",
            "instrument_model",  ## Required
            "library_layout",
            "library_source",
            "instrument_platform",  ## Required
            "library_name",  ## Required
            "library_strategy",
            "fastq_ftp",  ## Required
            "fastq_aspera",
            "fastq_bytes",
            "fastq_md5",
            "read_count",
            "submitted_ftp",
        ]
        REQUIRED_FIELDS = [
            "poseidon_IDs",
            "udg",
            "library_built",
            "instrument_model",
            "instrument_platform",
            "library_name",
            "fastq_ftp",
        ]

        ## Check entries
        for line_num, ssf_entry in enumerate(
            read_ssf_file(fin, required_fields=REQUIRED_FIELDS)
        ):
            line_num += (
                2  ## From 0-based to 1-based. Add an extra 1 for the header line
            )

            # Check valid number of columns per row
            # for key in ssf_entry.keys():
            #     print(key, "=", ssf_entry[key])
            # print(ssf_entry)
            if len(ssf_entry) < len(SSF_HEADER):
                error_counter = print_error(
                    "[Missing columns in row] Invalid number of columns (expected {}, got {})!".format(
                        len(SSF_HEADER), len(ssf_entry)
                    ),
                    "Line",
                    line_num,
                    error_counter,
                    file_name,
                )

            ## Check for spaces in entries
            error_counter = complain_about_spaces(
                ssf_entry, error_counter, line_num, file_name
            )

            ## Validate poseidon IDs
            error_counter = validate_poseidon_ids(
                ssf_entry["poseidon_IDs"], error_counter, line_num, file_name
            )

            ## Validate UDG
            # print(ssf_entry["udg"])
            if ssf_entry["udg"] not in ["minus", "half", "plus"]:
                error_counter = print_error(
                    "[Invalid udg formatting] udg entry '{}' is not recognised. Options: minus, half, plus.".format(
                        ssf_entry["udg"]
                    ),
                    "Line",
                    line_num,
                    error_counter,
                    file_name,
                )

            ## Validate library_built
            if ssf_entry["library_built"] not in ["ds", "ss"]:
                error_counter = print_error(
                    "[Invalid library_built formatting] library_built entry '{}' is not recognised. Options: ds, ss.".format(
                        ssf_entry["library_built"]
                    ),
                    "Line",
                    line_num,
                    error_counter,
                    file_name,
                )

            ## Validate date fields (first_public, last_updated) if present
            if "first_public" in ssf_entry:
                error_counter = validate_date_field(
                    ssf_entry["first_public"],
                    "first_public",
                    error_counter,
                    line_num,
                    file_name,
                )
            if "last_updated" in ssf_entry:
                error_counter = validate_date_field(
                    ssf_entry["last_updated"],
                    "last_updated",
                    error_counter,
                    line_num,
                    file_name,
                )

            ## Validate instrument_model
            error_counter = validate_instrument_model(
                ssf_entry["instrument_model"], error_counter, line_num, file_name
            )

            ## Validate instrument_platform
            if ssf_entry["instrument_platform"] not in ["ILLUMINA"]:
                error_counter = print_error(
                    "[Invalid instrument_platform] instrument_platform entry '{}' is not recognised. Options: ILLUMINA.".format(
                        ssf_entry["instrument_platform"]
                    ),
                    "Line",
                    line_num,
                    error_counter,
                    file_name,
                )

            ## Validate library_name
            if not ssf_entry["library_name"]:
                error_counter = print_error(
                    "[Library_name missing] library_name entry has not been specified!",
                    "Line",
                    line_num,
                    error_counter,
                    file_name,
                )
            elif isNAstr(ssf_entry["library_name"]):
                error_counter = print_error(
                    "[Library_name missing] library_name cannot be 'n/a'!",
                    "Line",
                    line_num,
                    error_counter,
                    file_name,
                )

            ## Validate fastq_ftp
            for reads in [ssf_entry["fastq_ftp"]]:
                ## Can be empty string in some cases where input is a BAM, but then data won't be processes (atm)
                if isNAstr(reads):
                    error_counter = print_error(
                        "[Fastq_ftp is 'n/a'] fastq_ftp cannot be 'n/a'!",
                        "Line",
                        line_num,
                        error_counter,
                        file_name,
                    )
                elif reads.find(" ") != -1:
                    error_counter = print_error(
                        "[Spaces in FastQ name] File names cannot contain spaces! Please rename.",
                        "Line",
                        line_num,
                        error_counter,
                        file_name,
                    )
                ## Check that the fastq_ftp entry ends with a valid extension
                elif (
                    not reads.endswith(".fastq.gz")
                    and not reads.endswith(".fq.gz")
                    and not reads.endswith(".fastq")
                    and not reads.endswith(".fq")
                    and not reads == ""
                ):
                    error_counter = print_error(
                        "[Invalid FastQ file extension] FASTQ file(s) have unrecognised extension. Allowed extensions: .fastq.gz, .fq.gz, .fastq, .fq!",
                        "Line",
                        line_num,
                        error_counter,
                        file_name,
                    )

    ## If formatting errors have occurred print their number and fail.
    if error_counter > 0:
        print(
            "[Formatting check] [File: {}] {} formatting error(s) were detected in the input file. Please check samplesheet.".format(
                file_name,
                error_counter,
            )
        )
        sys.exit(1)
    ## if no formatting errors have occurred, print success message and exit.
    else:
        print(
            "[Formatting check] [File: {}] No formatting errors were detected in the input file.".format(
                file_name
            )
        )
        sys.exit(0)


def main(args=None):
    args = parse_args(args)
    validate_ssf(args.FILE_IN)


if __name__ == "__main__":
    print("[ssf_validator.py]: version {}".format(VERSION), file=sys.stderr)
    sys.exit(main())
