import sqlite3

class DB(sqlite3.Connection):
    def __init__(self, db_location):
        try:
            super(DB, self).__init__(f"file:{db_location}?mode=rw", uri=True, detect_types=sqlite3.PARSE_DECLTYPES)
            self.execute("PRAGMA foreign_keys = ON")
        except sqlite3.OperationalError:
            print("DB file does not exist, initalising new DB.")
            super(DB, self).__init__(db_location, detect_types=sqlite3.PARSE_DECLTYPES)
            self.execute("PRAGMA foreign_keys = ON")
            with open("schema.sql", "r") as schema:
                self.executescript(schema.read())
                self.commit()
        
        self.row_factory = sqlite3.Row
