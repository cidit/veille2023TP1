import gtfs_kit as gk
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mp
from matplotlib.patches import PathPatch
from matplotlib.animation import FuncAnimation
import numpy as np
import dotenv
from result import Ok, Err, Result
from collections import deque

from src.gtfs_realtime_pb2 import FeedMessage
from src.config import Config
from src.db import sqlite_numpy_bridge, DB
from src.model import Bounds, BusData
from src.stm_api import Get


MATRIX_WIDTH = 100
MATRIX_HEIGHT = 100


def main():
    print("Hello, World!")
    dotenv.load_dotenv()
    sqlite_numpy_bridge()
    
    config = Config()
    position_queue = deque(maxlen=30)
        
    db = DB(config.db_path, reset_db=config.reset_db)
    fig, ax = plt.subplots()
    statics = Get.static_GTFS(config.validate)

    bounds = Bounds(statics.shps)
    
    # the following color map bit is taken from https://stackoverflow.com/questions/37327308/add-alpha-to-an-existing-colormap
    cmap = plt.get_cmap("autumn_r")
    my_cmap = cmap(np.arange(cmap.N))
    my_cmap[:,-1] = np.linspace(0, 1, cmap.N) 
    my_cmap = mpl.colors.ListedColormap(my_cmap)
    
    dynamic_hm = ax.imshow(np.zeros((MATRIX_WIDTH, MATRIX_HEIGHT)),
                            zorder=1,
                            alpha=1,
                            extent=[
                                bounds.minx,
                                bounds.maxx,
                                bounds.miny,
                                bounds.maxy,
                            ],
                            interpolation="spline16",
                            cmap=my_cmap,
                            vmin=0, vmax=5
                            )
    
    
    instructions = parse_shape_instructions(statics)
    # the following is pretty much a copy paste of https://matplotlib.org/stable/gallery/shapes_and_collections/path_patch.html#sphx-glr-gallery-shapes-and-collections-path-patch-py
    codes, verts = zip(*instructions)
    path = mp.Path(verts, codes)
    patch = PathPatch(path,
                      facecolor="none",
                      zorder=0,
                      lw=0.5)
    patchmap = ax.add_patch(patch)
    x, y = zip(*path.vertices)
    line, = ax.plot(x, y, 'g-', marker=None)
    line.remove()
    
    
    def update(_frame):
        print("updating...")
        print("\tfetching and parsing data")
        msg = Get.realtime_feed()
        match msg:
            case Ok(v):
                msg = v
            case Err(e):
                print("An error happened while fetching the dynamic date. returning early of the update function...")
                print(e)
                return dynamic_hm
        print("\tcleaning data")
        pos = list(clean_data(msg))
        print("\ttranslating coordinates")
        if len(position_queue) == position_queue.maxlen:
            position_queue.pop()
        position_queue.append(pos)
        interpreted = interpret(position_queue, bounds, (MATRIX_WIDTH, MATRIX_HEIGHT))
        print("\trotating dataset")
        new_matrix = np.rot90(interpreted, 1)
        print("\tsaving data")
        # db.save(new_matrix) gonna have to start saving the list of coords instead
        print("update finished")
        dynamic_hm.set_data(new_matrix)
        return dynamic_hm,

    # reference to `ani` must be kept alive because it needs to maintain an internal timer that's gonna get garbage collected otherwise.
    ani = FuncAnimation(fig, update,  
                        frames=None,
                        blit=True, 
                        interval=10_000, # once every 10s
                        cache_frame_data=False)

    plt.show()


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
        newcoords.append((nx, ny))
    return newcoords

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

def interpret(data: deque[list[tuple[int, float, float]]], bounds: Bounds, out_shape):
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
    (width, height) = out_shape
    out = [ [ set() for i in range(height) ] for j in range(width) ]
    for frame in data:
        for (id, lon, lat) in frame:
            nx = np.interp(lon, 
                        np.linspace(b.minx, b.maxx, MATRIX_WIDTH),
                        np.linspace(0, MATRIX_WIDTH, MATRIX_WIDTH, endpoint=False), 
                        )
            ny = np.interp(lat, 
                        np.linspace(b.miny, b.maxy, MATRIX_HEIGHT),
                        np.linspace(0, MATRIX_HEIGHT, MATRIX_HEIGHT, endpoint=False), 
                        )
            out[int(nx)][int(ny)].add(id)
    out = map(lambda l: map(lambda s: s.count(), l), out)
    return np.array(out)
 
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
