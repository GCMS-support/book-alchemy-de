"""Integration tests use an isolated in-memory database, never the real collection."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from app import create_app
from data_models import db, Author, Book

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SECRET_KEY':'test-only', 'SQLALCHEMY_DATABASE_URI':'sqlite://', 'OPENROUTER_API_KEY':None})
        self.client = self.app.test_client()
        self.client.get('/add_author')
        with self.client.session_transaction() as session:
            self.token = session['csrf_token']

    def post(self, path, **data):
        return self.client.post(path, data={'csrf_token':self.token, **data})

    def author(self, name='Test Author'):
        response = self.post('/add_author', name=name, birth_date='1900-01-01')
        self.assertEqual(response.status_code,302)
        with self.app.app_context():
            return db.session.scalar(db.select(Author).where(Author.name==name)).id

    def book(self, author_id, title='Test Book', isbn='9780141439518'):
        response = self.post('/add_book', title=title, isbn=isbn, publication_year='2000', author_id=str(author_id))
        self.assertEqual(response.status_code,302)
        with self.app.app_context():
            return db.session.scalar(db.select(Book).where(Book.isbn==isbn)).id

    def test_empty_and_pages(self):
        for path in ['/', '/add_author','/add_book','/recommendations','/static/style.css']:
            with self.client.get(path) as response:
                self.assertEqual(response.status_code,200)
        for path in ['/book/999','/author/999','/missing']:
            self.assertEqual(self.client.get(path).status_code,404)

    def test_create_and_detail(self):
        aid = self.author()
        self.assertIn(b'Autor erfolgreich',self.client.get('/add_author').data)
        bid = self.book(aid)
        self.assertIn(b'Buch erfolgreich',self.client.get('/add_book').data)
        for path in ['/', f'/book/{bid}',f'/author/{aid}']:
            response = self.client.get(path)
            self.assertEqual(response.status_code,200)
            self.assertIn(b'Test Book',response.data)

    def test_search_sort_and_literal_wildcards(self):
        first = self.author('Zulu Author')
        second = self.author('Alpha Author')
        self.book(first, 'Alpha Book')
        self.book(second, 'Zulu Book','9780451524935')
        self.assertIn(b'Alpha Book',self.client.get('/?search=alpha+book').data)
        self.assertNotIn(b'Zulu Book',self.client.get('/?search=alpha+book').data)
        self.assertIn(b'Keine B',self.client.get('/?search=nonexistent').data)
        self.assertIn(b'Keine B',self.client.get('/?search=%25').data)
        title = self.client.get('/?sort=title').data
        author = self.client.get('/?sort=author').data
        self.assertLess(title.index(b'Alpha Book'),title.index(b'Zulu Book'))
        self.assertLess(author.index(b'Zulu Book'),author.index(b'Alpha Book'))

    def test_author_validation(self):
        for data in [{'name':'','birth_date':'1900-01-01'}, {'name':'A','birth_date':'bad'}, {'name':'A','birth_date':'1900-01-01','date_of_death':'1800-01-01'}]:
            self.assertEqual(self.post('/add_author',**data).status_code,400)
        with self.app.app_context():
            self.assertEqual(db.session.query(Author).count(),0)

    def test_book_validation_and_duplicate(self):
        aid = self.author()
        self.book(aid)
        data = {'title':'Another','isbn':'9780141439518','publication_year':'2000','author_id':str(aid)}
        self.assertEqual(self.post('/add_book',**data).status_code,400)
        for field,value in [('isbn','9780141439519'),('title',''),('publication_year','zero'),('author_id','999')]:
            invalid = {**data,field:value}
            self.assertEqual(self.post('/add_book',**invalid).status_code,400)
        with self.app.app_context():
            self.assertEqual(db.session.query(Book).count(),1)

    def test_rating(self):
        bid = self.book(self.author())
        for rating in ['0','11','abc']:
            self.assertEqual(self.post(f'/book/{bid}/rate',rating=rating).status_code,400)
        for rating in ['1','10']:
            self.assertEqual(self.post(f'/book/{bid}/rate',rating=rating).status_code,302)
        with self.app.app_context():
            self.assertEqual(db.session.get(Book,bid).rating,10)

    def test_book_delete_keeps_author(self):
        aid = self.author()
        bid = self.book(aid)
        self.assertEqual(self.client.get(f'/book/{bid}/delete').status_code,405)
        self.assertEqual(self.post(f'/book/{bid}/delete').status_code,302)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Book,bid))
            self.assertIsNotNone(db.session.get(Author,aid))

    def test_author_delete_cascades(self):
        aid = self.author()
        self.book(aid)
        self.book(aid,'Second','9780451524935')
        self.assertEqual(self.post(f'/author/{aid}/delete').status_code,302)
        with self.app.app_context():
            self.assertEqual(db.session.query(Book).count(),0)
            self.assertEqual(db.session.query(Author).count(),0)

    def test_csrf_and_escaping(self):
        self.assertEqual(self.client.post('/add_author',data={'name':'bad'}).status_code,400)
        self.book(self.author(),'<script>alert(1)</script>')
        body = self.client.get('/').data
        self.assertNotIn(b'<script>',body)
        self.assertIn(b'&lt;script&gt;',body)

    def test_ai_setup_and_consent(self):
        self.assertEqual(self.post('/recommendations').status_code,503)
        self.app.config['OPENROUTER_API_KEY']='test-key'
        self.assertEqual(self.post('/recommendations',consent='yes').status_code,400)
        self.book(self.author())
        self.assertEqual(self.post('/recommendations').status_code,400)

    def test_ai_success_and_failure_mocked(self):
        self.app.config['OPENROUTER_API_KEY']='test-key'
        self.book(self.author())
        reply = io.BytesIO(json.dumps({'choices':[{'message':{'content':'Drei Empfehlungen'}}]}).encode())
        with patch('app.urlopen',return_value=reply) as mock:
            response = self.post('/recommendations',consent='yes')
            self.assertEqual(response.status_code,200)
            self.assertIn(b'Drei Empfehlungen',response.data)
            payload = json.loads(mock.call_args.args[0].data)
            self.assertIn('Test Book',payload['messages'][1]['content'])
        with patch('app.urlopen',side_effect=URLError('offline')):
            self.assertEqual(self.post('/recommendations',consent='yes').status_code,502)

if __name__ == '__main__':
    unittest.main(verbosity=2)
