import gtfs_kit as gk # type: ignore
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mp # type: ignore 
from matplotlib.patches import PathPatch # type: ignore 
from matplotlib.animation import FuncAnimation # type: ignore 
import numpy as np
import dotenv
from result import Ok, Err, Result
from collections import deque

from gtfs_realtime_pb2 import FeedMessage
from config import Config
from db import sqlite_numpy_bridge, DB
from model import Bounds, BusData
from processing import clean_data, interpret, parse_shape_instructions
from stm_api import Get


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

    bounds = Bounds.from_shapes(statics.shapes)
    
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




if __name__ == "__main__":
    main()
