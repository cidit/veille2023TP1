import os
import sys


class Config:
    def __init__(self) -> None:
        self.db_path = os.getenv("DB_PATH", "data/db.sqlite")
        self.validate = "--validate" in sys.argv
        self.reset_db = "--reset_db" in sys.argv
        