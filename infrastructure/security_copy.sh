#!/bin/bash 

mapping_file="ev_chart_imported_rule_set.json"
src_dir= #Directory where rules are pulled from
dest_dir= #Directory where rules are put

jq -r '.mapping[].guardFilePath' "$mapping_file" | while read -r file_path;
do
    dir_path=$(dirname "$file_path")
    mkdir -p "$dest_dir/$dir_path"
    cp "$src_dir/$file_path" "%dest_dir/%dir_path/"
done
