#!/usr/bin/env bash

## Track the version of the TSV_patch template used
VERSION='0.1.0dev'

## This script is applied to the eager input TSV file locally to edit the dummy
##    path to the fastQ files added by `create_eager_input.sh` to a real local
##    path provided as a positional argument. Any further local tweaks to the
##    TSV before running eager should be added below that in the form of bash
##    commands to aid in reproducibility.

## usage tsv_patch.sh <local_data_dir> <input_tsv>

local_data_dir="$(readlink -f ${1})"
input_tsv="$(readlink -f ${2})"
output_tsv="$(dirname ${local_data_dir})/$(basename -s ".tsv" ${input_tsv}).finalised.tsv"

sed -e "s|<PATH_TO_DATA>|${local_data_dir}|g" ${input_tsv} > ${output_tsv}

## Any further commands to edit the file before finalisation should be added below as shown
# sed -ie 's/replace_this/with_this/g' ${output_tsv}
