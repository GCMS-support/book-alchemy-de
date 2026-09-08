"""Relational models for the digital library."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date)
    books = db.relationship('Book', back_populates='author', cascade='all, delete-orphan')
    __table_args__ = (db.CheckConstraint('date_of_death IS NULL OR date_of_death >= birth_date'),)

    def __repr__(self):
        return f'<Author {self.id}: {self.name}>'

    def __str__(self):
        return self.name

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    rating = db.Column(db.Integer)
    author = db.relationship('Author', back_populates='books')
    __table_args__ = (db.CheckConstraint('rating IS NULL OR rating BETWEEN 1 AND 10'), db.CheckConstraint('publication_year BETWEEN 1 AND 9999'))

    def __repr__(self):
        return f'<Book {self.id}: {self.title}>'

    def __str__(self):
        return f'{self.title} ({self.publication_year})'
