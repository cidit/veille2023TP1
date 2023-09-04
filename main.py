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
    zeros = np.zeros((100, 100))
    
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    # static_hm = ax.imshow(matrix, cmap="Wistia", alpha=0.25)
    dynamic_hm = ax.imshow(zeros, zorder=1, alpha=0.25)
    
    def init():
        return (dynamic_hm)
    
    def update(frame):
        new_matrix = np.random.rand(100, 100)
        print(new_matrix[0:1])
        dynamic_hm.set_data(new_matrix)
        return (dynamic_hm),

    # reference to `ani` must be kept alive because it needs to maintain an internal timer that's gonna get garbage collected otherwise.
    ani = FuncAnimation(fig, func=update, 
                        init_func=init, 
                        frames=None,
                        blit=True, interval=50)
    
    plt.show()