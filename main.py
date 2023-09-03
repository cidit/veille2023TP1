import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import sqlite3


def simple_plot():
    x = np.linspace(0, 2 * np.pi, 200)
    y = np.sin(x)

    fig, ax = plt.subplots()
    ax.plot(x, y)
    plt.show()


if __name__ == "__main__":
    print("Hello, World!")

    matrix = np.random.rand(100, 100)
    
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    static_hm = ax.imshow(matrix, cmap="Wistia", alpha=0.25)
    dynamic_hm = ax.imshow(matrix, zorder=1, cmap="magma_r", alpha=0.25)
    
    def init():
        # ax.set_xlim(0, 2*np.pi)
        # ax.set_ylim(-1, 1)
        return dynamic_hm,

    def update(frame):
        new_matrix = np.random.rand(100, 100)
        dynamic_hm.set_data(new_matrix)
        return dynamic_hm,

    ani = FuncAnimation(fig, update, frames=None,
                        init_func=init, blit=True)
    plt.show()