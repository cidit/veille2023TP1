    
from dataclasses import dataclass

from pandas import DataFrame


@dataclass
class Bounds:
    minx: float
    maxx: float
    miny: float
    maxy: float
    
    @staticmethod
    def from_shapes(shps: DataFrame):
        minx = shps['shape_pt_lon'].min()
        maxx = shps['shape_pt_lon'].max()
        miny = shps['shape_pt_lat'].min()
        maxy = shps['shape_pt_lat'].max()
        
        return Bounds(minx=minx, maxx=maxx, miny=miny, maxy=maxy)
        
    def __str__(self) -> str:
        return f"""
minx={self.minx}
maxx={self.maxx}
miny={self.miny}
maxy={self.maxy}
        """
        
@dataclass
class BusData:
    id: int
    lon: float
    lat: float

