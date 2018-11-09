#!/usr/bin/env python

import os
import sys
import regex
import numpy as np
import datetime
# from functools import filter

# Set vars
coordsList = []
coordsDict = {}

input_name = 'au_riv_15s'
# input_name = 'test'
input_dir = '/mnt/c/Users/maarten/workspace/TerriaMap/wwwroot/rivers/' + input_name + '/'
input_file = input_dir + '/' + input_name + '.json'

# Get the input file
if input_dir is None:
    print("ERROR: configuration template dir not defined")
    sys.exit(1)

if not os.path.isdir(input_dir):
    print("ERROR: configuration template dir (%s) does not exist" % input_dir)
    sys.exit(1)

# Make ready to write the ouput file
result_dir = 'result/'
if not os.path.isdir(result_dir):
    os.mkdir(result_dir)

result_dir = 'result/' + input_name
if not os.path.isdir(result_dir):
    os.mkdir(result_dir)

output_file = result_dir + '/' + input_name +'.json'

# Calculate the Strahler and Shreve Orders for stream magnitude, recursively.
def getStrahlerAndShreve ( sourceLine, sourceCoords, sIndex, evaluated ):
    # If we have already evaluated this line, get the values from the coordsList
    if sIndex in evaluated:        
        return [coordsList[sIndex-1][3],coordsList[sIndex-1][4]]
    
    # Otherwise, append this index to the evaluated list so we don't do it twice
    evaluated.append(sIndex)

    # Set defaults
    allTributaries = []
    highestTributaryStrahler = 1

    # Get the coordinates to be evaluated, the first coordinates in the line
    firstCoordsOfSource = sourceCoords[0]
        
    # Loop over the lines to see if the last coordinates in that line match the first in ours
    if tuple(firstCoordsOfSource) in coordsDict:
        tributaries = coordsDict[tuple(firstCoordsOfSource)]        

        for t in tributaries:
            l = coordsList[t-1]
            line = l[1]
            coords = l[2]

            # If so, we need to calculate the Stream orders of our 'children'
            strahlerShreve = getStrahlerAndShreve(line, coords, t, evaluated)

            allTributaries.append(strahlerShreve)
            highestTributaryStrahler = max(highestTributaryStrahler, strahlerShreve[0])

    # Calculate the Strahler order, which only increases if multiple tributaries with the 
    # same (highest) order come together at this point
    # if there are no tributaries, this should be 1
    hits = 0
    strahlerOrder = 1
    for t in allTributaries:
        if t[0] == highestTributaryStrahler:
            hits = hits + 1

    if hits > 1:
        strahlerOrder = highestTributaryStrahler + 1
    else:
        strahlerOrder = highestTributaryStrahler

    # Calculate the Shreve order by adding all tributaries's Shreve orders
    # if there are no tributaries, this should be 1
    shreveOrder = 0
    if len(allTributaries) > 0:        
        for t in allTributaries:
            shreveOrder = shreveOrder + t[1]
    else:
        shreveOrder = 1

    # Add the calculated Strahler and Shreve orders to the coordsList
    coordsList[sIndex-1][3] = strahlerOrder
    coordsList[sIndex-1][4] = shreveOrder
    
    return [strahlerOrder, shreveOrder]

# Read all lines of the input file into a list with the following elements
# index, line (string), coordinates (list), strahler order (int), shreve order (int)
with open(input_file,'r') as f:
    for i, l in enumerate(f):
        l = l.rstrip()
        if not l: continue

        # The coordinates are extracted from the geojson and evaluated into a list 
        coords = regex.search(r'"coordinates":(\[.*\])', l)
        
        if coords:
            coordsNums = eval(coords.group(1))
            nums = np.array([coordsNums[0], coordsNums[-1]])
            # the Strahler and Shreve orders are set to default 1 here.
            coordsList.append([i, l, nums, 1, 1])

            tup = tuple(coordsNums[-1])
            
            if not tup in coordsDict:
                coordsDict[tup] = [i]
            else:
                coordsDict[tup].append(i)

# Open the ouput file so we can write to it
with open(output_file,'w+') as o:
    # Write geojson prefix
    o.write('{"type":"FeatureCollection", "features": [')

    # We keep a list of evaluated lines for optimization (so we don't evaluate twice)
    evaluated = []

    startTime = datetime.datetime.now().replace(microsecond=0)

    # For all input file lines
    for l in coordsList:
        index = l[0]
        line = l[1]
        coords = l[2]

        # the evaluated list is being appended to during the loop due to the recursive nature
        if not index in evaluated:
            strahlerShreve = getStrahlerAndShreve(line, coords, index, evaluated)

            # Print as a status indicator for the process
            print('done ' + str(index) + ' : ' + str(len(coordsList)))
        
    endTime = datetime.datetime.now().replace(microsecond=0)

    print ('Time taken: ' + str(endTime-startTime))

    # When done, write everything to the ouput file
    for l in coordsList:
        newLine = regex.sub(r'properties":{(.*?)}', r'properties":{\1,"STRAHLER":'+str(l[3])+',"SHREVE":'+str(l[4])+'}', l[1])
             
        o.write(newLine)

    # And add a postfix
    o.write(']}')

            