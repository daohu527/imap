search_dir=xodr
output_dir=apollo_map

echo "Generate Apollo map or not? [True/False]"
read generate_apollo

if [ $generate_apollo == True ]
    then
        rm -rf $output_dir
        mkdir $output_dir
fi

for entry in "$search_dir"/*

do
    if [ $generate_apollo == True ]
    then
        file_name=${entry##*/}
        base_name=${file_name%%.*}
        # echo ${file_name%%.*}
        cd $output_dir
        mkdir $base_name
        cd ..
        python run.py -f -i $entry -o $output_dir/$base_name/apollo_map.txt
    else
        python run.py -m $entry
    fi
done
