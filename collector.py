#!/usr/bin/env python

import os
import sys
import sqlite3
import csv


__author__ = "Daniel Oelschlegel"
__license__ = "new bsdl"
__copyright__ = "2013"
__version__ = "0.01"


TABLE_FORMAT_QUESTIONS = ("title[NOT EMPTY]",  "box[YES]", "manual[YES]", "cartridge[YES]", 
                        "region[PAL]", "price[5]", "condition[2]", "special['']", "comment['']")
YES, NO = ("y", "yes"), ("n", "no")

#sql injection friendly ;)

def db_init(db_name):
    connection = sqlite3.connect(db_name)
    connection.text_factory = str
    cursor = connection.cursor()
    try:
        cursor.execute("select * from collection")
    except sqlite3.OperationalError:
        ret = cursor.execute("""create table collection(
                        title primary key, box, manual, cartridge, region, 
                        price, condition, special, comment)""")
    return connection, cursor

def export(cursor, db_name):
    answers = ""
    if db_name:
        with open(db_name, 'w') as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(cursor.execute("select * from collection"))
            answers = "exported to %s" % db_name
    else:
        answers = "file name missing"
    return answers

def _import(cursor, db_name):
    conflicts = 0
    answers = ""
    if os.path.exists(db_name):
        db_name = db_name.lower()
        if not db_name.endswith(".csv"):
            db_name = "%s.csv" % db_name
        with open(db_name) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                try:
                    raw_insert(cursor, row)
                    answers += "%s added to database\n" % row[0]
                except sqlite3.IntegrityError:
                    answers += "%s already in database\n" % row[0]
                    conflicts += 1
        answers += "%d conflicts\n" % conflicts
    else:
        answers = "file name not found"
    return answers

def raw_insert(cursor, values):
    answers = ""
    try:
        cursor.execute("insert into collection values (?,?,?,?,?,?,?,?,?)", values)
    except sqlite3.OperationalError:
        return "nothing inserted"
    answers = "rows inserted"
    return answers

def insert(cursor):
    answer = []
    for column_identifier in TABLE_FORMAT_QUESTIONS:
        while True:
            answer.append(raw_input("%s: " % column_identifier))
            if not answer[-1] and "title" in column_identifier:
                answer.pop(-1)
                continue
            #boolean types: box, cartridge, manual
            elif "YES" in column_identifier:
                if not answer[-1] or answer[-1] not in YES + NO:
                    answer[-1] = "true"
                elif answer[-1].lower() in YES:
                    answer[-1] = "true"
                elif answer[-1].lower() in NO:
                    answer[-1] = "false"
            elif (not answer[-1] or answer not in ("PAL", "USA", "BRA", "JAP", "KOR")) and "region" in column_identifier:
                answer[-1] = "PAL"
            elif "condition" in column_identifier and (not answer[-1] or not 1 <= int(answer[-1]) <= 6):
               answer[-1] = 2
            elif "price" in column_identifier and not answer[-1]:
                answer[-1] = 5
            break

    return "one row added" if not raw_insert(cursor, answer).startswith("nothing") else "error, maybe locked"
    
def _update(cursor, query):
    try:
        cursor.execute(query)
    except sqlite3.OperationalError:
        return ""
    return "row updated"
    
def update(cursor, where):
    attributes = []
    answers = ""
    try:
        rows = list(cursor.execute("select * from collection where %s" % where))
    except sqlite3.OperationalError:
        return "nothing to update"
    rows_count = len(rows)
    print rows_count, "to update"
    for row in rows:
        for index, column_identifier in enumerate(TABLE_FORMAT_QUESTIONS):
            title = column_identifier.split('[')[0]
            type_text = "" if title in ("price", "condition") else "'"
            answer = raw_input("%s[%s%s%s]: " % (title, type_text, row[index], type_text))
            if answer:
                attributes.append((title, answer))
        query = "update collection set "
        for attribute in attributes:
            title, value = attribute[0], attribute[1]
            string = "'" if title not in ("price", "condition") else ""
            query = "%s %s=%s%s%s," % (query, title, string, value, string)
        query = "%s where title='%s'" % (query[:-1], row[0])
        print  _update(cursor, query)
        if rows_count > 1:
            if raw_input("continue(n): ").lower() == NO:
                break
    return ""
                
def delete(cursor, where):
    answers = ""
    try:
        cursor.execute("delete from collection where %s" % where)
        answers = "rows deleted"
    except sqlite3.OperationalError:
        answers =  "nothing deleted"
    return answers

def sequel(cursor, where="1=1"):
    answer_length = 0
    answers = ""
    answers += "title|box|manual|cartridge|region|price|condition|special|comment|\n"
    try:
        for row in cursor.execute("select * from collection where %s" % where):
            answer_length += 1
            for column in row:
                answers = "%s%s|" % (answers, str(column) if column else "''")
            answers += "\n"
    except sqlite3.OperationalError:
        return "nothing found"
    return "%s%d entries" % (answers, answer_length)

def accept(connection):
    while True:
        try:
            connection.commit()
            return "commited"
        except sqlite3.OperationalError:
            print "database maybe locked"
            answer = raw_input("try again[yes]: ")
            if answer.lower() in NO:
                return "commit aborted"

def gui(conn, cursor):
    commands = {"sequel": sequel, "import": _import, "export": export,
                        "update": update, "delete": delete, "sequel": sequel,
                        "quit": quit}
    
    alias = { "s": "sequel", "d": "delete", "+": "switch", "i": "import",
                "a": "add", "e": "export",  "?": "help", "u": "update", 
                "l": "list", "x": "exit", "!": "commit", "q": "quit"}
                        
    read_only = True
    while True:
        while True:
            raw_command = raw_input(":> ").strip()
            if not raw_command:
                continue
            command = raw_command.lower().split()[0]
            if command in alias.keys() + alias.values():
                parameter = raw_command[len(command) + 1:].strip()
                command = alias[command] if len(command) == 1 else command
                break
            else:
                print "not recognised"
        if command == alias["+"]:
            read_only = not read_only
            print "switch to", "read only" if read_only else "write", "mode"
        elif command == alias["x"]:
            break
        elif command == alias["!"]:
            print accept(conn)
        elif command == alias["?"]:
            print alias
        elif command == alias["q"]:
            print "abort and ignore all chances since last commit"
            return
        elif read_only and command in ("import", "update", "delete", "add"):
            print "currently in read only mode" 
        elif command == alias["a"]:
            insert(cursor)
        elif command == alias["l"]:
            print sequel(cursor)    
        else:
            print commands[command](cursor, parameter) if parameter else "missing argument"
    return True
            
def main(db_name="collection.db"):
    conn, cursor = db_init(db_name)
    if gui(conn, cursor):
        print accept(conn)
    cursor.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
        