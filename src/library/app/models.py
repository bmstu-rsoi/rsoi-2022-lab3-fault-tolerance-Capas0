import enum

from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError

from .base import db, app


class Library(db.Model):
    __tablename__ = 'library'

    id = Column(Integer, primary_key=True)
    library_uid = Column(UUID(), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    city = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)


class Book(db.Model):
    __tablename__ = 'book'

    class Condition(enum.Enum):
        EXCELLENT = 'EXCELLENT'
        GOOD = 'GOOD'
        BAD = 'BAD'

    id = Column(Integer, primary_key=True)
    book_uid = Column(UUID(), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    author = Column(String(255))
    genre = Column(String(255))
    condition = Column(Enum(Condition), nullable=False, default=Condition.EXCELLENT)


class LibraryBook(db.Model):
    __tablename__ = 'library_books'

    book_id = Column(ForeignKey(Book.id), primary_key=True)
    library_id = Column(ForeignKey(Library.id), primary_key=True)
    available_count = Column(Integer, nullable=False)
    library = db.relationship('Library')
    book = db.relationship('Book')


with app.app_context():
    db.create_all()

    book = Book(
        id=1,
        book_uid='f7cdc58f-2caf-4b15-9727-f89dcc629b27',
        name='Краткий курс C++ в 7 томах',
        author='Бьерн Страуструп',
        genre='Научная фантастика',
        condition='EXCELLENT'
    )
    library = Library(
        id=1,
        library_uid='83575e12-7ce0-48ee-9931-51919ff3c9ee',
        name='Библиотека имени 7 Непьющих',
        city='Москва',
        address='2-я Бауманская ул., д.5, стр.1'
    )
    lb = LibraryBook(book=book, library=library, available_count=1)

    db.session.add(book)
    db.session.add(library)
    db.session.add(lb)

    try:
        db.session.commit()
    except IntegrityError:
        pass
