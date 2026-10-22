#!/usr/bin/env bash
set -eu

input=$1
csv_output=$2
json_output=$3
mkdir -p "$(dirname "$csv_output")" "$(dirname "$json_output")"

awk -F, -v csv="$csv_output" -v json="$json_output" '
  NR == 1 { next }
  NF != 2 || $1 == "" { exit 2 }
  {
    count++
    total += $2
  }
  END {
    if (count == 0) exit 3
    mean = total / count
    printf "count,total,mean\n%d,%.0f,%.2f\n", count, total, mean > csv
    printf "{\n  \"count\": %d,\n  \"total\": %.0f,\n  \"mean\": %.2f\n}\n", count, total, mean > json
  }
' "$input"
