
from collections import deque

import numpy as np
from gtfs_realtime_pb2 import FeedMessage
import gtfs_kit as gk # type: ignore
import matplotlib.path as mp # type: ignore

from model import Bounds, BusData


# TODO: make out_shape a Bounds
def interpret(data: deque[list[tuple[int, float, float]]], bounds: Bounds, out_shape: Bounds):
    """
    METRIC OF QUALITY
    takes a queue of the cached data frames.
    each dataframe contains 3 fields that we are interested in:
    - vehicle id
    - longitude
    - latitude
    
    the output of this functions is a 2D numpy array of ints that can be fed directly to the heatmap.
    """
    b = bounds
    (width, height) = (int(out_shape.maxx), int(out_shape.maxy))
    out: list[list[set]]= [ [ set() for i in range(height) ] for j in range(width) ]
    for frame in data:
        for (id, lon, lat) in frame:
            nx = np.interp(lon, 
                        np.linspace(b.minx, b.maxx, width),
                        np.linspace(0, width, width, endpoint=False), 
                        )
            ny = np.interp(lat, 
                        np.linspace(b.miny, b.maxy, height),
                        np.linspace(0, height, height, endpoint=False), 
                        )
            out[int(nx)][int(ny)].add(id)
    return np.array(map(lambda l: map(lambda s: len(s), l), out))
 

def clean_data(raw: FeedMessage):
    """cleans the feed message, keeping and grouping only the information we need

    Args:
        raw (gtfs_realtime_pb2.FeedMessage)

    Returns:
        a list of BusData
    """
    return [
        BusData(
            id=int(e.vehicle.vehicle.id),
            lon=float(e.vehicle.position.longitude),
            lat=float(e.vehicle.position.latitude),   
        )
        for e 
        in raw.entity
    ]

def parse_shape_instructions(f: gk.Feed):
    instructions = []
    for name, group in f.shapes.sort_values('shape_pt_sequence').groupby('shape_id'):
        coords = iter(zip(group['shape_pt_lon'], group['shape_pt_lat']))
        start = next(coords)
        instructions.append((mp.Path.MOVETO, start))
        for coord in coords:
            instructions.append((mp.Path.LINETO, coord))
    return instructions

