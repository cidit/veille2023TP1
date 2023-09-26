from matplotlib import axes, path as mp, pyplot as plt, colors
from matplotlib.patches import PathPatch # type: ignore
from gtfs_kit import Feed # type: ignore
import numpy as np

from model import Bounds
from processing import parse_shape_instructions


def draw_map(ax: axes.Axes, statics: Feed):
    instructions = parse_shape_instructions(statics)
    # the following is pretty much a copy paste of https://matplotlib.org/stable/gallery/shapes_and_collections/path_patch.html#sphx-glr-gallery-shapes-and-collections-path-patch-py
    codes, verts = zip(*instructions)
    path = mp.Path(verts, codes)
    patch = PathPatch(path,
                      facecolor="none",
                      zorder=0,
                      lw=0.5)
    patchmap = ax.add_patch(patch) # type: ignore
    x, y = zip(*path.vertices)
    line, = ax.plot(x, y, 'g-', marker=None) # type: ignore
    line.remove()
    
    
def create_custom_color_map():
    # the following color map bit is taken from https://stackoverflow.com/questions/37327308/add-alpha-to-an-existing-colormap
    cmap = plt.get_cmap("autumn_r")
    my_cmap = cmap(np.arange(cmap.N))
    my_cmap[:,-1] = np.linspace(0, 1, cmap.N) 
    my_cmap = colors.ListedColormap(my_cmap)
    return my_cmap
    
    
def add_dyn_heatmap(ax: axes.Axes, hm_shape: Bounds, data_bounds: Bounds, cmap: colors.ListedColormap):
    ax.imshow(np.zeros((hm_shape.maxx, hm_shape.maxy)), # type: ignore 
              zorder=1,
              alpha=1,
              extent=[
                  data_bounds.minx,
                  data_bounds.maxx,
                  data_bounds.miny,
                  data_bounds.maxy,
              ],
              interpolation="spline16",
              cmap=cmap,
              vmin=0, vmax=5
              )
    
