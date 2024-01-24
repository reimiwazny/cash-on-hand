import sqlite3
import datetime
from dataclasses import dataclass

@dataclass
class Expense:
    category: str
    date: str
    amount: float
    title: str = ''
    color: str = '#000000'

def get_today_as_str() -> str:
    '''Returns the current data as a string in MM/DD/YYYY format.'''
    return datetime.date.today().strftime("%m/%d/%Y")

def str_to_date(string: str) -> datetime.datetime:
    '''Attempt to cast a string object to a datetime object matching the format MM/DD/YYYY.
    In the event of an invalid string, defaults to 1/1/1.'''
    output: datetime.datetime
    try:
        output = datetime.datetime.strptime(string, "%m/%d/%Y")
    except ValueError:
        output = datetime.datetime(1, 1, 1)
    return output

def sql_connect(data: str) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    '''Establish the connetion to the SQLite3 database.'''
    _db = sqlite3.connect(data)
    _cur = _db.cursor()
    return _db, _cur

def init_db(_db: sqlite3.Connection, _cur: sqlite3.Cursor, default_categories: (list[list[str, str]])) -> None:
    '''Check if the connected database already contains the required tables. If it does not, creates
    them.'''
    _cur.execute('CREATE TABLE IF NOT EXISTS expenses(category, date, amount, title, color)')
    _cur.execute('CREATE TABLE IF NOT EXISTS finance(cash)')
    _cur.execute('INSERT INTO finance VALUES(0.00)')
    _cur.execute('CREATE TABLE IF NOT EXISTS categories(name, color)')
    if default_categories:
        for category in default_categories:
            _cur.execute('INSERT INTO categories VALUES(?, ?)', [category[0], category[1]])
    _db.commit()

def find_expense_id(_cur: sqlite3.Cursor, expense: Expense) -> int:
    '''Attempt to find the ROWID of an expense given its attributes. If the expense is found,
    returns its ROWID. If it is not found, returns -1.'''
    expense_id: int = _cur.execute('SELECT ROWID FROM expenses WHERE category=? AND date=? AND amount=? AND title=? AND color=?',
                                  [expense.category, expense.date, expense.amount, expense.title, expense.color]).fetchone()
    if  expense_id != None:
        return expense_id[0]
    return -1
    
def add_expense(_db: sqlite3.Connection,
                _cur: sqlite3.Cursor,
                expense: Expense) -> None:
    '''Add an expense to the expenses database with a given category, amount, and optional title and color code.'''
    _cur.execute('INSERT INTO expenses VALUES(?, ?, ?, ?, ?)',
                 [expense.category, expense.date, expense.amount, expense.title, expense.color])
    _db.commit()

def delete_expense(_db:sqlite3.Connection, _cur: sqlite3.Cursor, target_id: int) -> None:
    '''Delete an expense from the database with a given ROWID.
    ROWID is used to select an expense to ensure the correct expense is deleted in the event
    that duplicate expenses exist.'''
    _cur.execute('DELETE FROM expenses WHERE ROWID=?', [target_id])
    _db.commit()
    
def update_expense(_db:sqlite3.Connection, _cur: sqlite3.Cursor, target_id: int, new: Expense) -> None:
    '''Update the expense with ROWID=target_id with a given set of values.'''
    _cur.execute('UPDATE expenses SET category=?, date=?, amount=?, title=?, color=? WHERE ROWID=?',
                 [new.category, new.date, new.amount, new.title, new.color, target_id])
    _db.commit()

def update_expense_category_group(_db:sqlite3.Connection, _cur: sqlite3.Cursor, target_category: str, new_category: str) -> None:
    '''Update all expenses of a given category group target_category to a new category, given as new_category.'''
    _cur.execute('UPDATE expenses SET category=? WHERE category=?', [new_category, target_category])
    _db.commit()

def update_expense_category_color(_db:sqlite3.Connection, _cur: sqlite3.Cursor, target_category: str, new_color: str) -> None:
    '''Update the color code of all expenses for a given category.'''
    _cur.execute('UPDATE expenses SET color=? WHERE category=?', [new_color, target_category])
    _db.commit()

def search_by_category(_cur: sqlite3.Cursor, cat_name: str) -> list[int]:
    '''Find all expenses with the given category cat_name, and return a list of their ROWIDs.'''
    results = _cur.execute('SELECT ROWID FROM expenses WHERE category=?', [cat_name]).fetchall()
    if len(results) > 0:
        return [item[0] for item in results]
    return [-1]

def delete_by_category(_db:sqlite3.Connection, _cur: sqlite3.Cursor, target_category: str) -> None:
    '''Delete all expenses from the database whose category is equal to the target_category.'''
    _cur.execute('DELETE FROM expenses WHERE category=?', [target_category])
    _db.commit()

def get_cash_amount(_cur: sqlite3.Cursor) -> float:
    '''Retrive the current cash on hand amount from the database.'''
    return _cur.execute('SELECT cash FROM finance WHERE ROWID=1').fetchone()[0]

def set_cash_amount(_db: sqlite3.Connection, _cur: sqlite3.Cursor, new_amount: float):
    '''Update the current amount of cash on hand in the database.'''
    if (type(new_amount) in [int, float]):
        _cur.execute('UPDATE finance SET cash=? WHERE ROWID=1', [new_amount])
        _db.commit() 

def is_duplicate_category(_cur: sqlite3.Cursor, cat_name: str) -> bool:
    '''Check if a category already exists.'''
    if _cur.execute('SELECT * FROM categories WHERE name=?', [cat_name]).fetchall() == []:
        return False
    return True       

def get_category_id(_cur: sqlite3.Cursor, cat_name: str) -> int:
    '''Search the categories database for a given category and returns its ROWID if it is found.'''
    cat_id = _cur.execute('SELECT ROWID FROM categories WHERE name=?', [cat_name]).fetchone()
    if cat_id != None:
        return cat_id[0]
    return -1

def add_category(_db: sqlite3.Connection, _cur: sqlite3.Cursor, cat_name: str, cat_color: str) -> None:
    '''Adds a new category to the categories database.'''
    _cur.execute('INSERT INTO categories VALUES(?, ?)', [cat_name, cat_color])
    _db.commit()

def delete_category(_db: sqlite3.Connection, _cur: sqlite3.Cursor, cat_id: int) -> None:
    '''Deletes a given category from the categories database.
    Be sure to check the expenses database and adjust any existing entries that used the
    deleted category afterwards.'''
    _cur.execute('DELETE FROM categories WHERE ROWID=?', [cat_id])
    _db.commit()

def update_category(_db: sqlite3.Connection, _cur: sqlite3.Cursor, cat_id: int, new_name: str, new_color: str) -> None:
    '''Update the name and color of the category at ROWID = cat_id.
    Be sure to update the entries in the expenses database that used the previous category
    after use.'''
    _cur.execute('UPDATE categories SET name=?, color=? WHERE ROWID=?', [new_name, new_color, cat_id])
    _db.commit()

def batch_category_update(_db: sqlite3.Connection,
                          _cur: sqlite3.Cursor,
                          target_cat: str,
                          new_cat_name: str,
                          new_cat_color: str) -> None:
    '''Updates all expenses of a given category with a new category and color code.'''
    _cur.execute('UPDATE expenses SET category=?, color=? WHERE category=?', [new_cat_name, new_cat_color, target_cat])
    _db.commit()

def expenses_sort_list_by_category(expenses: list, desc=False) -> list:
    '''Sort the given list of expenses by category name, alphabetically..
    If desc=True, the list will be sorted in reverse alphabetical order.'''
    return sorted(expenses, key=lambda x: x[0], reverse=desc)

def expenses_sort_list_by_date(expenses: list, desc=False) -> list:
    '''Sort the given list of expenses by posting date, oldest to newest.
    If desc=True, the list will be sorted from newest to oldest.'''
    return sorted(expenses, key=lambda x: str_to_date(x[1]), reverse=desc)

def expenses_sort_list_by_cost(expenses: list, desc=False) -> list:
    '''Sort the given list of expenses by cost, from least to greatest.
    If desc=True, the list will be sorted greatest to least.'''
    return sorted(expenses, key=lambda x: x[2], reverse=desc)

def reset_db(_db: sqlite3.Connection,_cur: sqlite3.Cursor, default_categories: (list[list[str, str]])) -> None:
    '''Clears the expenses and finance tables, reverting the database to a blank slate.
    Also reverts all user made categories to the initial defaults.'''
    _cur.execute('DELETE FROM expenses')
    _cur.execute('UPDATE finance SET cash=0.00 WHERE ROWID=1')
    _cur.execute('DELETE FROM categories')
    if default_categories:
        for category in default_categories:
            _cur.execute('INSERT INTO categories VALUES(?, ?)', [category[0], category[1]])
    _db.commit()
    _cur.execute('VACUUM')

def main() -> None:
    pass

if __name__ == '__main__':
    main()