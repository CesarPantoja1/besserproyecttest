from datetime import datetime, date, time
from typing import Any, List, Optional, Union, Set
from enum import Enum
from pydantic import BaseModel, field_validator


############################################
# Enumerations are defined here
############################################

############################################
# Classes are defined here
############################################
class LoanCreate(BaseModel):
    dueDate: date
    loanId: int
    loanDate: datetime
    returnDate: datetime
    bookcopy_1: Optional[List[int]] = None  # 1:N Relationship
    member: Optional[List[int]] = None  # 1:N Relationship


class ReservationCreate(BaseModel):
    reservationId: int
    reservationDate: datetime
    status: str
    book_3: Optional[List[int]] = None  # 1:N Relationship
    member_1: Optional[List[int]] = None  # 1:N Relationship


class GenreCreate(BaseModel):
    genreId: int
    name: str
    book_2: List[int]  # N:M Relationship


class AuthorCreate(BaseModel):
    authorId: int
    name: str
    biography: str
    book_1: List[int]  # N:M Relationship


class BookCopyCreate(BaseModel):
    copyId: int
    status: str
    loan_1: int  # N:1 Relationship (mandatory)
    book: Optional[List[int]] = None  # 1:N Relationship


class MemberCreate(BaseModel):
    joinDate: date
    memberId: int
    email: str
    name: str
    loan: int  # N:1 Relationship (mandatory)
    reservation: int  # N:1 Relationship (mandatory)


class BookCreate(BaseModel):
    publicationDate: date
    summary: str
    title: str
    isbn: str
    author: List[int]  # N:M Relationship
    reservation_1: int  # N:1 Relationship (mandatory)
    genre: List[int]  # N:M Relationship
    bookcopy: int  # N:1 Relationship (mandatory)


