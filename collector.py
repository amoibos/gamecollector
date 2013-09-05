#!/usr/bin/env python
#encoding:UTF-8
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

if sys.version_info[0] == 3:
   raw_input = input

COLUMN_LABELS = ("title", "box", "manual", "cartridge", "region", 
         "price", "condition", "date", "special", "comment")
TABLE_FORMAT_QUESTIONS = ("title[NOT EMPTY]",  "box[YES]", "manual[YES]", "cartridge[YES]", 
                        "region[PAL]", "price[5]", "condition[2]", "date[TODAY]", "special['']", "comment['']")
YES, NO = ("y", "yes"), ("n", "no")
ENCODING = "cp850" if platform.system() == "Windows" else "utf-8"

long_names = False

def db_init(db_name):
    connection = sqlite3.connect(":memory:")
    connection.text_factory = str
    cursor = connection.cursor()
    if os.path.exists(db_name):
        with gzip.open(db_name, "rb") as gz:
            data = gz.read()
            try:
                cursor.executescript(data)
            except ValueError:
                cursor.executescript(data.decode("utf-8"))
    else:
        ret = cursor.execute("""create table collection(
                        title primary key, box, manual, cartridge, region, 
                        price, condition, date, special, comment)""")
    return connection, cursor

def export(cursor, db_name):
    answers = ""
    if db_name:
        try:
            with open(db_name, 'w') as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerows(cursor.execute("select * from collection"))
            answers = "exported to %s" % db_name
        except IOError:
            print("inacceptable file name")
    else:
        answers = "file name missing"
    return answers

def _import(cursor, db_name):
    conflicts = 0
    answers = ""
    if os.path.exists(db_name):
        with open(db_name) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                try:
                    raw_insert(cursor, row)
                    answers += "%s added to database\n" % row[0]
                except sqlite3.IntegrityError:
                    answers += "%s already in database\n" % row[0]
                    conflicts += 1
        answers += "%d conflicts" % conflicts
    else:
        answers = "file name not found"
    return answers

def raw_insert(cursor, values):
    answers = ""
    try:
        cursor.execute("insert into collection values (?,?,?,?,?,?,?,?,?,?)", values)
    except sqlite3.OperationalError:
        return "nothing inserted"
    except sqlite3.IntegrityError:
        return "record discard because title already exists"
    return "one row added"

def insert(cursor):
    answer = []
    for column_identifier in TABLE_FORMAT_QUESTIONS:
        while True:
            answer.append(raw_input("%s: " % column_identifier))#.encode("utf-8"))
            #no empty title
            if not answer[-1] and "title" in column_identifier:
                answer.pop(-1)
                continue
            #date, price, condition should be values
            if column_identifier.split("[")[0] in ("date", "price", "condition") and answer[-1]:
                try:
                    answer[-1] = int(answer[-1])
                except ValueError:
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
            elif "date" in column_identifier and not answer[-1]:
                now = datetime.datetime.now()
                answer[-1] = int("%d%02d" % (now.year % 100, now.month))
            break
    return raw_insert(cursor, answer)
    
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
    print("%d to update" % rows_count)
    for row in rows:
        for index, column_identifier in enumerate(TABLE_FORMAT_QUESTIONS):
            title = column_identifier.split('[')[0]
            type_text = "" if title in ("price", "condition", "date") else "'"
            answer = raw_input("%s[%s%s%s]: " % (title, type_text, row[index], type_text))
            answer = answer.decode(ENCODING).encode("utf-8")
            if answer:
                attributes.append((title, answer))
        query = "update collection set "
        for attribute in attributes:
            title, value = attribute[0], attribute[1]
            string = "'" if title not in ("price", "condition", "date") else ""
            query = "%s %s=%s%s%s," % (query, title, string, value, string)
        query = "%s where title='%s'" % (query[:-1], row[0])
        print(_update(cursor, query))
        if rows_count > 1:
            if raw_input("continue(n): ").lower() in NO:
                break
    return ""
                
def delete(cursor, where):
    '''sql injection friendly'''
    answers = ""
    try:
        cursor.execute("delete from collection where %s" % where)
        answers = "rows deleted"
    except sqlite3.OperationalError:
        answers =  "nothing deleted"
    return answers

def prettify(value, idx):
    if isinstance(value, str) and platform.system() == "Windows" and sys.version_info[0] == 2:
        value = value.decode("utf-8").encode(ENCODING)
    if not long_names:
        return "{:<18}".format(value[:18]) if COLUMN_LABELS[idx] in ("title", "comment") else "{:<4}".format(str(value)[:4])
    else:
        return value
        
def sequel(cursor, where="1=1"):
    '''sql injection friendly'''
    answer_length = 0
    answers = ""
    for idx, column in enumerate(COLUMN_LABELS):
        answers += "%s|" % prettify(column, idx)
    answers += "\n"
    if not long_names:
        for idx, column in enumerate(COLUMN_LABELS):
            answers += "%s|" % prettify("--------------------", idx)
        answers += "\n"
    try:
        for row in cursor.execute("select * from collection where %s" % where):
            answer_length += 1
            for idx, column in enumerate(row):
                answers += "%s|" % prettify(column, idx)
            answers += "\n"
    except sqlite3.OperationalError:
        return "nothing found"
    
    return "%s%d entries" % (answers, answer_length)

def accept(connection, db_name):
    while True:
        try:
            connection.commit()
            write_back(connection, db_name)
            return "commited"
        except sqlite3.OperationalError:
            print("database maybe locked")
            answer = raw_input("try again[yes]: ")
            if answer.lower() in NO:
                return "commit aborted"

def calc(dummy, term):
    try:
        return eval(term)
    except SyntaxError:
        return "syntax error"

def gui(conn, cursor, db_name):
    commands = {"sequel": sequel, "import": _import, "export": export,
                        "update": update, "delete": delete, "sequel": sequel,
                        "evaluate": calc, "quit": quit}
    
    alias = { "s": "sequel", "d": "delete", "+": "switch", "i": "import",
                "a": "add", "e": "export",  "?": "help", "u": "update", "=": "evaluate",
                "l": "list", "x": "exit", "!": "commit", "*": "longnames", "q": "quit"}
                        
    read_only = True
    while True:
        while True:
            raw_command = raw_input(":> ").strip()
            if sys.version_info[0] == 2:
                raw_command = raw_command.decode(ENCODING)
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
        elif command == alias["!"]:
            print(accept(conn, db_name))
        elif command == alias["?"]:
            print(alias)
        elif command == alias["q"]:
            print("abort and ignore all chances since last commit")
            return
        elif read_only and command in ("import", "update", "delete", "add"):
            print("currently in read only mode")
        elif command == alias["a"]:
            print(insert(cursor))
        elif command == alias["l"]:
            print(sequel(cursor))   
        else:
            print(commands[command](cursor, parameter) if parameter else "missing argument")
    return True
 
def write_back(conn, db_name):
    with gzip.open(db_name, "w") as zf:
        for line in conn.iterdump():
            record = "%s\n" % line 
            try:
                if sys.version_info[0] == 3:
                    zf.write(record.encode("utf-8"))
                else:
                    zf.write(record.decode(ENCODING).encode("utf-8"))
            except:
                print("error occurs during write back")
                return False
    return True
            
def main(db_name):
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
        