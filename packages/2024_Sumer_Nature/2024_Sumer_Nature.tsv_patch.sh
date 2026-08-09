#!/usr/bin/env bash
set -uo pipefail ## Pipefail, complain on new unassigned variables.

## Track the version of the TSV_patch template used
VERSION='0.2.1dev'

## This script is applied to the eager input TSV file locally to edit the dummy
##    path to the fastQ files added by `create_eager_input.sh` to a real local
##    path provided as a positional argument. Any further local tweaks to the
##    TSV before running eager should be added below that in the form of bash
##    commands to aid in reproducibility.

## usage tsv_patch.sh <local_data_dir> <input_tsv> <path/to/source_me.sh>

local_data_dir="$(readlink -f ${1})"
input_tsv="$(readlink -f ${2})"
output_tsv="$(dirname ${local_data_dir})/$(basename -s ".tsv" ${input_tsv}).finalised.tsv"
columns_to_keep=("Sample_Name" "Library_ID" "Lane" "Colour_Chemistry" "SeqType" "Organism" "Strandedness" "UDG_Treatment" "R1" "R2" "BAM")
source $(readlink -f ${3}) ## Path to helper function script should be provided as 3rd argument. https://github.com/poseidon-framework/poseidon-eager/blob/main/scripts/source_me.sh

## Index non-proliferated columns and exclude them from the finalised TSV
cut_selector=''
tsv_header=($(head -n1 ${input_tsv}))
for col_name in ${columns_to_keep[@]}; do
  let idx=$(get_index_of ${col_name} "${columns_to_keep[@]}")+1 ## awk uses 1-based indexing
  if [[ ! ${idx} -eq -1 ]]; then
    cut_selector+="${idx},"
  fi
done

## Remove added columns, and put columns in right order
cut -f ${cut_selector%,} ${input_tsv} > ${output_tsv}
sed -i -e "s|<PATH_TO_DATA>|${local_data_dir}|g" ${output_tsv}

## Any further commands to edit the file before finalisation should be added below as shown
# sed -ie 's/replace_this/with_this/g' ${output_tsv}

## Keep track of versions
version_file="$(dirname ${input_tsv})/script_versions.txt"
##    Remove versions from older run if there
grep -v -F -e "$(basename ${0})" -e "source_me.sh for final TSV" ${version_file} >${version_file}.new
##    Then add new versions
echo -e "$(basename ${0}):\t${VERSION}" >> ${version_file}.new
echo -e "source_me.sh for final TSV:\t${HELPER_FUNCTION_VERSION}" >>${version_file}.new
mv ${version_file}.new ${version_file}
