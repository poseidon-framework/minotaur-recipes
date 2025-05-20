#!/usr/bin/env bash
VERSION='0.5.1'
set -o pipefail ## Pipefail, complain on new unassigned variables.

## Helptext function
function Helptext() {
  echo -ne "\t usage: ${0} [options] Package_name\n\n"
  echo -ne "This script reads the information present in the ena_table of a poseidon package and creates a TSV file that can be used for processing the publicly available data with nf-core/eager.\n\n"
  echo -ne "Options:\n"
  echo -ne "-h, --help\t\tPrint this text and exit.\n"
  echo -ne "-v, --version \t\tPrint version and exit.\n"
}

## Source helper functions
repo_dir=$(dirname $(readlink -f ${0}))/../..  ## The repository will be the original position of this script. If a user copies instead of symlink, this will fail.
source ${repo_dir}/scripts/delphis-bot_scripts/source_me.sh        ## Source helper functions

## Parse CLI args.
TEMP=`getopt -q -o hv --long help,version -n "${0}" -- "$@"`
eval set -- "${TEMP}"

## Parameter defaults
package_name=''
# root_download_dir='/mnt/archgen/poseidon/raw_sequencing_data'
# root_output_dir='/mnt/archgen/poseidon/raw_sequencing_data/eager'

## Print helptext and exit when no option is provided.
if [[ "${#@}" == "1" ]]; then
  Helptext
  exit 0
fi

## Read in CLI arguments
while true ; do
  case "$1" in
    -h|--help)          Helptext; exit 0 ;;
    -v|--version)       echo ${VERSION}; exit 0;;
    --)                 package_name="${2}"; break ;;
    *)                  echo -e "invalid option provided.\n"; Helptext; exit 1;;
  esac
done

## Throw error if expected positional argument is not there.
if [[ ${package_name} == '' ]]; then
  errecho -r "No package name provided."
  Helptext
  exit 0
fi

package_dir="${repo_dir}/packages/${package_name}"
ena_table="${package_dir}/${package_name}.ssf"
tsv_patch="${package_dir}/tsv_patch.sh"
raw_data_dummy_path='<PATH_TO_DATA>'

## Error if input ssf or directory does not exist
if [[ ! -d ${package_dir} ]]; then
  check_fail 1 "[${package_name}]: Package directory '${package_dir}' does not exist."
fi

if [[ ! -f ${ena_table} ]]; then
  check_fail 1 "[${package_name}]: No sequencingSourceFile found for package. Check that file ${ena_table} exists."
fi

## Read required info from yml file
# package_rawdata_dir="${root_download_dir}/${package_name}"
out_file="${package_dir}/${package_name}.tsv"
version_file="${package_dir}/script_versions.txt"

## This will all break down if the headers contain whitespace.
ssf_header=($(head -n1 ${ena_table}))

## Check that all expected columns are in the input file
req_cols=('poseidon_IDs' 'library_name' 'instrument_model' 'instrument_platform' 'fastq_ftp' 'library_built' 'udg')
missing_cols=''
for col in ${req_cols[@]}; do
  col_idx=$(get_index_of "${col}" "${ssf_header[@]}")
  if [[ ${col_idx} -eq -1 ]]; then
    missing_cols+="'${col}', "
  fi
done

if [[ ${missing_cols} != '' ]]; then
  check_fail 1 "[${package_name}]: Some columns are missing from the SSF file. Please check the SSF file and retry.\n\tMissing columns: ${missing_cols%, }"
fi

## Infer column indices
let pid_col=$(get_index_of 'poseidon_IDs' "${ssf_header[@]}")+1
let lib_name_col=$(get_index_of 'library_name' "${ssf_header[@]}")+1
let instrument_model_col=$(get_index_of 'instrument_model' "${ssf_header[@]}")+1
let instrument_platform_col=$(get_index_of 'instrument_platform' "${ssf_header[@]}")+1
let fastq_col=$(get_index_of 'fastq_ftp' "${ssf_header[@]}")+1
let submitted_col=$(get_index_of 'submitted_ftp' "${ssf_header[@]}")+1
let lib_built_col=$(get_index_of 'library_built' "${ssf_header[@]}")+1
let lib_udg_col=$(get_index_of 'udg' "${ssf_header[@]}")+1

## Keep track of observed values
poseidon_ids=()
library_ids=()
let missing_fastq_count=0
let submitted_is_not_bam_count=0

## Paste together stuff to make a TSV. Header will flush older tsv if it exists.
errecho -y "[${package_name}] Creating TSV input for nf-core/eager (v2.*)."
echo -e "Sample_Name\tLibrary_ID\tLane\tColour_Chemistry\tSeqType\tOrganism\tStrandedness\tUDG_Treatment\tR1\tR2\tBAM\tR1_target_file\tR2_target_file\tBAM_target" > ${out_file}
organism="Homo sapiens (modern human)"
while read line; do
  poseidon_id=$(echo "${line}" | awk -F "\t" -v X=${pid_col} '{print $X}')
  lib_name=$(echo "${line}" | awk -F "\t" -v X=${lib_name_col} '{print $X}')
  fastq_fn=$(echo "${line}" | awk -F "\t" -v X=${fastq_col} '{print $X}')         # | rev | cut -d "/" -f 1 | rev )
  submitted_fn=$(echo "${line}" | awk -F "\t" -v X=${submitted_col} '{print $X}')
  instrument_model=$(echo "${line}" | awk -F "\t" -v X=${instrument_model_col} '{print $X}')
  instrument_platform=$(echo "${line}" | awk -F "\t" -v X=${instrument_platform_col} '{print $X}')
  colour_chemistry=$(infer_colour_chemistry "${instrument_platform}" "${instrument_model}")
  library_built_field=$(echo "${line}" | awk -F "\t" -v X=${lib_built_col} '{print $X}')
  udg_treatment_field=$(echo "${line}" | awk -F "\t" -v X=${lib_udg_col} '{print $X}')
  ## in the ssf file, these fields should correspond to single fastQ, so they should never be list values anymore.
  library_built=$(infer_library_strandedness ${library_built_field} 0)
  udg_treatment=$(infer_library_udg ${udg_treatment_field} 0)

  ## If there is no FastQ file for this entry, skip it.
  if [[ -z ${fastq_fn}  || ${fastq_fn} == "n/a" ]] && [[ ${submitted_fn} =~ \.(bam|bai)$ ]]; then
    ## Count the number of entries without a FastQ file, but with a BAM file.
    let missing_fastq_count+=1
    ## These entries get the BAM picked up so they can be converted within eager.
  elif [[ -z ${fastq_fn} ]]; then
    ## Count number of entries without a FastQ file, where the submitted file is not BAM.
    let submitted_is_not_bam_count+=1
    ## These get skipped and a warning is printed at the end.
    continue
  fi

  ## One set of sequencing data can correspond to multiple poseidon_ids
  for index in $(seq 1 1 $(number_of_entries ';' ${poseidon_id})); do
    row_pid=$(pull_by_index ';' ${poseidon_id} "${index}-1")
    ## Add _ss suffix to sample_name (and later library_id) if single stranded (data never gets merged with double stranded data in eager).
    if [[ "${library_built}" == "single" ]]; then
      strandedness_suffix='_ss'
      row_pid+=${strandedness_suffix}
    else
      strandedness_suffix=''
    fi

    row_lib_id="${row_pid}_${lib_name}${strandedness_suffix}" ## paste poseidon ID with Library ID to ensure unique naming of library results (both with suffix)
    let lane=$(count_instances ${row_lib_id} "${library_ids[@]}")+1

    ## Get intended input file names on local system (R1, R2)
    read -r seq_type r1 r2 bam < <(dummy_r1_r2_from_ena_fastq "${raw_data_dummy_path}" "${row_lib_id}_L${lane}" "${fastq_fn}")
    ## Also add column with the file that those will symlink to, for transparency during PR review.
    read -r seq_type2 r1_target r2_target bam_target < <(r1_r2_from_ena_fastq "${fastq_fn}" "${submitted_fn}")
    echo -e "${row_pid}\t${row_lib_id}\t${lane}\t${colour_chemistry}\t${seq_type}\t${organism}\t${library_built}\t${udg_treatment}\t${r1}\t${r2}\t${bam}\t${r1_target}\t${r2_target}\t${bam_target}" >> ${out_file}

    ## Keep track of observed values
    poseidon_ids+=(${row_pid})
    library_ids+=(${row_lib_id})
  done

done < <(tail -n +2 ${ena_table})

## Print warning if there are lines with missing FastQ files
if [[ ${missing_fastq_count} -gt 0 ]]; then
  errecho -y "[${package_name}] There are ${missing_fastq_count} entries in the SSF file without a FastQ file.\n\tUsing submitted BAM instead."
fi
if [[ ${submitted_is_not_bam_count} -gt 0 ]]; then
  errecho -y "[${package_name}] There are ${submitted_is_not_bam_count} entries in the SSF file without a FastQ file or BAM file.\n\tThese entries have been ignored."
fi

errecho -y "[${package_name}] TSV creation completed"

## Keep track of versions
##    This is the first part of the pipeline, so always flush any older versions, since everything needs rerunning.
echo -e "$(basename ${0}):\t${VERSION}" > ${version_file}
echo -e "source_me.sh for initial TSV:\t${HELPER_FUNCTION_VERSION}" >>${version_file}
