"""Populate the library through the same POST routes used by its forms."""
from app import app
from data_models import db, Author, Book

SAMPLES = [
 ('Jane Austen','1775-12-16','1817-07-18','Pride and Prejudice','9780141439518',1813),
 ('George Orwell','1903-06-25','1950-01-21','1984','9780451524935',1949),
 ('Mary Shelley','1797-08-30','1851-02-01','Frankenstein','9780141439471',1818),
 ('Franz Kafka','1883-07-03','1924-06-03','The Metamorphosis','9780553213690',1915),
 ('F. Scott Fitzgerald','1896-09-24','1940-12-21','The Great Gatsby','9780743273565',1925),
 ('J. R. R. Tolkien','1892-01-03','1973-09-02','The Hobbit','9780547928227',1937),
]

def seed():
    client = app.test_client()
    client.get('/add_author')
    with client.session_transaction() as session:
        token = session['csrf_token']
    for name, birth, death, title, isbn, year in SAMPLES:
        with app.app_context():
            author = db.session.scalar(db.select(Author).where(Author.name == name))
            author_id = author.id if author else None
        if author_id is None:
            response = client.post('/add_author', data={'name':name, 'birth_date':birth, 'date_of_death':death, 'csrf_token':token})
            assert response.status_code == 302, response.get_data(as_text=True)
            with app.app_context():
                author_id = db.session.scalar(db.select(Author).where(Author.name == name)).id
        with app.app_context():
            exists = db.session.scalar(db.select(Book).where(Book.isbn == isbn)) is not None
        if not exists:
            response = client.post('/add_book', data={'title':title,'isbn':isbn,'publication_year':year,'author_id':author_id,'csrf_token':token})
            assert response.status_code == 302, response.get_data(as_text=True)
    with app.app_context():
        print(f'SEEDED: {db.session.query(Author).count()} authors, {db.session.query(Book).count()} books via POST routes')

if __name__ == '__main__':
    seed()
