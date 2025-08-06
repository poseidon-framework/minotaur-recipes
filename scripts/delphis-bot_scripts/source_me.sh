#!/usr/bin/env bash

HELPER_FUNCTION_VERSION='0.5.2'

## Print coloured messages to stderr
#   errecho -r will print in red
#   errecho -y will print in yellow
function errecho() {
  local Normal
  local Red
  local Yellow
  local colour

  Normal=$(tput sgr0)
  Red=$(tput sgr0)'\033[1;31m' ## Red normal face
  Yellow=$(tput sgr0)'\033[1;33m' ## Yellow normal face

  colour=''
  if [[ ${1} == '-y' ]]; then
    colour="${Yellow}"
    shift 1
  elif [[ ${1} == '-r' ]]; then
    colour="${Red}"
    shift 1
  fi
  echo -e ${colour}$*${Normal} 1>&2
}

## Function to check failure and stop execution
function check_fail() {
  if [[ ${1} != 0 ]]; then 
    errecho -r "${2}"
    exit ${1}
  fi
}

## Function to return index of item in bash array
## usage: get_index_of <value> "<array>" ## Array call MUST be quoted
#   i='banana'
#   list=("banana split" "apple" "potato" "banana" "apple")
#   get_index_of ${i} "${list[@]}" ## returns 3 ('banana split' =/= 'banana')
#   Returns: a list of all indexes that match the value.
#         -1 is returned if value is not found within the array.
function get_index_of() {
  local i
  local value
  local array
  local indices

  value=${1}
  shift 1
  array=("${@}")
  indices=''

  for i in "${!array[@]}"; do
    if [[ "${array[${i}]}" == "${value}" ]]; then
      indices+="${i} "
    fi
  done
  if [[ ${indices} != '' ]]; then
    echo ${indices}
  else
    echo "-1"
  fi
}

## Function to return index of item in bash array
#   i='banana'
#   list=("banana split" "apple" "potato" "banana" "apple")
#   get_index_of ${i} "${list[@]}" ## Array MUST be quoted
#   Returns: The number of times a value was found in the array. No partial matching (i.e. 'banana' will not match 'banana split')
function count_instances() {
  local i
  local value
  local array
  local result
  local i
  
  value="${1}"
  shift 1
  array=("${@}")
  let result=0

  for i in "${array[@]}"; do
    if [[ "${i}" == "${value}" ]]; then
      let result+=1
    fi
  done
  echo ${result}
}

## Function to return the number of entries in a field, given a specified delimiter
##  <delim> MUST be a single character
# usage: number_of_entries <delim> <field_contents>
# number_of_entries ';' 'ABC001;ABC001_subset' ## Returns 2
function number_of_entries() {
  local delim
  local value
  local result

  delim="${1}"
  value=($(echo ${2} | cut --output-delimiter ' ' -d ${delim} -f 1- ))
  let result=${#value[@]}

  echo ${result}
}

## Function to return the requested value from a list column, by index
##  <delim> MUST be a single character
##  <index> is 0-based
# usage: pull_by_index <delim> <field_contents> <index>
# pull_by_index ';' 'ABC001;ABC001_subset' 1 ## Returns 'ABC001_subset'
function pull_by_index() {
  local delim
  local value
  local index
  
  delim="${1}"
  value=($(echo ${2} | cut --output-delimiter ' ' -d ${delim} -f 1- ))
  let index=${3}

  echo ${value[${index}]}
}

## Function to return udg treatment based on janno entry
# usage: infer_library_udg 'half;minus;plus' 0
# The second argument (index) is 0-based
function infer_library_udg() {
  local value
  local index
  local result

  value=($(echo ${1} | cut --output-delimiter ' ' -d ';' -f 1- ))
  let index=${2}

  if [[ ${#value[@]} == '1' ]]; then
      if [[ ${value[0]} == 'mixed' ]]; then
        ## Mixed cannot deconstructed. Assume UDG none as that is most conservative.
        result='none'
      elif [[ ${value} == 'minus' ]]; then
        result='none'
      elif [[ ${value} == 'half' ]]; then
        result='half'
      elif [[ ${value} == 'plus' ]]; then
        result='full'
      else
        errecho "Unrecognised UDG_Treatment value: '${value}' in entry '${1}'"
        # exit 1
      fi
  else
      if [[ ${value[${index}]} == 'minus' ]]; then
        result='none'
      elif [[ ${value[${index}]} == 'half' ]]; then
        result='half'
      elif [[ ${value[${index}]} == 'plus' ]]; then
        result='full'
      else
        errecho "Unrecognised UDG_Treatment value: '${value[${index}]}' in entry '${1}'"
        # exit 1
      fi
  fi
  echo ${result}
}

## Function to return library strandedness based on janno entry
# usage: infer_library_udg 'ds;ds;ss' 0
# The second argument (index) is 0-based
function infer_library_strandedness() {
  local value
  local index
  local result
  
  value=( $(echo "${1}" | cut -d ';' --output-delimiter " " -f 1-) )
  let index=${2}

  if [[ ${#value[@]} == '1' ]]; then
      if [[ ${value[0]} == 'other' ]]; then
        ## Other cannot be deconstructed. Assuming double stranded since that is more conservative when genotyping (everything trimmed)
        result='double'
      elif [[ ${value} == 'ds' ]]; then
        result='double'
      elif [[ ${value} == 'ss' ]]; then
        result='single'
      else
        errecho "Unrecognised Library_Built value: '${value}' in entry '${1}'"
        # exit 1
      fi
  else
      if [[ ${value[${index}]} == 'ds' ]]; then
        result='double'
      elif [[ ${value[${index}]} == 'ss' ]]; then
        result='single'
      else
        errecho "Unrecognised Library_Built value: '${value[${index}]}' in entry '${1}'"
        # exit 1
      fi
  fi
  echo ${result}
}

## Function to create R1 and R2 columns from ena_table fastq_fn entries
#   usage: r1_r2_from_ena_fastq <fastq_ftp> <submitted_ftp>
#   Returns: a quadrupple of: seq_type R1 R2 BAM
function r1_r2_from_ena_fastq() {
  local value
  local value2
  local r1
  local r2
  local bam
  local seq_type
  local n_entries

  value="${1}"
  value2="${2}"

  ## BAMs containing collapsed PE reads will have 3 entries in the ENA (merged, R1 unmerged, R2 unmerged), but we only need the first (merged reads).
  n_entries=$(number_of_entries ';' ${value})

  r1="NA"
  r2="NA"
  bam="NA"
  if [[ ${value} == "n/a" || ${n_entries} -eq 0 ]]; then
    ## If there are no entries, then use the BAM (assumed SE). Check that the submitted_ftp is a BAM happens in main script.
    bam=$(basename "$(pull_by_index ';' "${value2}" 0)") ## This ensures we pull the BAM when a bai is also provided.
    seq_type="SE"
  elif [[ ${n_entries} -eq 2 ]]; then
    ## If there are two entries, then it's PE
    r1=$(basename "$(pull_by_index ';' ${value} 0)")
    r2=$(basename "$(pull_by_index ';' ${value} 1)")
    seq_type="PE"
  elif [[ ${n_entries} -eq 1  || ${n_entries} -eq 3 ]]; then
    ## If there is only one entry, then it's SE. With three, it is a BAM with collapsed reads, so keep only merged reads (treat as SE).
    r1=$(basename "$(pull_by_index ';' ${value} 0)")
    seq_type="SE"
  else
    errecho -r "Unexpected number of entries in fastq_ftp field: ${value}."
    exit 1
  fi

  echo "${seq_type} ${r1} ${r2} ${bam}"
}

## Function to create R1 and R2 columns from ena_table fastq_fn entries
#   usage: dummy_r1_r2_from_ena_fastq <path_prefix> <out_fn_prefix> <fastq_ftp>
#   Returns: a quadrupple of: seq_type R1 R2 BAM
function dummy_r1_r2_from_ena_fastq() {
  local prefix
  local out_fn_prefix
  local value
  local r1
  local r2
  local seq_type
  local n_entries
  local bam

  prefix="${1}"
  out_fn_prefix="${2}"
  value="${3}"

  ## BAMs containing collapsed PE reads will have 3 entries in the ENA (merged, R1 unmerged, R2 unmerged), but we only need the first (merged reads).
  n_entries=$(number_of_entries ';' ${value})

  r1="${prefix}/${out_fn_prefix}_R1.fastq.gz"
  bam="NA"
  if [[ ${value} == "n/a" || ${n_entries} -eq 0 ]]; then
    ## If there are no entries, then use the BAM (assumed SE). Check that the submitted_ftp is a BAM happens in main script.
    r1="NA"
    r2="NA"
    bam="${prefix}/${out_fn_prefix}.bam"
    seq_type="SE"
  elif [[ ${n_entries} -eq 2 ]]; then
    ## If there are two entries, then it's PE
    r2="${prefix}/${out_fn_prefix}_R2.fastq.gz"
    seq_type="PE"
  elif [[ ${n_entries} -eq 1 || ${n_entries} -eq 3 ]]; then
    ## If there is only one entry, then it's SE. With three, it is a BAM with collapsed reads, so keep only merged reads (treat as SE).
    r2="NA"
    seq_type="SE"
  else
    errecho -r "Unexpected number of entries in fastq_ftp field: ${value}."
    exit 1
  fi

  echo "${seq_type} ${r1} ${r2} ${bam}"
}

## Function to infer colour chemistry from an ENA-approved instrument model
#   Usage: infer_colour_chemistry ${instrument_platform} ${instrument_model}
#   Returns: The colour chemistry for the specified sequencer. Throw error and stop if the platform or sequencer are not identified.
function infer_colour_chemistry() {
  local platform
  local model
  local one_chem_seqs
  local two_chem_seqs
  local four_chem_seqs
  local colour_chemistry

  platform=${1}
  model=${2}
  ## Hard-coded list of sequencers per colour chemistry
  one_chem_seqs=("Illumina iSeq 100") ## Not sure eager can process this, but good to have a record of it.
  two_chem_seqs=("NextSeq 2000" "NextSeq 1000" "NextSeq 500" "NextSeq 550" "Illumina NovaSeq 6000" "Illumina NovaSeq X" "Illumina NovaSeq X Plus" "Illumina MiniSeq")
  four_chem_seqs=("Illumina HiSeq 1000" "Illumina HiSeq 1500" "Illumina HiSeq 2000" "Illumina HiSeq 2500" "Illumina HiSeq 3000" "Illumina HiSeq 4000" "Illumina HiSeq X" "Illumina HiSeq X Five" "Illumina HiSeq X Ten" "HiSeq X Five" "HiSeq X Ten" "Illumina Genome Analyzer" "Illumina Genome Analyzer II" "Illumina Genome Analyzer IIx" "Illumina HiScanSQ" "Illumina MiSeq")
  colour_chemistry=''

  ## Throw an error if sequencer is not ILLUMINA
  if [[ ${platform} != "ILLUMINA" ]]; then
    check_fail 5 "Colour chemistry inference only works for ILLUMINA sequencing platforms, not '${platform}'."
  else
    if   [[ $(get_index_of "${model}" "${four_chem_seqs[@]}") != '' ]]; then
      colour_chemistry="4"
    elif [[ $(get_index_of "${model}" "${two_chem_seqs[@]}") != '' ]]; then
      colour_chemistry="2"
    else
      check_fail 5 "Illumina model '${model}' not recognised. Please ensure your instrument model is in an ENA-approved format"
    fi
  fi

  echo ${colour_chemistry}
}