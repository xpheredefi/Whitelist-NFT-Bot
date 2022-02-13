"""
This file migrates the old json-format of backend data to the new sqlite format.

This is to not lose old data and maintain consistency in the DB
"""

from ..db import DB
import json

NEW_DB_NAME = "new_data.db"
OLD_JSON_FILE = "data.json"

db = DB(NEW_DB_NAME)
with open(OLD_JSON_FILE, 'r') as in_file:
    old_data = json.load(in_file)
for server in old_data:
    channel = old_data[server]["whitelist_channel"]
    role = old_data[server]["whitelist_role"]
    db.execute("INSERT INTO discord_server VALUES (?,?,?,?)", 
        (int(server), None if channel is None else int(channel) , None if role is None else int(role), old_data[server]["blockchain"]))
    for user in old_data[server]['data']:
        db.execute("INSERT INTO user VALUES (?,?,?)", (int(user), int(server), old_data[server]['data'][user]))
    db.commit()
db.close()