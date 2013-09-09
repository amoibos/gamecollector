#!/usr/bin/env python
#encoding:UTF-8

# A minimal SQLite shell for experiments

import sys
import sqlite3


if sys.version_info[0] >= 3:
   raw_input = input

db_name = sys.argv[1] if len(sys.argv) > 1 else "collection.db"
if os.path.exists(db_name):
    con = sqlite3.connect(db_name)
    cursor = con.cursor()

    while True:
        command = raw_input("> ")
        if not command:
            continue
        if command == "exit":
            break
        try:
            answer = list(cursor.execute(command))
            print(answer)
        except sqlite3.OperationalError, err:
            print("error")
    con.close()
else:
    print("database %s not found" % db_name)

