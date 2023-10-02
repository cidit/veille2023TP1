import os
import pickle
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation # type: ignore 
import numpy as np
import dotenv
from result import Ok, Err, Result
from collections import deque

import typer

from gtfs_realtime_pb2 import FeedMessage
from config import Config
from db import sqlite_numpy_bridge, DB
from model import Bounds, BusData
from processing import clean_data, interpret 
from render import add_dyn_heatmap, create_custom_color_map, draw_map
from stm_api import Get


def main(reset_db: bool = True, 
         validate_statics: bool = True, 
         db_path: str = os.getenv("DB_PATH", "data/db.sqlite")
         ):
    
    position_queue = deque(maxlen=30)
    db = DB(db_path, reset_db=reset_db)
    fig, ax = plt.subplots()
    statics = Get.static_GTFS(validate=validate_statics)

    bounds = Bounds.from_shapes(statics.shapes)
    hm_shape = Bounds(0, 
                      100, # width
                      0, 
                      100 # height
                      )
    
    draw_map(ax, statics)
    cmap = create_custom_color_map()
    dynamic_hm = add_dyn_heatmap(ax,
                                 hm_shape=hm_shape,
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
                return dynamic_hm,
        
        pos = clean_data(msg)
        
        if len(position_queue) == position_queue.maxlen:
            position_queue.pop()
        position_queue.append(pos)
        db.save(pickle.dumps(pos))
        
        interpreted = interpret(position_queue, bounds, hm_shape)
        print("\trotating dataset")
        new_matrix = np.rot90(interpreted, 1)
        
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
    
    
    # reset the DHM
    dynamic_hm.set_data(np.zeros((hm_shape.maxx, hm_shape.maxy))) 
    
    bus_data = (pickle.loads(data) for data in db.read_from_oldest())
    
    # reset positions queue
    position_queue = deque(maxlen=30)
    
    def transform(bd: list[BusData]):
        if len(position_queue) == position_queue.maxlen:
            position_queue.pop()
        position_queue.append(bd)
        return interpret(position_queue, bounds=bounds, out_shape=hm_shape)
    
    frames = (transform(bd) for bd in bus_data)
    
    def update(frame):
        new_matrix = np.rot90(frame, 1)
        dynamic_hm.set_data(new_matrix)
        return dynamic_hm,
    
    ani = FuncAnimation(fig, frames=frames, func=update, cache_frame_data=False)
    ani.save("data/anim.gif", writer="ffmpeg", fps=30)


if __name__ == "__main__":
    print("Hello, World!")
    dotenv.load_dotenv()
    sqlite_numpy_bridge()
    typer.run(main) 
