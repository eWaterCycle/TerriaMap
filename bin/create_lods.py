#!/usr/bin/env python

import os
import sys
import regex
import datetime
import argparse
import json
import numpy as np
import struct

def writeHeader(output_name, feature_table_length):
  total_length = 44 + feature_table_length
  with open(output_name, 'wb') as output_file:
    magic = 'vctr'

    # magic	4-byte ANSI string	"vctr". This can be used to identify the arraybuffer as a Vector tile.
    output_file.write(struct.pack('4s', magic.encode('utf-8')))
    # version	uint32	The version of the Vector Data format. It is currently 1.
    output_file.write(struct.pack('I', 1))
    # byteLength	uint32	The length of the entire tile, including the header, in bytes.
    output_file.write(struct.pack('I', total_length))
    # featureTableJSONByteLength	uint32	The length of the feature table JSON section in bytes.
    output_file.write(struct.pack('I', feature_table_length))
    # featureTableBinaryByteLength	uint32	The length of the feature table binary section in bytes. 
    # If featureTableJSONByteLength is zero, this will also be zero.
    output_file.write(struct.pack('I', 0))
    # batchTableJSONByteLength	uint32	The length of the batch table JSON section in bytes. 
    # Zero indicates that there is no batch table.
    output_file.write(struct.pack('I', 0))
    # batchTableBinaryByteLength	uint32	The length of the batch table binary section in bytes. 
    # If batchTableJSONByteLength is zero, this will also be zero.
    output_file.write(struct.pack('I', 0))
    # polygonIndicesByteLength	uint32	The length of the polygon indices buffer in bytes.
    output_file.write(struct.pack('I', 0))
    # polygonPositionsByteLength	uint32	The length of the polygon positions buffer in bytes.
    output_file.write(struct.pack('I', 0))
    # polylinePositionsByteLength	uint32	The length of the polyline positions buffer in bytes.
    output_file.write(struct.pack('I', 0))
    # pointPositionsByteLength	uint32	The length of the point positions buffer in bytes.
    output_file.write(struct.pack('I', 0))

def writeBody(output_name):  
  region = [0.0, 0.0, 3.1, 3.1, 0.0, 11.0]
  center = [2.05, 2.05, 5.5]
  polygon1 = {
    'properties': { 'name': 'poly1', 'area': 4 },
    'positions': [[1.0, 1.0, 0.0], [2.0, 2.0, 0.0], [3.0, 3.0, 0.0]],
    'indices': [0, 1, 2, 0],
    'minimum_height': 0.0,
    'maximum_height': 0.0
  }  
  polygon2 = {
    'properties': {'name': 'poly2', 'area' : 2},
    'positions': [[1.1, 1.1, 11.0], [2.1, 2.1, 11.0], [3.1, 3.1, 11.0]],
    'indices': [0, 1, 2, 0],
    'minimum_height': 11.0,
    'maximum_height': 11.0
  }
  polygons = [polygon1, polygon2]

  polyline1 = {
    'properties': { 'name': 'line1' },
    'positions': [[1.0, 1.0, 0.0], [2.0, 2.0, 0.0], [3.0, 3.0, 0.0]]
  } 
  polyline2 = {
    'properties': { 'name': 'line2' },
    'positions': [[1.1, 1.1, 11.0], [2.1, 2.1, 11.0], [3.1, 3.1, 11.0]]
  } 
  
  point1 = {
    'properties': { 'name': 'point1' },
    'position': [1.0, 1.0, 0.0]
  } 
  point2 = {
    'properties': { 'name': 'point2', 'suddenAttribute': 'argh' },
    'positions': [1.1, 1.1, 11.0]
  } 

  polylines = [polyline1, polyline2]
  points = [point1, point2]

  json_batch_table = constructBatchTableHeader(polygons, polylines, points)
  batch_binary = constructBatchTableBinary(polygons, polylines, points)

  print('batch table length: ' + str(len(json_batch_table)))
  print('batch table binary length: ' + str(len(batch_binary)))

  json_feature_table = constructFeatureTableHeader(region, center, polygons, polylines, points)
  feature_binary = constructFeatureTableBinary(polygons, polylines, points)

  print('feature table length: ' + str(len(json_feature_table)))
  print('feature table binary length: ' + str(len(feature_binary)))

  print(json_batch_table)
  print(json_feature_table)

def constructFeatureTableHeader(region, center, polygons, polylines, points):
  polygon_counts = []
  polygon_index_counts = []  
  polygon_minimum_heights = []
  polygon_maximum_heights = []
  polygon_batch_ids = []

  for p in polygons:
    polygon_counts.append(len(p['positions']))
    polygon_index_counts.append(len(p['indices']))

    if p['minimum_height']: 
      polygon_minimum_heights.append(p['minimum_height'])
    else:
      polygon_minimum_heights.append(0.0)

    if p['maximum_height']: 
      polygon_maximum_heights.append(p['maximum_height'])
    else:
      polygon_maximum_heights.append(0.0)
      
    if p['batch_id']: 
      polygon_batch_ids.append(p['batch_id'])
    else:
      polygon_batch_ids.append(0)

  polyline_counts = []
  polyline_batch_ids = []

  for p in polylines:
    polyline_counts.append(len(p['positions']))
    
    if p['batch_id']: 
      polyline_batch_ids.append(p['batch_id'])
    else:
      polyline_batch_ids.append(0)

  point_batch_ids = []

  for p in points:    
    if p['batch_id']: 
      point_batch_ids.append(p['batch_id'])
    else:
      point_batch_ids.append(0)


  header = {
    #   'REGION': struct.pack('6f', *region),
    'REGION': region,
    #   'RTC_CENTER': struct.pack('3f', *center),
    'RTC_CENTER': center,
    #   'POLYGONS_LENGTH': struct.pack('I', len(polygons)),
    'POLYGONS_LENGTH': len(polygons),
    #   'POLYLINES_LENGTH': struct.pack('I', len(polylines)),
    'POLYLINES_LENGTH': len(polylines),
    #   'POINTS_LENGTH': struct.pack('I', len(points)),
    'POINTS_LENGTH': len(points),

    # POLYGON_COUNTS	uint32[]	The number of vertices that belong to each polygon. This refers to the polygon 
    # section of the positions buffer in the body. Each polygon count refers to a contiguous number of vertices 
    # in the position buffer that represents the polygon.	
    # ✅ Yes, when the global POLYGONS_LENGTH is greater than zero.
    #   'POLYGON_COUNTS': struct.pack('%sL' % len(polygon_counts), *polygon_counts),
    'POLYGON_COUNTS': polygon_counts,

    # POLYGON_INDEX_COUNTS	uint32[]	The number of indices that belong to each polygon. This refers to the indices 
    # buffer of the body. Each index count refers to a contiguous number of indices that represent the triangulated polygon.	
    # ✅ Yes, when the global POLYGONS_LENGTH is greater than zero.
    #   'POLYGON_INDEX_COUNTS': struct.pack('%sL' % len(polygon_index_counts), *polygon_index_counts),
    'POLYGON_INDEX_COUNTS': polygon_index_counts,

    # POLYGON_MINIMUM_HEIGHTS	float32[]	The minimum height of each polygon in meters above the WGS84 ellipsoid.	
    # 🔴 No. If the minimum height for each polygon is not specified, the global MINIMUM_HEIGHT will be used.
    # #   'POLYGON_MINIMUM_HEIGHTS': struct.pack('%sf' % len(polygon_minimum_heights), *polygon_minimum_heights),    
    'POLYGON_MINIMUM_HEIGHTS': polygon_minimum_heights,

    # POLYGON_MAXIMUM_HEIGHTS	float32[]	The maximum height of each polygon in meters above the WGS84 ellipsoid.	
    # 🔴 No. If the maximum height for each polygon is not specified, the global MAXIMUM_HEIGHT will be used.
    #   'POLYGON_MAXIMUM_HEIGHTS': struct.pack('%sf' % len(polygon_maximum_heights), *polygon_maximum_heights),
    'POLYGON_MAXIMUM_HEIGHTS': polygon_maximum_heights,

    # POLYGON_BATCH_IDS	uint16[]	The batchId of the polygon that can be used to retrieve metadata from the Batch Table.	
    # 🔴 No
    #   'POLYGON_BATCH_IDS': struct.pack('%sI' % len(polygon_batch_ids), *polygon_batch_ids),
    'POLYGON_BATCH_IDS': polygon_batch_ids,

    # POLYLINE_COUNTS	uint32[]	The number of vertices that belong to each polyline. This refers to the polyline section 
    # of the positions buffer in the body. Each polyline count refers to a contiguous number of vertices in the position 
    # buffer that represents the polyline. From the first point on the polyline, each successive point creates a segment 
    # connected to the previous.	
    # ✅ Yes, when the global POLYLINES_LENGTH is greater than zero.
    #   'POLYLINE_COUNTS': struct.pack('%sL' % len(polyline_counts), *polyline_counts),
    'POLYLINE_COUNTS': polyline_counts,

    # POLYLINE_BATCH_IDS	uint16[]	The batchId of the polyline that can be used to retrieve metadata from the Batch Table.	
    # 🔴 No
    #   'POLYLINE_BATCH_IDS': struct.pack('%sI' % len(polyline_batch_ids), *polyline_batch_ids),
    'POLYLINE_BATCH_IDS': polyline_batch_ids,

    # POINT_BATCH_IDS	uint16[]	The batchId of the point that can be used to retrieve metadata from the Batch Table.	
    # 🔴 No
    #   'POINT_BATCH_IDS': struct.pack('%sI' % len(point_batch_ids), *point_batch_ids)
    'POINT_BATCH_IDS': point_batch_ids
  }
  return json.dumps(header)

def constructFeatureTableBinary(polygons, polylines, points):
  stuff = ''
  result = struct.pack('%ss' % len(stuff), stuff.encode('utf-8'))

  return padToByte(result)

def constructBatchTableHeader(polygons, polylines, points):
  batch = {'id' : []}
  i = 0
  
  addBatchedKeys(batch, polygons)
  addBatchedKeys(batch, polylines)
  addBatchedKeys(batch, points)

  i = addBatchedProperties(batch, i, polygons)  
  i = addBatchedProperties(batch, i, polylines)  
  i = addBatchedProperties(batch, i, points)

  return json.dumps(batch)

def constructBatchTableBinary(polygons, polylines, points):
  stuff = ''
  result = struct.pack('%ss' % len(stuff), stuff.encode('utf-8'))

  return padToByte(result)

def addBatchedKeys(batch, propsObjectList):
  for p in propsObjectList:
    if 'properties' in p.keys():      
      for key in p['properties']:        
        if not key in batch:
          batch[key] = []

def addBatchedProperties(batch, i, propsObjectList):
  for p in propsObjectList:
    if 'properties' in p.keys():
      p['batch_id'] = i
      batch['id'].append(i)
      i += 1

      for key in p['properties']:
        batch[key].append(p['properties'][key])
      for key in batch:
        if not key == 'id' and not key in p['properties']:
          batch[key].append(None)
  return i

def padToByte(binary):
  result = ''
  filler = 4 - len(binary) % 4
  extra_spaces = ''
  if not filler == 4:
    for i in range(0, filler):
      extra_spaces = extra_spaces + ' '
  
  result = binary + struct.pack('%ss' % len(extra_spaces), extra_spaces.encode('utf-8'))  
  return result
    
template = {
  'asset': { 'version': '1.0' },
  'geometricError': 500,
  'root': {
    'transform': [
      # 16 numbers comma separated
    ],
    'boundingVolume': {
      'box': [
        # 16 numbers comma separated
      ]
    },
    'geometricError': 100,
    'refine': 'REPLACE',
    'content': {
      'url': ''
    },
    'children': [
      {
        'boundingVolume': {
          'box': [
            # 16 numbers comma separated
          ]
        },
        'geometricError': 10,
        'content': {
          'url': ''
        },
        'children': [
          {
            'boundingVolume': {
              'box': [
                # 16 numbers comma separated
              ]
            },
            'geometricError': 0,
            'content': {
              'url': ''
            }
          }
        ]
      }
    ]
  }
}

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
    if (False):
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
    # parser.add_argument('-l','--lods', type=int, default=11)
    # parser.add_argument('-o','--output_dir', type=is_dir, help='The output directory', default='.')
    # parser.add_argument('files', type=argparse.FileType('r'), nargs='+', help='One or more geojson files')
    args = parser.parse_args()

    # with open('output.vct', 'wb') as output_file: 
    # writeHeader('output.vct')         
    writeBody('output.vct')

    main(args)
    