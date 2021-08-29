#!/bin/bash

dir=${PWD##*/}
ext="wav"
IFS="-"
a=1
last=""
isFolderFeatureEnabled=true
for i in *.$ext; do
    read -a strarr <<< "${i%%.*}"
    if [[ "$last" != "${strarr[0]}" ]] ;then
        last=${strarr[0]}
        if [ ! -d "$last" ] && [ $isFolderFeatureEnabled ]; then
            mkdir -p "$last";
        fi
        let a=1
    fi
    new=$(printf "${strarr[0]}_%03d_A$dir.$ext" "$a")
    mv -i -- "$i" "$last/$new"
    let a=a+1
done
