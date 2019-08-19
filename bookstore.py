import sqlite3

db = 'database/books.db'

class Book:

    """ Represents one book in the program. 
    Before books are saved, create without ID then call save() method to save to DB and create an ID. 
    Future calls to save() will update the database record for the book with this id. """

    def __init__(self, title, author, read=False, id=None):
        self.title = title 
        self.author = author
        self.read = read 
        self.id = id

        self.bookstore = BookStore()


    def save(self):
        if self.id:
            self.bookstore._update_book(self)
        else:
            self.bookstore._add_book(self)


    def __str__(self):
        read_status = 'have' if self.read else 'have not'
        return f'ID {self.id}, Title: {self.title}, Author: {self.author}. You {read_status} read this book.'


    def __repr__(self):
        return f'ID {self.id} Title: {self.title} Author: {self.author} Read: {self.read}'


    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.id == other.id and self.title == other.title and self.author == other.author and self.read == other.read 
        return False 

    def __ne__(self, other):
        if not isinstance(self, other.__class__):
            return True 

        return self.id != other.id or self.title != other.title or self.author != other.author or self.read != other.read 


    def __hash__(self):
        return hash((self.id, self.title, self.author, self.read))





class BookStore:

    """ Singleton class to hold and manage a list of Books. """

    instance = None


    class __BookStore:

        def __init__(self):
            
            create_table_sql = 'CREATE TABLE IF NOT EXISTS books (title TEXT, author TEXT, read BOOLEAN)'
        
            con = sqlite3.connect(db)
        
            with con:
                con.execute(create_table_sql)

            con.close()
            

        def _add_book(self, book):
            """ Adds book to store. Raises BookError if a book with exact author and title is already in the store.
             :param book the book to add """


            # Raise BookError if book with same author and title is already in list. Don't add the new book. 
            if self.exact_match(book):
                raise BookError(f'{book} is already in the store.')


            insert_sql = 'INSERT INTO books (title, author, read) VALUES (?, ?, ?)'

            con = sqlite3.connect(db)

            with con:
                res = con.execute(insert_sql, (book.title, book.author, book.read) )
                new_id = res.lastrowid  # Get the ID of the new row in the table 
                    
            con.close()

            book.id = new_id   # Set this book's ID 
            


        def delete_book(self, book):

            """ Removes book from store. Raises BookError if book not in store. """

            delete_sql = 'DELETE FROM books WHERE rowid = ?'

            con = sqlite3.connect(db)

            with con:
                deleted = con.execute(delete_sql, (book.id, ) )
                deleted_count = deleted.rowcount
            con.close()

            if deleted_count == 0:
                raise BookError(f'Book {book} not found in store.')


        def delete_all_books(self):
            """ Deletes all books from database """

            delete_all_sql = "DELETE FROM books"

            con = sqlite3.connect(db)

            with con:
                deleted = con.execute(delete_all_sql)
            con.close()
           


        def _update_book(self, book):
            
            update_read_sql = 'UPDATE books SET title = ?, author = ?, read = ? WHERE rowid = ?'

            con = sqlite3.connect(db)
            
            with con:
                updated = con.execute(update_read_sql, (book.title, book.author, book.read, book.id) )
                rows_modfied = updated.rowcount
                
            con.close()

            
            # TODO raise BookError if book not found.
            if rows_modfied == 0:
                raise BookError(f'Book with id {book.id} not found')



        def exact_match(self, search_book):
            """ Searches bookstore for a book with exact same title and author. Not case sensitive.
             :param search_book: the book to search for
             :returns: True if a book with same author and title are found in the store, false otherwise. """
            
            
            find_exact_match_sql = 'SELECT * FROM books WHERE UPPER(title) = UPPER(?) AND UPPER(author) = UPPER(?)'
            
            con = sqlite3.connect(db)

            with con:
                rows = con.execute(find_exact_match_sql, (search_book.title, search_book.author) )
                the_row = rows.fetchone()
                found = the_row is not None
                print('\nsearch', search_book, 'found? ', found, the_row)

            con.close() 

            return found


        def get_book_by_id(self, id):
            """ Searches list for Book with given ID,
            :param id the ID to search for
            :returns the book, if found, or None if book not found.
            """
         

            get_book_by_id_sql = 'SELECT rowid, * FROM books WHERE rowid = ?'

            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row


            with con:
                rows = con.execute(get_book_by_id_sql, (id,)  )
                book_data = rows.fetchone()
                
                if book_data:
                    book = Book(book_data['title'], book_data['author'], book_data['read'], book_data['rowid'])
                   
            con.close()            
            
            return book 



        def book_search(self, term):
            """ Searches the store for books whose author or title contain a search term.
            Makes partial matches, so a search for 'Row' will match a book with author='JK Rowling'; a book with title='Rowing For Dummies'
            :param term the search term
            :returns a list of books with author or title that match the search term.
            """
            # TODO make this case-insensitive. So 'ROWLING' is a match for a book with author = 'jk rowling'

 
            search_sql = 'SELECT rowid, * FROM books WHERE UPPER(title) like UPPER(?) OR UPPER(author) like UPPER(?)'

            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row


            with con:

                search = f'%{term}%'   # Example - if searching for text with 'bOb' in then use '%bOb%' in SQL
                rows = con.execute(search_sql, (search, search) )
                
                books = []

                for r in rows:
                    book = Book(r['title'], r['author'], r['read'], r['rowid'])
                    books.append(book)

            con.close()            
            
            return books



        def get_books_by_read_value(self, read):
            """ Get a list of books that have been read, or list of books that have not been read.
            :param read True for books that have been read, False for books that have not been read
            :returns all books with the read value.
            """

            get_book_by_id_sql = 'SELECT rowid, * FROM books WHERE read = ?'

            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row


            with con:
                rows = con.execute(get_book_by_id_sql, (read, ) )
                
                books = []

                for r in rows:
                    book = Book(r['title'], r['author'], r['read'], r['rowid'])
                    books.append(book)

            con.close()            
            
            return books


        def get_all_books(self):
            """ :returns entire booklist """
    
            get_all_books_sql = 'SELECT rowid, * FROM books'

            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row


            with con:
                rows = con.execute(get_all_books_sql)
                
                books = []

                for r in rows:
                    book = Book(r['title'], r['author'], r['read'], r['rowid'])
                    books.append(book)

            con.close()            
            
            return books


        def book_count(self):
            """ :returns the number of books in the store """
            
            count_books_sql = 'SELECT COUNT(*) FROM books'

            con = sqlite3.connect(db)

            with con:
                count = con.execute(count_books_sql)
                total = count.fetchone()[0]    # fetchone() returns the first row of the results. This is a tuple with one element - the count 
            con.close()            
            
            return total


    def __new__(cls):
        """ The __new__ magic method handles object creation. (Compare to __init__ which initializes an object.) 
        If there's already a Bookstore instance, return that. If not, then create a new one
        This way, there can only ever be one __Bookstore, which uses the same database. """
        
        if not BookStore.instance:
            BookStore.instance = BookStore.__BookStore()
        return BookStore.instance


    def __getattr__(self, name):
        return getattr(self.instance, name)


    def __setattr__(self, name, value):
        return setattr(self.instance, name, value)



class BookError(Exception):
    """ For BookStore errors. """
    pass