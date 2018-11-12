#!/usr/bin/env python

import os
import sys
import regex
import numpy as np
import datetime
import argparse

# Calculate the Strahler and Shreve Orders for stream magnitude, recursively.
def getStrahlerAndShreve ( sourceLine, sourceCoords, sIndex, evaluated, coordsList, coordsDict ):
    # If we have already evaluated this line, get the values from the coordsList
    if sIndex in evaluated:        
        return [coordsList[sIndex-1][3],coordsList[sIndex-1][4]]
    
    # Otherwise, append this index to the evaluated list so we don't do it twice
    evaluated.add(sIndex)

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
            strahlerShreve = getStrahlerAndShreve(line, coords, t, evaluated, coordsList, coordsDict)

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

def main(args):
    for f in args.files:
        # Set vars
        coordsList = []
        coordsDict = {}

        # Get the basename for this file, add '_out' to it for the output file
        input_name = os.path.basename(f.name)
        output_file = os.path.splitext(input_name)[0] + '_out.json'
        
        if (args.time):
            startTime = datetime.datetime.now().replace(microsecond=0)

        if (args.verbose):
            print ('reading input file and constructing dictionary')
        
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
        
        if (args.time):
            endTime = datetime.datetime.now().replace(microsecond=0)
            print ('Dictionary construction time taken: ' + str(endTime-startTime))

        # Open the ouput file so we can write to it
        with open(output_file,'w+') as o:
            if (args.time):
                startTime = datetime.datetime.now().replace(microsecond=0)

            if (args.verbose):
                print ('start stream order calculations')            

            # Keep a list of evaluated lines for optimization (so we don't evaluate twice)
            evaluated = set({})

            # For all input file lines
            for l in coordsList:
                index = l[0]
                line = l[1]
                coords = l[2]

                # the evaluated list is being appended to during the loop due to the recursive nature
                if not index in evaluated:
                    getStrahlerAndShreve(line, coords, index, evaluated, coordsList, coordsDict)

                    # Print as a status indicator for the process
                    if (args.verbose):
                        print('done ' + str(index) + ' : ' + str(len(coordsList)))
            
            if (args.time):
                endTime = datetime.datetime.now().replace(microsecond=0)
                print ('Order calculations time taken: ' + str(endTime-startTime))

            # When done, write everything to the ouput file
            if (args.time):
                startTime = datetime.datetime.now().replace(microsecond=0)

            if (args.verbose):
                print ('writing output to ' + output_file)

            # Write geojson prefix
            o.write('{"type":"FeatureCollection", "features": [\n')

            # Write lines
            for l in coordsList:
                newLine = regex.sub(r'properties":{(.*?)}', r'properties":{\1,"STRAHLER":'+str(l[3])+',"SHREVE":'+str(l[4])+'}', l[1])                
                o.write(newLine + '\n')

            # And add a postfix
            o.write(']}\n\n')        
            
            if (args.time):
                endTime = datetime.datetime.now().replace(microsecond=0)
                print ('Output written, time taken: ' + str(endTime-startTime))

if __name__ == "__main__":
    sys.setrecursionlimit(2000)

    # parse arguments
    parser = argparse.ArgumentParser(description='Calculate the Strahler and Shreve stream orders for the given river segments in GeoJSON.')
    parser.add_argument('-v','--verbose', help="increase output verbosity", action='store_true')
    parser.add_argument('-t','--time', help="calculate and display time taken", action='store_true')
    parser.add_argument('files', type=argparse.FileType('r'), nargs='+', help='one or more geojson files')
    args = parser.parse_args()

    main(args)
    