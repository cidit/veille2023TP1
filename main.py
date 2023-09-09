import pathlib
import pandas
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
from result import Ok, Err, Result
import queue

MATRIX_WIDTH = 100
MATRIX_HEIGHT = 100


def main():
    print("Hello, World!")
    dotenv.load_dotenv()
    sqlite_numpy_bridge()
    
    position_queue = queue.Queue(30)
    
    db = DB(sqlite3.connect(os.getenv("DB_PATH")))
    fig, ax = plt.subplots()
    statics = Get.static_GTFS()

    shps = statics.shapes
    bounds = Bounds(shps)
    
    # the following color map bit is taken from https://stackoverflow.com/questions/37327308/add-alpha-to-an-existing-colormap
    cmap = plt.get_cmap("autumn_r")
    my_cmap = cmap(np.arange(cmap.N))
    my_cmap[:,-1] = np.linspace(0, 1, cmap.N) 
    my_cmap = mpl.colors.ListedColormap(my_cmap)
    
    dynamic_hm = ax.imshow(np.zeros((MATRIX_WIDTH, MATRIX_HEIGHT)),
                            zorder=1,
                            alpha=1,
                            extent=[
                                shps['shape_pt_lon'].min(),
                                shps['shape_pt_lon'].max(),
                                shps['shape_pt_lat'].min(),
                                shps['shape_pt_lat'].max(),
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
        new_matrix = np.zeros((MATRIX_WIDTH,MATRIX_HEIGHT)) 
        print("\tfetching and parsing data")
        msg = Get.realtime_feed()
        match msg:
            case Ok(v):
                msg = v
            case Err(e):
                print("An error happened while fetching the dynamic date. returning early of the update function...")
                print(e)
                return dynamic_hm
        pos = map(lambda e: e.vehicle.position, msg.entity)
        pos = map(lambda p: (p.longitude, p.latitude), pos)
        print("\ttranslating coordinates")
        positions = translate_coords(pos, bounds)
        print(f"\tcumulating {len(positions)} coordinates")
        for (x, y) in positions:
            new_matrix[int(x)][int(y)] += 1
        print("\trotating dataset")
        new_matrix = np.rot90(new_matrix, 1)
        print("\tsaving data")
        db.save(new_matrix)
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
    
def sqlite_numpy_bridge():
    # this entire function is lifted from https://stackoverflow.com/questions/18621513/python-insert-numpy-array-into-sqlite3-database
    import io
    
    def adapt_array(arr):
        """
        http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
        """
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)
        return sqlite3.Binary(out.read())
    
    def convert_array(text):
        out = io.BytesIO(text)
        out.seek(0)
        return np.load(out)
    # Converts np.array to TEXT when inserting
    sqlite3.register_adapter(np.ndarray, adapt_array)

    # Converts TEXT to np.array when selecting
    sqlite3.register_converter("array", convert_array)

class Get:
    def static_GTFS():
        """gets the static GTFS data and prints any validation warning.
        crashes the program in the event of any errors reported in the validation.
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
        
    def realtime_feed():
        dyndat_url = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
        try:
            response = requests.get(dyndat_url, headers={
                "accept": "application/x-protobuf",
                "apiKey": os.getenv("API_KEY")
            })
            msg = gtfs_realtime_pb2.FeedMessage()
            msg.ParseFromString(response.content)
            
            return Ok(msg)
        except Exception as err:
            return Err(err)
        
class DB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.table_name = "vehicle_pos_snapshots"
        cur = self.conn.cursor()
        if "--reset_db" in sys.argv:
            cur.execute(f"DROP TABLE IF EXISTS {self.table_name};")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                data ARRAY NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
            """
        )
        
    def save(self, vpos: np.ndarray):
        self.conn.cursor().execute(
            f"""
            INSERT INTO {self.table_name} (data) values (?); 
            """,
            (vpos, ))
        self.conn.commit()
        
    def read_from_oldest(self):
        """returns a generator that will get the data in the db sequentially, from oldest to newest
        """
        cur = self.conn.cursor()
        cur.execute(
            f"""
            SELECT data 
            FROM {self.table_name} 
            ORDER BY time ASC;
            """
        ) 
        # we map to the first element of the tupple for each entry of the returned data
        generator = (entry[0] for entry in cur)
        return generator

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
        newcoords.append((nx, ny))
    return newcoords

def interpret(data: queue.Queue[pandas.DataFrame], bounds: Bounds):
    """
    takes a queue of the cached data frames.
    each dataframe contains 3 fields:
    - vehicle id
    - longitude
    - latitude
    
    the output of this functions is a 2D numpy matrix of ints that can be fed directly to the heatmap.
    """
    
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
