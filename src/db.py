
import sqlite3
import numpy as np


class DB:
    def __init__(self, db_path: str, reset_db: bool):
        self.conn = sqlite3.connect(db_path)
        self.table_name = "vehicle_pos_snapshots"
        cur = self.conn.cursor()
        if reset_db:
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
 