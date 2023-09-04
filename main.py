import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import sqlite3


if __name__ == "__main__":
    print("Hello, World!")

    matrix = np.random.rand(100, 100)
    zeros = np.zeros((100, 100), dtype=int)
    print(zeros)
    print(matrix)
    
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    # static_hm = ax.imshow(matrix, cmap="Wistia", alpha=0.25)
    dynamic_hm = ax.imshow(zeros, zorder=1, alpha=0.25, vmin=0, vmax=1)
    
    
    def update(frame):
        new_matrix = np.random.rand(100, 100) 
        dynamic_hm.set_data(new_matrix)
        return (dynamic_hm),

    # reference to `ani` must be kept alive because it needs to maintain an internal timer that's gonna get garbage collected otherwise.
    ani = FuncAnimation(fig, update,  
                        frames=None,
                        blit=True, 
                        cache_frame_data=False)
    
    plt.show()