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

    matrix = np.array([[0.8, 2.4, 2.5, 3.9, 0.0, 4.0, 0.0],
                    [2.4, 0.0, 4.0, 1.0, 2.7, 0.0, 0.0],
                    [1.1, 2.4, 0.8, 4.3, 1.9, 4.4, 0.0],
                    [0.6, 0.0, 0.3, 0.0, 3.1, 0.0, 0.0],
                    [0.7, 1.7, 0.6, 2.6, 2.2, 6.2, 0.0],
                    [1.3, 1.2, 0.0, 0.0, 0.0, 3.2, 5.1],
                    [0.1, 2.0, 0.0, 1.4, 0.0, 1.9, 6.3]])
    
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    static_hm = ax.imshow(matrix)
    dynamic_hm = ax.imshow(matrix, zorder=1)
    
    def init():
        # ax.set_xlim(0, 2*np.pi)
        # ax.set_ylim(-1, 1)
        return dynamic_hm,

    def update(frame):
        new_matrix = np.random.rand(7, 7)
        dynamic_hm.set_data(new_matrix)
        return dynamic_hm,

    ani = FuncAnimation(fig, update, frames=None,
                        init_func=init, blit=True)
    plt.show()