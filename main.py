import pathlib
import sys
import gtfs_kit as gk
import matplotlib.pyplot as plt
import matplotlib.path as mp
from matplotlib.animation import FuncAnimation
import numpy as np
import sqlite3


def main():
    print("Hello, World!")

    statics = Get.static_data()
    
    instructions = []
    for name, group in statics.shapes.sort_values('shape_pt_sequence').groupby('shape_id'):
        coords = iter(zip(group['shape_pt_lat'], group['shape_pt_lon']))
        start = next(coords)
        instructions.append((mp.Path.MOVETO, start))
        for coord in coords:
            instructions.append((mp.Path.LINETO, coord))
        instructions.append((mp.Path.CLOSEPOLY, start))
    print(instructions)
    
    
    fig, ax = plt.subplots()
    # static_hm = ax.imshow(matrix, cmap="Wistia", alpha=0.25)
    dynamic_hm = ax.imshow(np.zeros((100, 100)),
                           zorder=1,
                        #    alpha=0.25,
                           cmap="Blues",
                           vmin=0,
                           vmax=1)
    
    
    def update(frame):
        new_matrix = np.random.rand(100, 100) 
        # dynamic_hm.set_data(new_matrix)
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
        else: 
            return feed
        
    def dynamic_data():
        pass

if __name__ == "__main__":
    main()
