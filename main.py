'''
Author: Dillon O'Brien
Email: dillon.obrien@dkolabs.com
Requirments: prettytable, pyperclip, pyfiglet

TODO
- Add function to edit SPL and Notes
- Limit table width (being completed by implementing word wrapping)
- Word wrap tags, maybe two per line
- Word wrap notes
- Allow user to select max line lengths for word wrapping
'''

import sqlite3
import os
import json
from textwrap import fill

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
    
    ### Init Database ###
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
            if res is not None:
                return {res[0]: {"tags": res[1], "spl": res[2], "notes": res[3]}}
        
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

    ### Delete Search ###
    def delete_search(self, id):
        if isinstance(id, int):
            self.cur.execute("DELETE FROM searches WHERE id=?", (id,))
            self.commit_db()
    
    ### Update Tags ###
    def update_tags(self, id, new_tags):
        if isinstance(id, int):
            self.cur.execute("UPDATE searches SET tags=? WHERE id=?", (new_tags, id))
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
        
    ### Main Menu ###
    def main_menu(self):
        choices = [
            "Searches",
            "Database Management",
            "Quit"
        ]

        clear()
        print(pyfiglet.figlet_format("Main Menu"))
        ans = get_answer(choices)

        ## Searches
        if ans == "Searches":
            self.search_menu()
        
        ## Database Management
        elif ans == "Database Management":
            self.db_menu()
        
        ## Quit
        elif ans == "Quit":
            self.end()

    ### SEARCH Menu ###
    def search_menu(self):
        choices = [
            "View All Searches",
            "Search by Text",
            "Search by Tag",
            "Search by ID",
            "Add Search",
            "Go Back",
            "Quit"
        ]

        clear()
        print(pyfiglet.figlet_format("Searches"))
        ans = get_answer(choices)

        ## View All Searches
        if ans == "View All Searches":
            all_searches = self.database.get_searches()

            if all_searches is not None:
                clear()
                self.search_options(all_searches)
            else:
                print("\nNo results")

        ## Search by Text
        elif ans == "Search by Text":
            search_term = input("\nEnter the text to search for: ")
            results = self.database.search_spl(search_term)

            if results is None or len(results) == 0:
                print("\nNo results")
            else:
                clear()
                self.search_options(results)

        ## Search by Tag
        elif ans == "Search by Tag":
            tags = self.database.get_tags()
            clear()
            print(pyfiglet.figlet_format("Select Tag"))
            tags.sort()
            tag = get_answer(tags)

            results = self.database.search_tag(tag)

            if results is None:
                print("\nNo results")
            else:
                clear()
                self.search_options(results)
        
        ## Search by ID
        elif ans == "Search by ID":
            while True:
                try:
                    search_id = int(input("Enter the ID to Search: "))
                    if search_id < 1:
                        raise ValueError
                    else:
                        break
                except ValueError:
                    print("\nNot a valid ID")
                    _ = input("\nPress Enter to Continue...") 
                    self.search_menu()

            result = self.database.get_search(search_id)

            if result is not None:
                self.search_options(result)
            else:
                print("\nNo results.")

        ## Add Search
        elif ans == "Add Search":
            # Get SPL
            print("Enter SPL Below (ENTER to Cancel)")

            user_input = multiline_input()

            if len(user_input) == 0:
                print("Canceled")
                _ = input("\nPress Enter to Continue...")
                self.search_menu()

            user_input[-1] = user_input[-1].strip("\n")
            spl = "".join(user_input)
            
            # Get Notes
            print("Enter Notes Below (ENTER for None)")

            user_input = multiline_input()

            if len(user_input) != 0:
                user_input[-1] = user_input[-1].strip("\n")
                notes = "".join(user_input)
            else:
                notes = ""

            # Get Tags
            tags = tags_input()

            # Add search
            self.database.add_search(tags, spl, notes)
            print("\nSearch Added.")

        ## Go Back
        elif ans == "Go Back":
            self.main_menu()

        ## Quit
        elif ans == "Quit":
            self.end()

        _ = input("\nPress Enter to Continue...")
        self.search_menu()

    ### Search Options ###
    def search_options(self, searches):

        # Narrow down options to one search
        if len(searches) > 1:
            pretty_print_searches(searches)
            try:
                search_id = int(input("Search ID or ENTER for None: "))
                if search_id not in searches.keys():
                    raise ValueError
                else: 
                    search = {search_id: searches[search_id]}
            except ValueError:
                print("\nNo results")
                _ = input("\nPress Enter to Continue...")
                self.search_menu()
        else:
            search = searches
        
        choices =[
            "Copy",
            "Edit Tags",
            "Edit SPL",
            "Edit Notes",
            "Delete",
            "Go Back",
            "Quit"
        ]

        clear()
        print(pyfiglet.figlet_format("Search Options"))
        pretty_print_searches(search)
        search_id = list(search.keys()).pop()
        print("")
        ans = get_answer(choices)

        ## Copy
        if ans == "Copy":
            pyperclip.copy(searches[search_id]["spl"])
            print(f"\nSearch {search_id} copied to the clipboard.")

        ## Edit Tags
        elif ans == "Edit Tags":
            print("")

            new_tags = tags_input()
            self.database.update_tags(search_id, new_tags)
            updated_search = self.database.get_search(search_id)

            print("\nUpdated Search\n")
            pretty_print_searches(updated_search)

        ## Edit SPL
        elif ans == "Edit SPL":
            print("Not yet implemented")
            pass

        ## Edit Notes
        elif ans == "Edit Notes":
            print("Not yet implemented")
            pass
        
        ## Delete Search
        elif ans == "Delete":
            self.database.delete_search(search_id)
            print(f"\nSearch {search_id} deleted.")

        ## Go Back
        elif ans == "Go Back":
            self.search_menu()

        ## Quit
        elif ans == "Quit":
            self.end()

        _ = input("\nPress Enter to Continue...")
        self.search_menu()

    ### Database Management ###
    def db_menu(self):
        
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

        ## Re-Index Database
        if ans == "Re-Index Database":
            # TODO: Create re-index functionality
            print("\nNot yet implemented")

        ## Export Database
        elif ans == "Export Database":
            # TODO: Create export functionality
            print("\nNot yet implemented")

        ## Reset Database
        elif ans == "Reset Database":
            self.database.init_db()
            print("\nDatabase has been reset.")

        ## Go Back
        elif ans == "Go Back":
            self.main_menu()

        ## Quit
        elif ans == "Quit":
            self.end()

        _ = input("\nPress Enter to Continue...")
        self.db_menu()

    ### End ###
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
    table = PrettyTable()
    table.align = "l"
    table.field_names = ["ID", "Tags", "SPL", "Notes"]

    for search in searches:
        # Format tags to look nice
        tags = searches[search]["tags"]
        
        if tags == "[]":
            tags_string = ""
        else:
            tags_string = tags.strip("[]")
            tags_string = tags_string.replace("\"", "")
        
        # Word wrap SPL
        spl = searches[search]["spl"]
        spl_split = [line + "\n" for line in spl.split('\n') if line]

        spl_list = list()
        for line in spl_split:
            filled = fill(line, subsequent_indent="    ")
            spl_list.append(filled)
        
        spl = "\n".join(spl_list)

        # Add search to table
        table.add_row([search, tags_string, spl + "\n", searches[search]["notes"]])

    # Print out the table sorted by ID
    print(table.get_string(sortby="ID"))

### Get Answer ###
def get_answer(choices):
    choices_tuples = list()
    ans = None

    while True:
        for pos, choice in enumerate(choices, 1):
            print(f"{pos}) {choice}")
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

### Tags Input ###
def tags_input():
    tags_unformatted = input("Enter tags, comma seperated (ENTER for none)\n--> ")
    tags_unformatted = tags_unformatted.split(",")
    tag_list = list()

    for tag in tags_unformatted:
        tag_list.append(tag.strip())
    
    return json.dumps(tag_list)

### Multiline Input ###
def multiline_input():
    lines = []

    while True:
        user_input = input()
        if user_input == "":
            break
        else:
            lines.append(user_input + "\n")

    return lines

### Clear ###
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
