import os
import pathlib
import sys
import gtfs_kit as gk
import requests
from result import Err, Ok

from src.gtfs_realtime_pb2 import FeedMessage

class Get:
    def static_GTFS(validate: bool):
        """gets the static GTFS data and prints any validation warning.
        crashes the program in the event of any errors reported in the validation.
        """
        p = pathlib.Path("./data/gtfs.zip")
        print(f"reading GTFS feed at {p}")
        feed = gk.read_feed(p, dist_units='km')
        if validate:
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
            msg = FeedMessage()
            msg.ParseFromString(response.content)
            
            return Ok(msg)
        except Exception as err:
            return Err(err)
        