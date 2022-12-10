'''
Author: Dillon O'Brien
Email: dillon.obrien@dkolabs.com
Requirments: prettytable, pyperclip, pyfiglet

TODO
- Add notes to seaches
- Add function to remove/add tags to search
'''

import sqlite3
import os
import json
import pyperclip
import pyfiglet
from prettytable import PrettyTable


######################################
########### Database Class ###########
######################################

class DB:
    def __init__(self):
        self.db_name = "test.db"

        self.con = sqlite3.connect(self.db_name)
        self.cur = self.con.cursor()

        # Check if table exists
        res = self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='searches'").fetchone()

        # If not, create it
        if res is None:
            self.init_db()
    
    def init_db(self):
        self.cur.execute("DROP TABLE IF EXISTS searches")
        self.cur.execute("CREATE TABLE searches(id, tags, spl, notes)")
        self.commit_db()

    ### Search SPL ###
    def search_spl(self, search_term):
        res = self.cur.execute(f"SELECT * FROM searches WHERE spl LIKE ?", ("%" + search_term + "%",)).fetchall()

        if len(res) == 0:
            return None
        else:
            return {search[0]: {"tags": search[1], "spl": search[2], "notes": search[3]} for search in res}

    ### Search Tags ###
    def search_tag(self, tag):
        tag = f'%"{tag}"%'
        res = self.cur.execute(f"SELECT * FROM searches WHERE tags LIKE ?", (tag,)).fetchall()
        
        return {search[0]: {"tags": search[1], "spl": search[2], "notes": search[3]} for search in res}

    ### Get Searches ###
    def get_searches(self):
        res = self.cur.execute("SELECT * FROM searches").fetchall()

        if len(res) == 0:
            return None
        else:
            return {search[0]: {"tags": search[1], "spl": search[2], "notes": search[3]} for search in res}

    ### Get Search ###
    def get_search(self, id):
        if isinstance(id, int):
            res = self.cur.execute(f"SELECT * FROM searches WHERE id=?", (id,)).fetchone()
            return res
        else:
            return None

    ### Get Next ID ###
    def get_next_id(self):
        res = self.cur.execute("SELECT MAX(id) FROM searches")
        id = res.fetchone()[0]

        if id is None:
            return 1
        else:
            id += 1
            return id
    
    ### Get Tags ###
    def get_tags(self):
        res = self.cur.execute("SELECT DISTINCT(tags) FROM searches").fetchall()
        tags = list()
        
        for item in res:
            if item[0] != '[""]':
                temp = json.loads(item[0])
                tags += temp

        return list(dict.fromkeys(tags))

    ### Add Search ###
    def add_search(self, tags, spl, notes):
        id = self.get_next_id()

        data = (id, tags, spl, notes)

        self.cur.execute("INSERT INTO searches VALUES(?, ?, ?, ?)", data)
        self.commit_db()

    def delete_search(self, id):
        if isinstance(id, int):
            self.cur.execute(f"DELETE FROM searches WHERE id=?", (id,))

        self.commit_db()

    def commit_db(self):
        self.con.commit()

    def close_db(self):
        self.con.close()


######################################
############# Menu Class #############
######################################

class Menu:
    def __init__(self):
        self.database = DB()
        
    def main_menu(self):
        choices = [
            "Searches",
            "Database Management",
            "Quit"
        ]

        clear()
        print(pyfiglet.figlet_format("Main Menu"))
        ans = get_answer(choices)

        if ans == "Searches":
            self.search_options()
        elif ans == "Database Management":
            self.db_managment()
        elif ans == "Quit":
            self.end()

    ### SEARCHES ###
    def search_options(self):
        choices = [
            "View All Searches",
            "Search by Text",
            "Search by Tag",
            "Search by ID",
            "Add Search",
            "Delete Search",
            "Go Back",
            "Quit"
        ]

        clear()
        print(pyfiglet.figlet_format("Searches"))
        ans = get_answer(choices)

        ### View All Searches ###
        if ans == "View All Searches":
            all_searches = self.database.get_searches()

            if all_searches is not None:
                pretty_print_searches(all_searches)
                copy_search(all_searches)
            else:
                print("\nNo results")

        elif ans == "Search by Text":
            search_term = input("Enter the text to search for: ")
            results = self.database.search_spl(search_term)
            if results is None or len(results) == 0:
                print("\nNo results")
            else:
                pretty_print_searches(results)
                copy_search(results)

        ### Menu - Search by Tag ###
        elif ans == "Search by Tag":
            tags = self.database.get_tags()
            clear()
            print(pyfiglet.figlet_format("Select Tag"))
            tag = get_answer(tags)

            results = self.database.search_tag(tag)

            if results is None:
                print("\nNo results")
            else:
                pretty_print_searches(results)
                copy_search(results)
        
        ### Menu - Search by ID ###
        elif ans == "Search by ID":
            while True:
                try:
                    search_id = int(input("Enter the ID to Search: "))
                    if search_id < 1:
                        raise ValueError
                    else:
                        break
                except ValueError:
                    print("Not a valid ID")

            result = self.database.get_search(search_id)

            if result is not None:
                pyperclip.copy(result[2])
                print(f"\n{result[2]}\n\nSearch copied to clipboard")
            else:
                print("\nNo results.")

        ### Menu - Add Search ###
        elif ans == "Add Search":
            # Get SPL
            print("Enter SPL Below (ENTER to Cancel)")

            user_input = multiline_input()

            if len(user_input) == 0:
                print("Canceled")
                _ = input("\nPress Enter to Continue...")
                self.search_options()

            user_input[-1] = user_input[-1].strip("\n")
            spl = ''.join(user_input)
            
            # Get Notes
            print("Enter Notes Below (ENTER for None)")

            user_input = multiline_input()

            if len(user_input) != 0:
                user_input[-1] = user_input[-1].strip("\n")
                notes = "".join(user_input)
            else:
                notes = ""

            # Get Tags
            tags_unformatted = input("Enter tags, comma seperated (ENTER for none)\n--> ")
            tags_unformatted = tags_unformatted.split(",")
            tag_list = list()
            for tag in tags_unformatted:
                tag_list.append(tag.strip())
            
            tags = json.dumps(tag_list)

            self.database.add_search(tags, spl, notes)
            self.search_options()

        ### Menu - Delete Search ###
        elif ans == "Delete Search":
            try:
                search_to_delete = int(input("Enter the ID of the search to delete (ENTER to Cancel)\n--> "))
                self.database.delete_search(search_to_delete)
            except ValueError:
                print("\nNot a valid answer or canceled")

        ### Go Back ###
        elif ans == "Go Back":
            self.main_menu()

        ### Quit ###
        elif ans == "Quit":
            self.end()

        _ = input("\nPress Enter to Continue...")
        self.search_options()

    ### Database Management ###
    def db_managment(self):
        
        choices = [
            "Re-Index Database",
            "Export Database",
            "Reset Database",
            "Go Back",
            "Quit"
        ]

        clear()
        print(pyfiglet.figlet_format("DB Management"))
        ans = get_answer(choices)

        if ans == "Re-Index Database":
            # TODO: Create re-index functionality
            print("\nNot yet implemented")

        elif ans == "Export Database":
            # TODO: Create export functionality
            print("\nNot yet implemented")

        elif ans == "Reset Database":
            self.database.init_db()
            print("\nDatabase has been reset.")

        elif ans == "Go Back":
            self.main_menu()

        elif ans == "Quit":
            self.end()

        _ = input("\nPress Enter to Continue...")
        self.db_managment()

    def end(self):
        self.database.commit_db()
        self.database.close_db()
        quit()


######################################
########## Helper Functions ##########
######################################

# TODO Add a word wraping function to limit table width
### Print Table ###
def pretty_print_searches(searches):
    clear()
    table = PrettyTable()
    table.align = "l"
    table.field_names = ["ID", "Tags", "SPL", "Notes"]

    for search in searches:
        tags = searches[search]["tags"]
        
        if tags == "[]":
            tags_string = ""
        else:
            tags_string = tags.strip("[]")
            tags_string = tags_string.replace("\"", "")

        table.add_row([search, tags_string, searches[search]["spl"] + "\n", searches[search]["notes"]])

    print(table.get_string(sortby="ID"))

### Copy Search ###
def copy_search(searches):
    try:
        ans = int(input("Enter ID of Search to Copy or Press ENTER to Skip\n--> "))
        if ans not in searches.keys():
            raise ValueError
        else:
            pyperclip.copy(searches[ans]["spl"])
            print(f"\nSearch {ans} copied to the clipboard")

    except ValueError:
        print("\nNothing Copied")

### Get Answer ###
def get_answer(choices):
    choices_tuples = list()
    ans = None

    while True:
        for pos, choice in enumerate(choices, 1):
            print(f'{pos}) {choice}')
            choices_tuples.append((pos, choice))

        try:
            user_ans = int(input("--> "))
            for t in choices_tuples:
                if t[0] == user_ans:
                    ans = t[1]
            if ans is None:
                raise ValueError
            else:
                break
        except ValueError:
            clear()
            print("That is not a valid answer.\n")

    return ans

def multiline_input():
    lines = []

    while True:
        user_input = input()
        if user_input == "":
            break
        else:
            lines.append(user_input + "\n")

    return lines

def clear():
    if os.name == "nt":
        _ = os.system("cls")
    else:
        _ = os.system("clear")


######################################
############# Main Loop ##############
######################################

if __name__ == "__main__":

    menu = Menu()
    menu.main_menu()
