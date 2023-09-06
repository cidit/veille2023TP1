import pathlib
import gtfs_realtime_pb2
import os
import requests
import sys
import gtfs_kit as gk
import matplotlib.pyplot as plt
import matplotlib.path as mp
from matplotlib.patches import PathPatch
from matplotlib.animation import FuncAnimation
import numpy as np
import sqlite3
import dotenv


def main():
    print("Hello, World!")
    dotenv.load_dotenv()

    statics = Get.static_data()
    
    shps = statics.shapes
    
    fig, ax = plt.subplots()
    # static_hm = ax.imshow(matrix, cmap="Wistia", alpha=0.25)
    dynamic_hm = ax.imshow(np.zeros((1000, 1000)),
                           zorder=1,
                           alpha=0.25,
                           extent=[
                                shps['shape_pt_lon'].min(),
                                shps['shape_pt_lon'].max(),
                                shps['shape_pt_lat'].min(),
                                shps['shape_pt_lat'].max(),
                            ],
                            interpolation="spline16",
                           cmap="Blues",
                           vmin=0,
                           vmax=1)
    
    
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
        new_matrix = np.random.rand(1000, 1000) 
        dynamic_hm.set_data(new_matrix)
        return dynamic_hm,
    

    # reference to `ani` must be kept alive because it needs to maintain an internal timer that's gonna get garbage collected otherwise.
    ani = FuncAnimation(fig, update,  
                        frames=None,
                        blit=True, 
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
        dyndat_url = "https://api.stm.info/pub/od/gtfs-rt/ic/v2"
        payload = requests.get(dyndat_url, headers={
            "accept": "application/x-protobuf",
            "apiKey": os.getenv("API_KEY")
        })
        

class DB:
    def __init__(self, conn):
        self.conn = conn
        
    def save_changes(changes):
        pass
    
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
