import gtfs_kit as gk # type: ignore
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation # type: ignore 
import numpy as np
import dotenv
from result import Ok, Err, Result
from collections import deque

from gtfs_realtime_pb2 import FeedMessage
from config import Config
from db import sqlite_numpy_bridge, DB
from model import Bounds, BusData
from processing import clean_data, interpret 
from render import add_dyn_heatmap, create_custom_color_map, draw_map
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
    
    draw_map(ax, statics)
    cmap=create_custom_color_map()
    dynamic_hm = add_dyn_heatmap(ax,
                                 hm_shape=Bounds(0, MATRIX_WIDTH, 0, MATRIX_HEIGHT),
                                 data_bounds=bounds,
                                 cmap=cmap)  
        
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
