import enum
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, ForeignKey, Table, Text, Boolean, String, Date, 
    Time, DateTime, Float, Integer, Enum
)
from sqlalchemy.orm import (
    column_property, DeclarativeBase, Mapped, mapped_column, relationship
)
from datetime import datetime as dt_datetime, time as dt_time, date as dt_date

class Base(DeclarativeBase):
    pass



# Tables definition for many-to-many relationships
categorizedas = Table(
    "categorizedas",
    Base.metadata,
    Column("genre", ForeignKey("genre.id"), primary_key=True),
    Column("book_2", ForeignKey("book.id"), primary_key=True),
)
writtenby = Table(
    "writtenby",
    Base.metadata,
    Column("author", ForeignKey("author.id"), primary_key=True),
    Column("book_1", ForeignKey("book.id"), primary_key=True),
)

# Tables definition
class Loan(Base):
    __tablename__ = "loan"
    id: Mapped[int] = mapped_column(primary_key=True)
    loanId: Mapped[int] = mapped_column(Integer)
    loanDate: Mapped[dt_datetime] = mapped_column(DateTime)
    dueDate: Mapped[dt_date] = mapped_column(Date)
    returnDate: Mapped[dt_datetime] = mapped_column(DateTime)

class Reservation(Base):
    __tablename__ = "reservation"
    id: Mapped[int] = mapped_column(primary_key=True)
    reservationId: Mapped[int] = mapped_column(Integer)
    reservationDate: Mapped[dt_datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(100))

class Genre(Base):
    __tablename__ = "genre"
    id: Mapped[int] = mapped_column(primary_key=True)
    genreId: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))

class Author(Base):
    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True)
    authorId: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    biography: Mapped[str] = mapped_column(String(100))

class BookCopy(Base):
    __tablename__ = "bookcopy"
    id: Mapped[int] = mapped_column(primary_key=True)
    copyId: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(100))
    loan_1_id: Mapped[int] = mapped_column(ForeignKey("loan.id"))

class Member(Base):
    __tablename__ = "member"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    joinDate: Mapped[dt_date] = mapped_column(Date)
    memberId: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservation.id"))
    loan_id: Mapped[int] = mapped_column(ForeignKey("loan.id"))

class Book(Base):
    __tablename__ = "book"
    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(String(100))
    publicationDate: Mapped[dt_date] = mapped_column(Date)
    reservation_1_id: Mapped[int] = mapped_column(ForeignKey("reservation.id"))
    bookcopy_id: Mapped[int] = mapped_column(ForeignKey("bookcopy.id"))


#--- Relationships of the loan table
Loan.member: Mapped[List["Member"]] = relationship("Member", back_populates="loan", foreign_keys=[Member.loan_id])
Loan.bookcopy_1: Mapped[List["BookCopy"]] = relationship("BookCopy", back_populates="loan_1", foreign_keys=[BookCopy.loan_1_id])

#--- Relationships of the reservation table
Reservation.book_3: Mapped[List["Book"]] = relationship("Book", back_populates="reservation_1", foreign_keys=[Book.reservation_1_id])
Reservation.member_1: Mapped[List["Member"]] = relationship("Member", back_populates="reservation", foreign_keys=[Member.reservation_id])

#--- Relationships of the genre table
Genre.book_2: Mapped[List["Book"]] = relationship("Book", secondary=categorizedas, back_populates="genre")

#--- Relationships of the author table
Author.book_1: Mapped[List["Book"]] = relationship("Book", secondary=writtenby, back_populates="author")

#--- Relationships of the bookcopy table
BookCopy.loan_1: Mapped["Loan"] = relationship("Loan", back_populates="bookcopy_1", foreign_keys=[BookCopy.loan_1_id])
BookCopy.book: Mapped[List["Book"]] = relationship("Book", back_populates="bookcopy", foreign_keys=[Book.bookcopy_id])

#--- Relationships of the member table
Member.reservation: Mapped["Reservation"] = relationship("Reservation", back_populates="member_1", foreign_keys=[Member.reservation_id])
Member.loan: Mapped["Loan"] = relationship("Loan", back_populates="member", foreign_keys=[Member.loan_id])

#--- Relationships of the book table
Book.author: Mapped[List["Author"]] = relationship("Author", secondary=writtenby, back_populates="book_1")
Book.reservation_1: Mapped["Reservation"] = relationship("Reservation", back_populates="book_3", foreign_keys=[Book.reservation_1_id])
Book.genre: Mapped[List["Genre"]] = relationship("Genre", secondary=categorizedas, back_populates="book_2")
Book.bookcopy: Mapped["BookCopy"] = relationship("BookCopy", back_populates="book", foreign_keys=[Book.bookcopy_id])

# Database connection
DATABASE_URL = "sqlite:///Class_Diagram.db"  # SQLite connection
engine = create_engine(DATABASE_URL, echo=True)

# Create tables in the database
Base.metadata.create_all(engine, checkfirst=True)