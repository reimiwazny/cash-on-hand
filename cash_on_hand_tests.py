import unittest
import cash_on_hand_api
from random import randint

class DatabaseTests(unittest.TestCase):
    #Build a saple database in memory to manipulate for tests
    def setUp(self) -> None:
        self.default_cats = [['Food', '#004400'],
                            ['Bills', '#660000'],
                            ['DEMO_CAT', '#111111'],
                            ['Pet Supplies', '#440044']]
        self.db, self.cur = cash_on_hand_api.sql_connect(':memory:')
        cash_on_hand_api.init_db(self.db, self.cur, self.default_cats)
        #Expenses setup
        self.cur.execute('INSERT INTO expenses VALUES("Food", "1/1/2021", 42.50, "Weekly Groceries", "#004400")')
        self.cur.execute('INSERT INTO expenses VALUES("Food", "9/12/2020", 350.12, "Way too much pizza", "#004400")')
        self.cur.execute('INSERT INTO expenses VALUES("Bills", "5/5/2020", 600.00, "Rent", "#660000")')
        self.cur.execute('INSERT INTO expenses VALUES("Food", "9/9/1900", 10.00, "Monthly Groceries", "#004400")')
        self.cur.execute('INSERT INTO expenses VALUES("DEMO_CAT", "1/1/1111", 11.11, "TEST_DUPES", "#111111")')
        self.cur.execute('INSERT INTO expenses VALUES("DEMO_CAT", "1/1/1111", 11.11, "TEST_DUPES", "#111111")')
        #Finance setup
        self.cur.execute('UPDATE finance SET cash=500.00 WHERE ROWID=1')
        self.db.commit()

    def tearDown(self) -> None:
        if self.db:
            self.db.close()

    def test_expense_addition(self) -> None:
        #Add an expense and test that the add method does not return a value
        self.assertEqual(cash_on_hand_api.add_expense(self.db, self.cur, cash_on_hand_api.Expense('Pet Supplies', '1/2/2020', 50.00, 'Dog toys', '#440044')),
                         None,
                         'add_expense should not return anything.')
        #Test that the added value was successfully added to the database.
        self.assertEqual(self.cur.execute('''SELECT * FROM expenses WHERE 
                         category="Pet Supplies" AND date="1/2/2020" AND amount=50.00 
                         AND title="Dog toys" AND color="#440044"''').fetchone(),
                         ('Pet Supplies', '1/2/2020', 50.00, 'Dog toys', '#440044'),
                         'Expense data was not added to the database successfully.')
        
    def test_expense_deletion(self) -> None:
        #Delete an expense from the database and test that the delete method does not return a value
        self.assertEqual(cash_on_hand_api.delete_expense(self.db, self.cur, 1), None,
                         'delete_expense should not return anything.')
        #Test that the deleted expense no longer exists in the database
        self.assertEqual(self.cur.execute('''SELECT * FROM expenses WHERE
                                          category="Food" AND date="1/1/2021" AND amount=42.50
                                          AND title="Weekly Groceries" AND color="#004400"''').fetchone(),
                                          None,
                                          'Target expense was not deleted.')
        
    def test_deletion_with_duplicates(self) -> None:
        #Delete an expense from the database and test that the delete method does not return a value.
        #This expense has a duplicate of itself at ROWID=6
        #Realistically this should never delete more than 1 expense, but better to be thorough.
        self.assertEqual(cash_on_hand_api.delete_expense(self.db, self.cur, 5), None,
                         'delete_expense should not return anything.')
        #Test that the duplicate of the deleted expense still exists. There were two instances of the expense,
        #so there should be exactly 1 instance remaining.
        self.assertEqual(len(self.cur.execute('''SELECT * FROM expenses WHERE
                                          category="DEMO_CAT" AND date="1/1/1111" AND amount=11.11
                                          AND title="TEST_DUPES" AND color="#111111"''').fetchall()),
                                          1,
                                          'Only one instance of a duplicate expense should be deleted.')   

    def test_expense_id_search(self) -> None:
        target_id = self.cur.execute('''SELECT ROWID FROM expenses WHERE
                                     category="Food" AND date="1/1/2021" AND amount=42.50 AND title="Weekly Groceries" AND color="#004400"''').fetchone()[0]
        #Test that searching for the expense in ROWID=1 successfully returns a value of 1
        self.assertEqual(cash_on_hand_api.find_expense_id(self.cur,
                                                      cash_on_hand_api.Expense('Food', '1/1/2021', 42.50, 'Weekly Groceries', '#004400')),
                                                      target_id,
                                                      'Incorrect expense ROWID returned.')
        #Searching for an expense that does not exist should return a value of -1
        self.assertEqual(cash_on_hand_api.find_expense_id(self.cur,
                                                      cash_on_hand_api.Expense('NULL', '0/0/0000', 0.00, 'Nonexistant Category', '#000000')),
                                                      -1,
                                                      'Incorrect expense ROWID returned: expecting -1.\nFound an expense that does not exist in the database.')

    def test_expense_update(self) -> None:
        #Update the expense and check that the update method is not returning a value
        self.assertEqual(cash_on_hand_api.update_expense(self.db, self.cur, 1,
                                                     cash_on_hand_api.Expense('Food', '1/1/2021', 420.50, 'Party Supplies', '#004400')),
                                                     None,
                                                     'update_expense should not return a value')
        #Check that the values of the expense were properly updated
        self.assertEqual(self.cur.execute('''SELECT * FROM expenses WHERE
                                          category="Food" AND date="1/1/2021" AND amount=420.50 AND title="Party Supplies" AND color="#004400"''').fetchone(),
                                          ('Food', '1/1/2021', 420.50, 'Party Supplies', '#004400'),
                                          '''Failed to update expense. Unable to find the intended updated expense:\n
                                          (Food, 1/1/2021, 420.50, Party Supplies, #004400).''')
        #Check that the original target expense is no longer still in the database
        self.assertEqual(self.cur.execute('''SELECT * FROM expenses WHERE
                                          category="Food" AND date="1/1/2021" AND amount=42.50 AND title="Weekly Groceries" AND color="#004400"''').fetchone(),
                                          None,
                                          '''Failed to update expense. The original target expense:\n
                                          (Food, 1/1/2021, 42.50, Weekly Groceries, #004400)\n
                                          is still in the database.''')
        
    def test_expense_category_update(self) -> None:
        #Get the number of entries in the database with a category of 'Food'
        num_entries = len(self.cur.execute('SELECT * FROM expenses WHERE category="Food"').fetchall())
        #Update an expense category and check that the update meethod does not return a value
        self.assertEqual(cash_on_hand_api.update_expense_category_group(self.db, self.cur, 'Food', 'Some Stuff'),
                         None,
                         'update_expense_category_group should not return a value.')
        #Check that the same number of expenses for the new 'Some Stuff' category is equal
        #to the number of 'Food' category entries that were originally present
        self.assertEqual(len(self.cur.execute('SELECT * FROM expenses WHERE category="Some Stuff"').fetchall()),
                         num_entries,
                         f'''Failed to update category "Food" to "Some Stuff":\n
                         Number of "Some Stuff" entries does not match the number of original "Food" entries{num_entries}''')
        #Check that the updated entries no longer have a category of 'Food'
        self.assertNotEqual(len(self.cur.execute('SELECT * FROM expenses WHERE category="Food"').fetchall()),
                            num_entries,
                            '''The number of entries in the updated category "Food" is unchanged.''')
        
    def test_update_expense_color(self) -> None:
        #Get the number of entries with the original 'Food' category color of '#004400'.
        num_entries = len(self.cur.execute('SELECT * FROM expenses WHERE category="Food" AND color="#004400"').fetchall())
        #Update the 'Food' category color and check that the update method returns None
        self.assertEqual(cash_on_hand_api.update_expense_category_color(self.db, self.cur, 'Food', '#FFFFFF'),
                         None,
                         'update_expense_category_color should not return a value.')
        #Confirm that the number of 'Food' entries with the new color of '#FFFFFF' is equal to the original
        #number of entries with color='#004400'.
        self.assertEqual(len(self.cur.execute('SELECT * FROM expenses WHERE category="Food" AND color="#FFFFFF"').fetchall()),
                         num_entries,
                         'The number of updated "Food" entries should be equal to the original number of "Food" entries.')
        
    def test_search_by_category(self) -> None:
        #Searching by the 'Food' category should yield a result of [1,2,4] with the sample db
        self.assertEqual(cash_on_hand_api.search_by_category(self.cur, 'Food'), [1,2,4], 'Did not find the target entries.')
        #Searching a category with no expenses should return -1
        self.assertEqual(cash_on_hand_api.search_by_category(self.cur, 'Wumbus'), [-1], 'Should return -1 when no entries that match the search exist.')

    def test_get_cash_amt(self) -> None:
        self.assertEqual(cash_on_hand_api.get_cash_amount(self.cur), 500.00, 'Did not get the correct cash amount.')
    
    def test_set_cash_amt(self) -> None:
        target_amount: float = float(randint(1,1000))
        #Check that set_cash_amount has no return value
        self.assertEqual(cash_on_hand_api.set_cash_amount(self.db, self.cur, target_amount),
                         None,
                         'set_cash_amount should not have a return value.')
        #Check that the cash amount was set correctly
        self.assertEqual(self.cur.execute('SELECT cash FROM finance WHERE ROWID=1').fetchone()[0],
                         target_amount,
                         'Cash amount was not set successfully.')
        #Check that the cash amount does not update when a non numeric argument is passed as new_amount
        cash_on_hand_api.set_cash_amount(self.db, self.cur, 'Poodle')
        self.assertNotEqual(self.cur.execute('SELECT cash FROM finance WHERE ROWID=1').fetchone()[0],
                            'Poodle',
                            'set_cash_amount should not update the cash amount if a non numeric value is given.')
        
    def test_duplicate_category_check(self) -> None:
        self.assertEqual(cash_on_hand_api.is_duplicate_category(self.cur, 'Food'),
                         True,
                         'Category "Food" already exists: should return True.')
        self.assertEqual(cash_on_hand_api.is_duplicate_category(self.cur, 'Tires'),
                         False,
                         'Category "Tires" does not exist: should return False.')

    def test_category_id_find(self) -> None:
        self.assertEqual(cash_on_hand_api.get_category_id(self.cur, 'Food'),
                         1,
                         'Category "Food" should return an id of 1.')
        self.assertEqual(cash_on_hand_api.get_category_id(self.cur, 'Ispods'),
                         -1,
                         'Should return -1 for a category that does not exist.')
    
    def test_add_category(self) -> None:
        self.assertEqual(cash_on_hand_api.add_category(self.db, self.cur, 'Generic', '#330033'),
                         None,
                         'add_category should not return a value.')
        self.assertEqual(self.cur.execute('SELECT * FROM categories WHERE name="Generic" AND color="#330033"').fetchone(),
                         ('Generic', '#330033'),
                         'Category was not added successfully.')
        
    def test_delete_category(self) -> None:
        self.assertEqual(cash_on_hand_api.delete_category(self.db, self.cur, 1),
                         None,
                         'delete_category should not return a value.')
        self.assertEqual(self.cur.execute('SELECT * FROM categories WHERE name="Food" AND color ="#004400"').fetchone(),
                         None,
                         'Category "Food" was not deleted from the database.')
        
    def test_single_category_update(self) -> None:
        self.assertEqual(cash_on_hand_api.update_category(self.db, self.cur, 1, 'Drinks', '#AA0011'),
                         None,
                         'update_category should not return a value.')
        self.assertEqual(self.cur.execute('SELECT * FROM categories WHERE name="Drinks" AND color="#AA0011"').fetchone(),
                         ('Drinks', '#AA0011'),
                         'Updated category entry not found.')
        self.assertEqual(self.cur.execute('SELECT * FROM categories WHERE name="Food" AND color="#004400"').fetchone(),
                         None,
                         'Target category still exists in its original form.')

    def test_db_reset(self) -> None:
        self.assertEqual(cash_on_hand_api.reset_db(self.db, self.cur, self.default_cats),
                         None,
                         'reset_db should not return a value.')
        self.assertEqual(self.cur.execute('SELECT * FROM expenses').fetchall(),
                         [] ,
                         'Table "expenses" should be empty after reset.')
        self.assertEqual(self.cur.execute('SELECT cash FROM finance WHERE ROWID=1').fetchone()[0],
                         0.00,
                         'cash value in the finance table should be 0.00 after reset.')
        self.assertEqual(self.cur.execute('SELECT * FROM categories').fetchall(),
                         [tuple(item) for item in self.default_cats],
                         'Table "categories" should be reset to the default categories list after a reset.')
        
    def test_batch_category_update(self) -> None:
        target_amount = len(self.cur.execute('SELECT * FROM expenses WHERE category="Food"').fetchall())
        self.assertEqual(cash_on_hand_api.batch_category_update(self.db, self.cur, 'Food', 'Other', '#AAAA00'),
                         None,
                         'batch_category_update should not return a value.')
        self.assertEqual(len(self.cur.execute('SELECT * FROM expenses WHERE category="Other" AND color="#AAAA00"').fetchall()),
                         target_amount,
                         'Number of final expenses of category "Other" differs from number of expenses of original category "Food".')
        self.assertEqual(self.cur.execute('SELECT * FROM expenses WHERE category="Food"').fetchall(),
                         [],
                         'Items of original category "Food" were not changed.')
        
    def test_category_sorting(self) -> None:
        self.maxDiff = None
        sorted_order = [('Bills', '5/5/2020', 600.0, 'Rent', '#660000'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('Food', '1/1/2021', 42.5, 'Weekly Groceries', '#004400'),
                        ('Food', '9/12/2020', 350.12, 'Way too much pizza', '#004400'),
                        ('Food', '9/9/1900', 10.0, 'Monthly Groceries', '#004400')]
        expenses_list = self.cur.execute('SELECT * FROM expenses').fetchall()
        expenses_list = cash_on_hand_api.expenses_sort_list_by_category(expenses_list)
        #Test that sorting by category returns expenses sorted alphabetically A-Z
        self.assertEqual(expenses_list,
                         sorted_order,
                         'Expenses list should be sorted by category alphabetically.')
        #Descending sort will not be exactly the reverse of the original sort order as subsorting
        #is determined by index 1
        sorted_order = [('Food', '1/1/2021', 42.5, 'Weekly Groceries', '#004400'),
                        ('Food', '9/12/2020', 350.12, 'Way too much pizza', '#004400'),
                        ('Food', '9/9/1900', 10.0, 'Monthly Groceries', '#004400'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('Bills', '5/5/2020', 600.0, 'Rent', '#660000')]
        expenses_list = cash_on_hand_api.expenses_sort_list_by_category(expenses_list, desc=True)
        #Test that sorting by descending alphabetical returns expenses sorted alphabetically Z-A
        self.assertEqual(expenses_list,
                    sorted_order,
                    'Expenses list should be sorted by category alphabetically in reverse.')
        
    def test_date_sorting(self) -> None:
        self.maxDiff = None
        sorted_order = [('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('Food', '9/9/1900', 10.00, 'Monthly Groceries', '#004400'),
                        ('Bills', '5/5/2020', 600.00, 'Rent', '#660000'),
                        ('Food', '9/12/2020', 350.12, 'Way too much pizza', '#004400'),
                        ('Food', '1/1/2021', 42.50, 'Weekly Groceries', '#004400')]
        expenses_list = self.cur.execute('SELECT * FROM expenses').fetchall()
        expenses_list = cash_on_hand_api.expenses_sort_list_by_date(expenses_list)
        #Test that sorting by date sorts all expenses by date, oldest to newest
        self.assertEqual(expenses_list,
                         sorted_order,
                         'Expenses list should be sorted by date from least to most current.')
        sorted_order.reverse()
        #Test that sorting by date with desc=True sortes expenses by date, newest to oldest
        expenses_list = cash_on_hand_api.expenses_sort_list_by_date(expenses_list, desc=True)
        self.assertEqual(expenses_list,
                         sorted_order,
                         'Expenses list should be sorted by date from most to least recent.')
        
    def test_cost_sorting(self) -> None:
        self.maxDiff = None
        sorted_order = [('Food', '9/9/1900', 10.00, 'Monthly Groceries', '#004400'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('DEMO_CAT', '1/1/1111', 11.11, 'TEST_DUPES', '#111111'),
                        ('Food', '1/1/2021', 42.50, 'Weekly Groceries', '#004400'),
                        ('Food', '9/12/2020', 350.12, 'Way too much pizza', '#004400'),
                        ('Bills', '5/5/2020', 600.00, 'Rent', '#660000')]
        expenses_list = self.cur.execute('SELECT * FROM expenses').fetchall()
        expenses_list = cash_on_hand_api.expenses_sort_list_by_cost(expenses_list)
        #Test sorting in ascending cost order
        self.assertEqual(expenses_list,
                         sorted_order,
                         'Expenses should be sorted based on cost, from least to greatest.') 
        sorted_order.reverse()
        expenses_list = cash_on_hand_api.expenses_sort_list_by_cost(expenses_list, desc=True)
        #Test sorting in descending cost order
        self.assertEqual(expenses_list,
                         sorted_order,
                         'Expensses should be sorted based on cost, from greatest to least.')