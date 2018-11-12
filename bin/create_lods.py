#!/usr/bin/env python

import os
import sys
import regex
import datetime
import argparse

def is_dir(dirname):
    # Checks if a path is an actual directory
    if not os.path.isdir(dirname):
        msg = '{0} is not a directory'.format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname

def write_lods(input_file, lod_files):
    for l in input_file:
        l = l.rstrip()
        if not l: continue

        # Get the Strahler Order
        match1 = regex.search(r'"SHREVE":(.*?)}', l)
        match2 = regex.search(r'"STRAHLER":(.*?),', l)
        
        if match1 and match2:
            shreve = eval(match1.group(1))
            strahler = eval(match2.group(1))

            # always write to the highest LOD
            length = len(lod_files)
            lod_files[length-1].write(l + '\n')
            
            # write the lines with higher strahler orders to the other LODS
            for i, f in enumerate(lod_files):
                if shreve > (length - i):
                    lod_files[i-1].write(l + '\n')

def main(args):
    for f in args.files:
        # Get the basename for this file, add '_out' to it for the output file
        input_name = os.path.basename(f.name)
        base_name = os.path.splitext(input_name)[0]

        lod_files = []
        for i in range(1, args.lods+1):
            name = args.output_dir + base_name + '_lod'+str(i)+'.json'
            o = open(name, 'w+')
            lod_files.append(o)
            
            # Write geojson prefix
            o.write('{"type":"FeatureCollection", "features": [\n')
            
        # Write lines
        write_lods(f, lod_files)

        # And add a postfix
        for i in range(1, args.lods+1):
            f = lod_files[i-1]
            print(f)
            last_line = f.seek(-3,2).read()
            # last_chars = regex.search(r'.{0,2}\z', lod_files[i-1].readline())
            print ('last ::'+ str(last_line) + '::')

            lod_files[i-1].write(']}\n\n')

if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='Calculate the Strahler and Shreve stream orders for the given river segments in GeoJSON.')
    parser.add_argument('-l','--lods', type=int, default=11)
    parser.add_argument('-o','--output_dir', type=is_dir, help='The output directory', default='.')
    parser.add_argument('files', type=argparse.FileType('r'), nargs='+', help='One or more geojson files')
    args = parser.parse_args()

    main(args)
    