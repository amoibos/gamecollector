#!/usr/bin/env python
#encoding: UTF-8

from __future__ import print_function
import os
import sys
import sqlite3
import csv
import datetime
import gzip
import platform
import shutil

__author__ = "Daniel Oelschlegel"
__license__ = "new bsdl"
__copyright__ = "2013, " + __author__ 
__version__ = "0.05"

if sys.version_info[0] >= 3:
   raw_input = input

DEFAULTS = ("NOT EMPTY", "SMS", "1", "1", "1", "PAL", 5, 2, "TODAY", "")
COLUMN_LABELS = ("title", "system", "box", "manual", "cartridge", "region", "price", 
                            "condition", "date", "comment")
YES, NO = ("y", "yes"), ("n", "no")

ENCODING = sys.stdin.encoding if platform.system() == "Windows" else "utf-8"
long_names = False

def db_init(db_name):
    '''initalization database and creates an empty database if necessary'''
    connection = sqlite3.connect(":memory:")
    connection.text_factory = str
    cursor = connection.cursor()
    if os.path.exists(db_name):
        with gzip.open(db_name, "rb") as gz:
            data = gz.read()
            cursor.executescript(data if sys.version_info[0] < 3 else data.decode("utf-8"))
    else:
        ret = cursor.execute("""create table collection(
                        title text primary key, system text not null, box integer not null, manual integer not null, 
                        cartridge integer not null, region text not null, price real not null, 
                        condition integer not null, date integer not null, comment text)""")
    return connection, cursor

def export(cursor, db_name, sorting_column="title"):
    '''exports all records to utf8 csv file'''
    if db_name:
        try:
            with open(db_name, 'wb') as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerows(cursor.execute("select * from collection order by %s" % sorting_column))
            answers = "exported to %s" % db_name
        except IOError:
            print("inacceptable file name")
    else:
        answers = "file name missing"
    return answers

def _import(cursor, db_name):
    '''imports records from a csv file stored in utf8'''
    conflicts = 0
    answers = ""
    if os.path.exists(db_name):
        with open(db_name, "rb") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                try:
                    raw_insert(cursor, row)
                    answers += "%s records added to database\n" % row[0]
                except sqlite3.IntegrityError:
                    answers += "%s already in database\n" % row[0]
                    conflicts += 1
        answers += "%d conflicts" % conflicts
    else:
        answers = "file name not found"
    return answers

def raw_insert(cursor, values):
    '''import values into database and is used for user interacted and csv import'''
    answers = ""
    try:
        cursor.execute("insert into collection values (?,?,?,?,?,?,?,?,?,?)", values)
    except sqlite3.OperationalError:
        return "nothing inserted"
    except sqlite3.IntegrityError:
        return "record discard because title already exists"
    return "one record added"

def insert(cursor):
    '''ask the user for the inputs in the record'''
    answer, aborting = [], False
    for idx, column_identifier in enumerate(COLUMN_LABELS):
        while True:
            answer.append(make_unicode_python2(raw_input("%s[%s]: " % (column_identifier, str(DEFAULTS[idx])))))
            if answer[-1] == "!":
                aborting = True
                break
            #no empty title
            if not answer[-1] and "title" in column_identifier:
                answer.pop(-1)
                continue
            #date, price, condition should be values
            if column_identifier in ("date", "price", "condition") and answer[-1]:
                try:
                    answer[-1] = float(answer[-1]) if "price" == column_identifier else int(answer[-1])
                except ValueError:
                    answer.pop(-1)
                    continue
            #boolean types: box, cartridge, manual
            elif column_identifier in ("box", "cartridge", "manual"):
                if not answer[-1] or answer[-1] not in YES + NO:
                    answer[-1] = 1
                elif answer[-1].lower() in YES:
                    answer[-1] = 1
                elif answer[-1].lower() in NO:
                    answer[-1] = 0
            elif (not answer[-1] or answer[-1].upper() not in ("PAL", "USA", "BRA", "JAP", "KOR")) and "region" == column_identifier:
                answer[-1] = DEFAULTS[idx]
            elif "condition" in column_identifier and (not answer[-1] or not 1 <= int(answer[-1]) <= 6):
               answer[-1] = DEFAULTS[idx]
            elif "system" == column_identifier and not answer[-1]:
                answer[-1] = DEFAULTS[idx]
            elif "price" == column_identifier and not answer[-1]:
                answer[-1] = DEFAULTS[idx]
            elif "date" == column_identifier and not answer[-1]:
                now = datetime.datetime.now()
                answer[-1] = int("%d%02d" % (now.year % 100, now.month))
            break
        if aborting:
            return
    return raw_insert(cursor, answer)
    
def _update(cursor, query):
    '''update database via sql query'''
    try:
        cursor.execute(query)
    except sqlite3.OperationalError:
        return "nothing updated"
    except sqlite3.IntegrityError:
        return "record discard because title already exists"
    return "record updated"
    
def update(cursor, where):
    '''ask the user for data for the records specified with where clause(sql injection friendly for fuzzy)'''
    answers, failed, aborting = "", "", False
    try:
        rows = list(cursor.execute("select * from collection where %s" % where))
    except sqlite3.OperationalError:
        return "nothing to update"
    rows_count = len(rows)
    print("%d records to update" % rows_count)
    for row in rows:
        attributes = []
        for index, title in enumerate(COLUMN_LABELS):
            type_text = "" if title in ("price", "condition", "date") else "'"
            answer = make_unicode_python2(raw_input("%s[%s%s%s]: " % (title, type_text, row[index], type_text)))
            if answer:
                if answer == "!":
                    aborting = True
                    break
                attributes.append((title, answer))
        query = "update collection set "
        if not aborting:
            for attribute in attributes:
                title, value = attribute[0], attribute[1]
                string = "'" if title not in ("price", "condition", "date") else ""
                query = "%s %s=%s%s%s," % (query, title, string, value, string)
            query = "%s where title='%s'" % (query[:-1], row[0])
            failed = _update(cursor, query) 
            if rows_count > 1:
                if raw_input("continue(y): ").lower() in NO:
                    break
                print()
    return "update successful" if not "discard" in failed else failed
                
def delete(cursor, where):
    '''deletes records via where part of a sql query(sql injection friendly for fuzzy)'''
    answers = ""
    try:
        amount_records = len(list(cursor.execute("select * from collection")))
        cursor.execute("delete from collection where %s" % where)
        answers = "%d records deleted" % (amount_records - len(list(cursor.execute("select * from collection"))))
    except sqlite3.OperationalError:
        answers =  "nothing deleted"
    return answers

def prettify(value, idx):
    '''creates fixed column width'''
    if isinstance(value, str) and platform.system() == "Windows" and sys.version_info[0] < 3:
        value = value.decode("utf-8").encode(ENCODING)
    if not long_names:
        return "{:<18}".format(value[:18]) if COLUMN_LABELS[idx] in ("title", "comment") else "{:<4}".format(str(value)[:4])
    else:
        return value
        
def sequel(cursor, where="1=1", sorting_column=""):
    '''looking for records via sql query(injection friendly)'''
    answer_length = 0
    answers = ""
    for idx, column in enumerate(COLUMN_LABELS):
        answers += "%s|" % prettify(str(column), idx)
    answers += "\n"
    if not long_names:
        for idx, column in enumerate(COLUMN_LABELS):
            answers += "%s|" % prettify("--------------------", idx)
        answers += "\n"
    try:
        order = "order by %s" % sorting_column if sorting_column else ""
        for row in cursor.execute("select * from collection where %s %s" % (where, order)):
            answer_length += 1
            for idx, column in enumerate(row):
                answers += "%s|" % prettify(str(column), idx)
            answers += "\n"
    except sqlite3.OperationalError:
        return "nothing found"
    
    return "%s%d entries" % (answers, answer_length)

def make_unicode_python2(value):
    #TEST REQUIRED UNDER LINUX
    return value.decode(ENCODING).encode("utf-8") if sys.version_info[0] < 3 else value

def raw(cursor, clause):
    "bypass raw sql query"
    try:
        cursor.execute(query)
    except sqlite3.OperationalError:
        return "nothing executed"
    except sqlite3.IntegrityError:
        return "record discard because dont pass integrity check"
    return "operation sucessful"


def accept(connection, db_name):
    '''for commit changes to database'''
    while True:
        try:
            if write_back(connection, db_name):
                return "commited"
        except sqlite3.OperationalError:
            print("database maybe locked")
            answer = raw_input("try again[yes]: ")
            if answer.lower() in NO:
                return "commit aborted"

def calc(dummy, term):
    '''computes a term'''
    try:
        return eval(term)
    except SyntaxError:
        return "syntax error"
    return "term evaluated"

def gui(conn, cursor, db_name):
    '''user interaction a central entry point for all functionality'''
    commands = {"sequel": sequel, "import": _import, "export": export,
                        "update": update, "delete": delete, "sequel": sequel,
                        "evaluate": calc, "quit": quit, "raw": raw}
    
    alias = { "s": "sequel", "d": "delete", "+": "switch", "i": "import",
                "a": "add", "e": "export",  "?": "help", "u": "update", "=": "evaluate",
                "l": "list", "x": "exit", "*": "longnames", 
                "r": "raw"}
                        
    read_only = True
    while True:
        while True:
            raw_command = make_unicode_python2(raw_input(":> ").strip())
            if not raw_command:
                continue
            command = raw_command.lower().split()[0]
            if command in (list(alias.keys()) + list(alias.values())):
                parameter = raw_command[len(command) + 1:].strip()
                command = alias[command] if len(command) == 1 else command
                break
            else:
                print("not recognised")
        if command == alias["+"]:
            read_only = not read_only
            print("switch to %s mode" % ("read only" if read_only else "write"))
        elif command == alias["*"]:
            global long_names
            long_names = not long_names
            print("switch to %s mode" % ("long names" if long_names else "shortened names"))
        elif command == alias["x"]:
            break
        elif command == alias["?"]:
            print(alias)
        elif read_only and command in ("import", "update", "delete", "add"):
            print("currently in read only mode")
        elif command == alias["a"]:
            print(insert(cursor))
        elif command == alias["l"]:
            column = parameter.lower().strip() if parameter else "title"
            print(sequel(cursor, sorting_column=column if column in COLUMN_LABELS else ""))   
        else:
            print(commands[command](cursor, parameter) if parameter else "missing argument")
    return True
 
def write_back(conn, db_name):
    '''storage interface which stores a dump with gzip'''
    with gzip.open(db_name, "w") as zf:
        for line in conn.iterdump():
            record = "%s\n" % line 
            try:
                zf.write(record.encode("utf-8") if sys.version_info[0] >= 3 else \
                    record)
            except:
                print("during writing back is an error occur")
                return False
    return True
            
def main(db_name):
    '''starts gui and manage fallback for writing the database'''
    conn, cursor = db_init(db_name)
    if gui(conn, cursor, db_name):
        print("%s and application terminated" % accept(conn, db_name))
        backup_name =  db_name+".bak"
        shutil.copyfile(db_name, backup_name)
        os.remove(backup_name if write_back(conn, db_name) else db_name)
        if os.path.exists(backup_name):
            os.rename(backup_name, db_name)
    cursor.close()
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] != "--info":
            main(sys.argv[1])
        else:
            print("\nname: %s\nversion: %s\nlicense: %s\ncopyright: %s" % (__file__[:-3], __version__,\
                                                    __license__, __copyright__))
    else:
        home_dir = os.getenv("HOME") if os.getenv("HOME") else os.getenv("USERPROFILE")
        main(os.path.join(home_dir, "collect_dump.gz"))
        