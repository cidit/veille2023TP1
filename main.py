import pathlib
from dataclasses import dataclass
import gtfs_realtime_pb2
import os
import requests
import sys
import gtfs_kit as gk
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mp
from matplotlib.patches import PathPatch
from matplotlib.animation import FuncAnimation
import numpy as np
import sqlite3
import dotenv

MATRIX_WIDTH = 150
MATRIX_HEIGHT = 150


def main():
    print("Hello, World!")
    dotenv.load_dotenv()
    
    fig, ax = plt.subplots()
    statics = Get.static_data()

    shps = statics.shapes
    bounds = Bounds(shps)
    
    cmap = plt.get_cmap("Reds")
    cmap.set_under("00000000")
    norm = mpl.colors.Normalize(vmin=1, vmax=5, clip=False)
    
    cdict = {
        "blue": ((0,1,1), (1, 1, 1)),
        "red": ((0,0,0), (1, 0, 0)),
        "green": ((0,0,0), (1, 0, 0)),
        "alpha": ((0, 0,0), (1,1,1)),
    }
    plt.register_cmap(cmap=mpl.colors.LinearSegmentedColormap("MyCMAP", cdict))
    dynamic_hm = ax.imshow(np.zeros((MATRIX_WIDTH, MATRIX_HEIGHT)),
                           zorder=1,
                           alpha=0.75,
                           extent=[
                                shps['shape_pt_lon'].min(),
                                shps['shape_pt_lon'].max(),
                                shps['shape_pt_lat'].min(),
                                shps['shape_pt_lat'].max(),
                            ],
                            interpolation="spline16",
                            cmap="MyCMAP")
    
    
    instructions = parse_shape_instructions(statics)
    # the following is pretty much a copy paste of https://matplotlib.org/stable/gallery/shapes_and_collections/path_patch.html#sphx-glr-gallery-shapes-and-collections-path-patch-py
    codes, verts = zip(*instructions)
    path = mp.Path(verts, codes)
    patch = PathPatch(path,
                      facecolor="none",
                      lw=1)
    patchmap = ax.add_patch(patch)
    x, y = zip(*path.vertices)
    line, = ax.plot(x, y, 'g-', marker=None)
    line.remove()

    
    
    def update(frame):
        new_matrix = np.zeros((MATRIX_WIDTH,MATRIX_HEIGHT))        
        positions = Get.dynamic_data()
        positions = translate_coords(positions, bounds)
        # print(list(positions))
        for (x, y) in positions:
            new_matrix[int(x)][int(y)] += 1
        # new_matrix = np.flip(new_matrix, 1)
        new_matrix = np.rot90(new_matrix, 1)
        dynamic_hm.set_data(new_matrix)
        return dynamic_hm,
    

    # reference to `ani` must be kept alive because it needs to maintain an internal timer that's gonna get garbage collected otherwise.
    ani = FuncAnimation(fig, update,  
                        frames=None,
                        blit=True, 
                        interval=10_000, # once every 10s
                        cache_frame_data=False)

    plt.show()

class Get:
    def static_data():
        """gets the static GTFS data and prints any validation warning.
        crashes the program in the event of any errors reported in the validation.

        Returns:
            _type_: _description_
        """
        p = pathlib.Path("./data/gtfs.zip")
        print(f"reading GTFS feed at {p}")
        feed = gk.read_feed(p, dist_units='km')
        if "--validate" in sys.argv:
            print("validating feed")
            v = feed.validate(as_df=True, include_warnings=True)
            print(f"GTFS Warnings and Errors:\n{v}")
            any_err = len(v.loc[v['type'] == 'error']) > 0
            if any_err:
                sys.exit(1)
         
        return feed
        
    def dynamic_data():
        dyndat_url = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
        response = requests.get(dyndat_url, headers={
            "accept": "application/x-protobuf",
            "apiKey": os.getenv("API_KEY")
        })
        msg = gtfs_realtime_pb2.FeedMessage()
        msg.ParseFromString(response.content)
        pos = map(lambda e: e.vehicle.position, msg.entity)
        pos = map(lambda p: (p.longitude, p.latitude), pos)
        return pos
        

class DB:
    def __init__(self, conn):
        self.conn = conn
        
    def save_changes(changes):
        pass


class Bounds:
    def __init__(self, shps) -> None:
        self.minx = shps['shape_pt_lon'].min()
        self.maxx = shps['shape_pt_lon'].max()
        self.miny = shps['shape_pt_lat'].min()
        self.maxy = shps['shape_pt_lat'].max()
        
    def __str__(self) -> str:
        return f"""
minx={self.minx}
maxx={self.maxx}
miny={self.miny}
maxy={self.maxy}
        """
        
def translate_coords(coords, bounds: Bounds):
    b = bounds
        
    newcoords = []
    for x, y in coords:
        nx = np.interp(x, 
                       np.linspace(b.minx, b.maxx, MATRIX_WIDTH),
                       np.linspace(0, MATRIX_WIDTH, MATRIX_WIDTH, endpoint=False), 
                       )
        ny = np.interp(y, 
                       np.linspace(b.miny, b.maxy, MATRIX_HEIGHT),
                       np.linspace(0, MATRIX_HEIGHT, MATRIX_HEIGHT, endpoint=False), 
                       )
        print(nx, ny)
        newcoords.append((nx, ny))
    return newcoords
 
def parse_shape_instructions(f: gk.Feed):
    instructions = []
    for name, group in f.shapes.sort_values('shape_pt_sequence').groupby('shape_id'):
        coords = iter(zip(group['shape_pt_lon'], group['shape_pt_lat']))
        start = next(coords)
        instructions.append((mp.Path.MOVETO, start))
        for coord in coords:
            instructions.append((mp.Path.LINETO, coord))
    return instructions
    
    

if __name__ == "__main__":
    main()
