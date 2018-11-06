#!/bin/bash

mkdir $1
/mnt/c/Users/maarten/workspace/mapshaper/bin/mapshaper /mnt/c/Users/maarten/Downloads/shapes/$1/$1.shp -filter 'UP_CELLS > 2000' -simplify 10% -o format=geojson $1/