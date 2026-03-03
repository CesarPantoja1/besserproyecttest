import uvicorn
import os, json
import time as time_module
import logging
from fastapi import Depends, FastAPI, HTTPException, Request, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic_classes import *
from sql_alchemy import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

############################################
#
#   Initialize the database
#
############################################

def init_db():
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/Class_Diagram.db")
    # Ensure local SQLite directory exists (safe no-op for other DBs)
    os.makedirs("data", exist_ok=True)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal

app = FastAPI(
    title="Class_Diagram API",
    description="Auto-generated REST API with full CRUD operations, relationship management, and advanced features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "System health and statistics"},
        {"name": "Loan", "description": "Operations for Loan entities"},
        {"name": "Loan Relationships", "description": "Manage Loan relationships"},
        {"name": "Reservation", "description": "Operations for Reservation entities"},
        {"name": "Reservation Relationships", "description": "Manage Reservation relationships"},
        {"name": "Genre", "description": "Operations for Genre entities"},
        {"name": "Genre Relationships", "description": "Manage Genre relationships"},
        {"name": "Author", "description": "Operations for Author entities"},
        {"name": "Author Relationships", "description": "Manage Author relationships"},
        {"name": "BookCopy", "description": "Operations for BookCopy entities"},
        {"name": "BookCopy Relationships", "description": "Manage BookCopy relationships"},
        {"name": "Member", "description": "Operations for Member entities"},
        {"name": "Member Relationships", "description": "Manage Member relationships"},
        {"name": "Book", "description": "Operations for Book entities"},
        {"name": "Book Relationships", "description": "Manage Book relationships"},
    ]
)

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

############################################
#
#   Middleware
#
############################################

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses."""
    start_time = time_module.time()
    response = await call_next(request)
    process_time = time_module.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

############################################
#
#   Exception Handlers
#
############################################

# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": str(exc),
            "detail": "Invalid input data provided"
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    logger.error(f"Database integrity error: {exc}")

    # Extract more detailed error information
    error_detail = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Conflict",
            "message": "Data conflict occurred",
            "detail": error_detail
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle general SQLAlchemy errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "Database operation failed",
            "detail": "An internal database error occurred"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "message": exc.detail,
            "detail": f"HTTP {exc.status_code} error occurred"
        }
    )

# Initialize database session
SessionLocal = init_db()
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        logger.error("Database session rollback due to exception")
        raise
    finally:
        db.close()

############################################
#
#   Global API endpoints
#
############################################

@app.get("/", tags=["System"])
def root():
    """Root endpoint - API information"""
    return {
        "name": "Class_Diagram API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }


@app.get("/statistics", tags=["System"])
def get_statistics(database: Session = Depends(get_db)):
    """Get database statistics for all entities"""
    stats = {}
    stats["loan_count"] = database.query(Loan).count()
    stats["reservation_count"] = database.query(Reservation).count()
    stats["genre_count"] = database.query(Genre).count()
    stats["author_count"] = database.query(Author).count()
    stats["bookcopy_count"] = database.query(BookCopy).count()
    stats["member_count"] = database.query(Member).count()
    stats["book_count"] = database.query(Book).count()
    stats["total_entities"] = sum(stats.values())
    return stats


############################################
#
#   BESSER Action Language standard lib
#
############################################


async def BAL_size(sequence:list) -> int:
    return len(sequence)

async def BAL_is_empty(sequence:list) -> bool:
    return len(sequence) == 0

async def BAL_add(sequence:list, elem) -> None:
    sequence.append(elem)

async def BAL_remove(sequence:list, elem) -> None:
    sequence.remove(elem)

async def BAL_contains(sequence:list, elem) -> bool:
    return elem in sequence

async def BAL_filter(sequence:list, predicate) -> list:
    return [elem for elem in sequence if predicate(elem)]

async def BAL_forall(sequence:list, predicate) -> bool:
    for elem in sequence:
        if not predicate(elem):
            return False
    return True

async def BAL_exists(sequence:list, predicate) -> bool:
    for elem in sequence:
        if predicate(elem):
            return True
    return False

async def BAL_one(sequence:list, predicate) -> bool:
    found = False
    for elem in sequence:
        if predicate(elem):
            if found:
                return False
            found = True
    return found

async def BAL_is_unique(sequence:list, mapping) -> bool:
    mapped = [mapping(elem) for elem in sequence]
    return len(set(mapped)) == len(mapped)

async def BAL_map(sequence:list, mapping) -> list:
    return [mapping(elem) for elem in sequence]

async def BAL_reduce(sequence:list, reduce_fn, aggregator) -> any:
    for elem in sequence:
        aggregator = reduce_fn(aggregator, elem)
    return aggregator


############################################
#
#   Loan functions
#
############################################

@app.get("/loan/", response_model=None, tags=["Loan"])
def get_all_loan(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Loan)
        loan_list = query.all()

        # Serialize with relationships included
        result = []
        for loan_item in loan_list:
            item_dict = loan_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            bookcopy_list = database.query(BookCopy).filter(BookCopy.loan_1_id == loan_item.id).all()
            item_dict['bookcopy_1'] = []
            for bookcopy_obj in bookcopy_list:
                bookcopy_dict = bookcopy_obj.__dict__.copy()
                bookcopy_dict.pop('_sa_instance_state', None)
                item_dict['bookcopy_1'].append(bookcopy_dict)
            member_list = database.query(Member).filter(Member.loan_id == loan_item.id).all()
            item_dict['member'] = []
            for member_obj in member_list:
                member_dict = member_obj.__dict__.copy()
                member_dict.pop('_sa_instance_state', None)
                item_dict['member'].append(member_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Loan).all()


@app.get("/loan/count/", response_model=None, tags=["Loan"])
def get_count_loan(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Loan entities"""
    count = database.query(Loan).count()
    return {"count": count}


@app.get("/loan/paginated/", response_model=None, tags=["Loan"])
def get_paginated_loan(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Loan entities"""
    total = database.query(Loan).count()
    loan_list = database.query(Loan).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": loan_list
        }

    result = []
    for loan_item in loan_list:
        bookcopy_1_ids = database.query(BookCopy.id).filter(BookCopy.loan_1_id == loan_item.id).all()
        member_ids = database.query(Member.id).filter(Member.loan_id == loan_item.id).all()
        item_data = {
            "loan": loan_item,
            "bookcopy_1_ids": [x[0] for x in bookcopy_1_ids],            "member_ids": [x[0] for x in member_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/loan/search/", response_model=None, tags=["Loan"])
def search_loan(
    database: Session = Depends(get_db)
) -> list:
    """Search Loan entities by attributes"""
    query = database.query(Loan)


    results = query.all()
    return results


@app.get("/loan/{loan_id}/", response_model=None, tags=["Loan"])
async def get_loan(loan_id: int, database: Session = Depends(get_db)) -> Loan:
    db_loan = database.query(Loan).filter(Loan.id == loan_id).first()
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")

    bookcopy_1_ids = database.query(BookCopy.id).filter(BookCopy.loan_1_id == db_loan.id).all()
    member_ids = database.query(Member.id).filter(Member.loan_id == db_loan.id).all()
    response_data = {
        "loan": db_loan,
        "bookcopy_1_ids": [x[0] for x in bookcopy_1_ids],        "member_ids": [x[0] for x in member_ids]}
    return response_data



@app.post("/loan/", response_model=None, tags=["Loan"])
async def create_loan(loan_data: LoanCreate, database: Session = Depends(get_db)) -> Loan:


    db_loan = Loan(
        dueDate=loan_data.dueDate,        loanId=loan_data.loanId,        loanDate=loan_data.loanDate,        returnDate=loan_data.returnDate        )

    database.add(db_loan)
    database.commit()
    database.refresh(db_loan)

    if loan_data.bookcopy_1:
        # Validate that all BookCopy IDs exist
        for bookcopy_id in loan_data.bookcopy_1:
            db_bookcopy = database.query(BookCopy).filter(BookCopy.id == bookcopy_id).first()
            if not db_bookcopy:
                raise HTTPException(status_code=400, detail=f"BookCopy with id {bookcopy_id} not found")

        # Update the related entities with the new foreign key
        database.query(BookCopy).filter(BookCopy.id.in_(loan_data.bookcopy_1)).update(
            {BookCopy.loan_1_id: db_loan.id}, synchronize_session=False
        )
        database.commit()
    if loan_data.member:
        # Validate that all Member IDs exist
        for member_id in loan_data.member:
            db_member = database.query(Member).filter(Member.id == member_id).first()
            if not db_member:
                raise HTTPException(status_code=400, detail=f"Member with id {member_id} not found")

        # Update the related entities with the new foreign key
        database.query(Member).filter(Member.id.in_(loan_data.member)).update(
            {Member.loan_id: db_loan.id}, synchronize_session=False
        )
        database.commit()



    bookcopy_1_ids = database.query(BookCopy.id).filter(BookCopy.loan_1_id == db_loan.id).all()
    member_ids = database.query(Member.id).filter(Member.loan_id == db_loan.id).all()
    response_data = {
        "loan": db_loan,
        "bookcopy_1_ids": [x[0] for x in bookcopy_1_ids],        "member_ids": [x[0] for x in member_ids]    }
    return response_data


@app.post("/loan/bulk/", response_model=None, tags=["Loan"])
async def bulk_create_loan(items: list[LoanCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Loan entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_loan = Loan(
                dueDate=item_data.dueDate,                loanId=item_data.loanId,                loanDate=item_data.loanDate,                returnDate=item_data.returnDate            )
            database.add(db_loan)
            database.flush()  # Get ID without committing
            created_items.append(db_loan.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Loan entities"
    }


@app.delete("/loan/bulk/", response_model=None, tags=["Loan"])
async def bulk_delete_loan(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Loan entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_loan = database.query(Loan).filter(Loan.id == item_id).first()
        if db_loan:
            database.delete(db_loan)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Loan entities"
    }

@app.put("/loan/{loan_id}/", response_model=None, tags=["Loan"])
async def update_loan(loan_id: int, loan_data: LoanCreate, database: Session = Depends(get_db)) -> Loan:
    db_loan = database.query(Loan).filter(Loan.id == loan_id).first()
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")

    setattr(db_loan, 'dueDate', loan_data.dueDate)
    setattr(db_loan, 'loanId', loan_data.loanId)
    setattr(db_loan, 'loanDate', loan_data.loanDate)
    setattr(db_loan, 'returnDate', loan_data.returnDate)
    if loan_data.bookcopy_1 is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(BookCopy).filter(BookCopy.loan_1_id == db_loan.id).update(
            {BookCopy.loan_1_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if loan_data.bookcopy_1:
            # Validate that all IDs exist
            for bookcopy_id in loan_data.bookcopy_1:
                db_bookcopy = database.query(BookCopy).filter(BookCopy.id == bookcopy_id).first()
                if not db_bookcopy:
                    raise HTTPException(status_code=400, detail=f"BookCopy with id {bookcopy_id} not found")

            # Update the related entities with the new foreign key
            database.query(BookCopy).filter(BookCopy.id.in_(loan_data.bookcopy_1)).update(
                {BookCopy.loan_1_id: db_loan.id}, synchronize_session=False
            )
    if loan_data.member is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Member).filter(Member.loan_id == db_loan.id).update(
            {Member.loan_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if loan_data.member:
            # Validate that all IDs exist
            for member_id in loan_data.member:
                db_member = database.query(Member).filter(Member.id == member_id).first()
                if not db_member:
                    raise HTTPException(status_code=400, detail=f"Member with id {member_id} not found")

            # Update the related entities with the new foreign key
            database.query(Member).filter(Member.id.in_(loan_data.member)).update(
                {Member.loan_id: db_loan.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_loan)

    bookcopy_1_ids = database.query(BookCopy.id).filter(BookCopy.loan_1_id == db_loan.id).all()
    member_ids = database.query(Member.id).filter(Member.loan_id == db_loan.id).all()
    response_data = {
        "loan": db_loan,
        "bookcopy_1_ids": [x[0] for x in bookcopy_1_ids],        "member_ids": [x[0] for x in member_ids]    }
    return response_data


@app.delete("/loan/{loan_id}/", response_model=None, tags=["Loan"])
async def delete_loan(loan_id: int, database: Session = Depends(get_db)):
    db_loan = database.query(Loan).filter(Loan.id == loan_id).first()
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    database.delete(db_loan)
    database.commit()
    return db_loan





############################################
#
#   Reservation functions
#
############################################

@app.get("/reservation/", response_model=None, tags=["Reservation"])
def get_all_reservation(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Reservation)
        reservation_list = query.all()

        # Serialize with relationships included
        result = []
        for reservation_item in reservation_list:
            item_dict = reservation_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            book_list = database.query(Book).filter(Book.reservation_1_id == reservation_item.id).all()
            item_dict['book_3'] = []
            for book_obj in book_list:
                book_dict = book_obj.__dict__.copy()
                book_dict.pop('_sa_instance_state', None)
                item_dict['book_3'].append(book_dict)
            member_list = database.query(Member).filter(Member.reservation_id == reservation_item.id).all()
            item_dict['member_1'] = []
            for member_obj in member_list:
                member_dict = member_obj.__dict__.copy()
                member_dict.pop('_sa_instance_state', None)
                item_dict['member_1'].append(member_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Reservation).all()


@app.get("/reservation/count/", response_model=None, tags=["Reservation"])
def get_count_reservation(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Reservation entities"""
    count = database.query(Reservation).count()
    return {"count": count}


@app.get("/reservation/paginated/", response_model=None, tags=["Reservation"])
def get_paginated_reservation(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Reservation entities"""
    total = database.query(Reservation).count()
    reservation_list = database.query(Reservation).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": reservation_list
        }

    result = []
    for reservation_item in reservation_list:
        book_3_ids = database.query(Book.id).filter(Book.reservation_1_id == reservation_item.id).all()
        member_1_ids = database.query(Member.id).filter(Member.reservation_id == reservation_item.id).all()
        item_data = {
            "reservation": reservation_item,
            "book_3_ids": [x[0] for x in book_3_ids],            "member_1_ids": [x[0] for x in member_1_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/reservation/search/", response_model=None, tags=["Reservation"])
def search_reservation(
    database: Session = Depends(get_db)
) -> list:
    """Search Reservation entities by attributes"""
    query = database.query(Reservation)


    results = query.all()
    return results


@app.get("/reservation/{reservation_id}/", response_model=None, tags=["Reservation"])
async def get_reservation(reservation_id: int, database: Session = Depends(get_db)) -> Reservation:
    db_reservation = database.query(Reservation).filter(Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    book_3_ids = database.query(Book.id).filter(Book.reservation_1_id == db_reservation.id).all()
    member_1_ids = database.query(Member.id).filter(Member.reservation_id == db_reservation.id).all()
    response_data = {
        "reservation": db_reservation,
        "book_3_ids": [x[0] for x in book_3_ids],        "member_1_ids": [x[0] for x in member_1_ids]}
    return response_data



@app.post("/reservation/", response_model=None, tags=["Reservation"])
async def create_reservation(reservation_data: ReservationCreate, database: Session = Depends(get_db)) -> Reservation:


    db_reservation = Reservation(
        reservationId=reservation_data.reservationId,        reservationDate=reservation_data.reservationDate,        status=reservation_data.status        )

    database.add(db_reservation)
    database.commit()
    database.refresh(db_reservation)

    if reservation_data.book_3:
        # Validate that all Book IDs exist
        for book_id in reservation_data.book_3:
            db_book = database.query(Book).filter(Book.id == book_id).first()
            if not db_book:
                raise HTTPException(status_code=400, detail=f"Book with id {book_id} not found")

        # Update the related entities with the new foreign key
        database.query(Book).filter(Book.id.in_(reservation_data.book_3)).update(
            {Book.reservation_1_id: db_reservation.id}, synchronize_session=False
        )
        database.commit()
    if reservation_data.member_1:
        # Validate that all Member IDs exist
        for member_id in reservation_data.member_1:
            db_member = database.query(Member).filter(Member.id == member_id).first()
            if not db_member:
                raise HTTPException(status_code=400, detail=f"Member with id {member_id} not found")

        # Update the related entities with the new foreign key
        database.query(Member).filter(Member.id.in_(reservation_data.member_1)).update(
            {Member.reservation_id: db_reservation.id}, synchronize_session=False
        )
        database.commit()



    book_3_ids = database.query(Book.id).filter(Book.reservation_1_id == db_reservation.id).all()
    member_1_ids = database.query(Member.id).filter(Member.reservation_id == db_reservation.id).all()
    response_data = {
        "reservation": db_reservation,
        "book_3_ids": [x[0] for x in book_3_ids],        "member_1_ids": [x[0] for x in member_1_ids]    }
    return response_data


@app.post("/reservation/bulk/", response_model=None, tags=["Reservation"])
async def bulk_create_reservation(items: list[ReservationCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Reservation entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_reservation = Reservation(
                reservationId=item_data.reservationId,                reservationDate=item_data.reservationDate,                status=item_data.status            )
            database.add(db_reservation)
            database.flush()  # Get ID without committing
            created_items.append(db_reservation.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Reservation entities"
    }


@app.delete("/reservation/bulk/", response_model=None, tags=["Reservation"])
async def bulk_delete_reservation(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Reservation entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_reservation = database.query(Reservation).filter(Reservation.id == item_id).first()
        if db_reservation:
            database.delete(db_reservation)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Reservation entities"
    }

@app.put("/reservation/{reservation_id}/", response_model=None, tags=["Reservation"])
async def update_reservation(reservation_id: int, reservation_data: ReservationCreate, database: Session = Depends(get_db)) -> Reservation:
    db_reservation = database.query(Reservation).filter(Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    setattr(db_reservation, 'reservationId', reservation_data.reservationId)
    setattr(db_reservation, 'reservationDate', reservation_data.reservationDate)
    setattr(db_reservation, 'status', reservation_data.status)
    if reservation_data.book_3 is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Book).filter(Book.reservation_1_id == db_reservation.id).update(
            {Book.reservation_1_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if reservation_data.book_3:
            # Validate that all IDs exist
            for book_id in reservation_data.book_3:
                db_book = database.query(Book).filter(Book.id == book_id).first()
                if not db_book:
                    raise HTTPException(status_code=400, detail=f"Book with id {book_id} not found")

            # Update the related entities with the new foreign key
            database.query(Book).filter(Book.id.in_(reservation_data.book_3)).update(
                {Book.reservation_1_id: db_reservation.id}, synchronize_session=False
            )
    if reservation_data.member_1 is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Member).filter(Member.reservation_id == db_reservation.id).update(
            {Member.reservation_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if reservation_data.member_1:
            # Validate that all IDs exist
            for member_id in reservation_data.member_1:
                db_member = database.query(Member).filter(Member.id == member_id).first()
                if not db_member:
                    raise HTTPException(status_code=400, detail=f"Member with id {member_id} not found")

            # Update the related entities with the new foreign key
            database.query(Member).filter(Member.id.in_(reservation_data.member_1)).update(
                {Member.reservation_id: db_reservation.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_reservation)

    book_3_ids = database.query(Book.id).filter(Book.reservation_1_id == db_reservation.id).all()
    member_1_ids = database.query(Member.id).filter(Member.reservation_id == db_reservation.id).all()
    response_data = {
        "reservation": db_reservation,
        "book_3_ids": [x[0] for x in book_3_ids],        "member_1_ids": [x[0] for x in member_1_ids]    }
    return response_data


@app.delete("/reservation/{reservation_id}/", response_model=None, tags=["Reservation"])
async def delete_reservation(reservation_id: int, database: Session = Depends(get_db)):
    db_reservation = database.query(Reservation).filter(Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    database.delete(db_reservation)
    database.commit()
    return db_reservation





############################################
#
#   Genre functions
#
############################################

@app.get("/genre/", response_model=None, tags=["Genre"])
def get_all_genre(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Genre)
        genre_list = query.all()

        # Serialize with relationships included
        result = []
        for genre_item in genre_list:
            item_dict = genre_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            book_list = database.query(Book).join(categorizedas, Book.id == categorizedas.c.book_2).filter(categorizedas.c.genre == genre_item.id).all()
            item_dict['book_2'] = []
            for book_obj in book_list:
                book_dict = book_obj.__dict__.copy()
                book_dict.pop('_sa_instance_state', None)
                item_dict['book_2'].append(book_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Genre).all()


@app.get("/genre/count/", response_model=None, tags=["Genre"])
def get_count_genre(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Genre entities"""
    count = database.query(Genre).count()
    return {"count": count}


@app.get("/genre/paginated/", response_model=None, tags=["Genre"])
def get_paginated_genre(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Genre entities"""
    total = database.query(Genre).count()
    genre_list = database.query(Genre).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": genre_list
        }

    result = []
    for genre_item in genre_list:
        book_ids = database.query(categorizedas.c.book_2).filter(categorizedas.c.genre == genre_item.id).all()
        item_data = {
            "genre": genre_item,
            "book_ids": [x[0] for x in book_ids],
        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/genre/search/", response_model=None, tags=["Genre"])
def search_genre(
    database: Session = Depends(get_db)
) -> list:
    """Search Genre entities by attributes"""
    query = database.query(Genre)


    results = query.all()
    return results


@app.get("/genre/{genre_id}/", response_model=None, tags=["Genre"])
async def get_genre(genre_id: int, database: Session = Depends(get_db)) -> Genre:
    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    book_ids = database.query(categorizedas.c.book_2).filter(categorizedas.c.genre == db_genre.id).all()
    response_data = {
        "genre": db_genre,
        "book_ids": [x[0] for x in book_ids],
}
    return response_data



@app.post("/genre/", response_model=None, tags=["Genre"])
async def create_genre(genre_data: GenreCreate, database: Session = Depends(get_db)) -> Genre:

    if not genre_data.book_2 or len(genre_data.book_2) < 1:
        raise HTTPException(status_code=400, detail="At least 1 Book(s) required")
    if genre_data.book_2:
        for id in genre_data.book_2:
            # Entity already validated before creation
            db_book = database.query(Book).filter(Book.id == id).first()
            if not db_book:
                raise HTTPException(status_code=404, detail=f"Book with ID {id} not found")

    db_genre = Genre(
        genreId=genre_data.genreId,        name=genre_data.name        )

    database.add(db_genre)
    database.commit()
    database.refresh(db_genre)


    if genre_data.book_2:
        for id in genre_data.book_2:
            # Entity already validated before creation
            db_book = database.query(Book).filter(Book.id == id).first()
            # Create the association
            association = categorizedas.insert().values(genre=db_genre.id, book_2=db_book.id)
            database.execute(association)
            database.commit()


    book_ids = database.query(categorizedas.c.book_2).filter(categorizedas.c.genre == db_genre.id).all()
    response_data = {
        "genre": db_genre,
        "book_ids": [x[0] for x in book_ids],
    }
    return response_data


@app.post("/genre/bulk/", response_model=None, tags=["Genre"])
async def bulk_create_genre(items: list[GenreCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Genre entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_genre = Genre(
                genreId=item_data.genreId,                name=item_data.name            )
            database.add(db_genre)
            database.flush()  # Get ID without committing
            created_items.append(db_genre.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Genre entities"
    }


@app.delete("/genre/bulk/", response_model=None, tags=["Genre"])
async def bulk_delete_genre(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Genre entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_genre = database.query(Genre).filter(Genre.id == item_id).first()
        if db_genre:
            database.delete(db_genre)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Genre entities"
    }

@app.put("/genre/{genre_id}/", response_model=None, tags=["Genre"])
async def update_genre(genre_id: int, genre_data: GenreCreate, database: Session = Depends(get_db)) -> Genre:
    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    setattr(db_genre, 'genreId', genre_data.genreId)
    setattr(db_genre, 'name', genre_data.name)
    existing_book_ids = [assoc.book_2 for assoc in database.execute(
        categorizedas.select().where(categorizedas.c.genre == db_genre.id))]

    books_to_remove = set(existing_book_ids) - set(genre_data.book_2)
    for book_id in books_to_remove:
        association = categorizedas.delete().where(
            (categorizedas.c.genre == db_genre.id) & (categorizedas.c.book_2 == book_id))
        database.execute(association)

    new_book_ids = set(genre_data.book_2) - set(existing_book_ids)
    for book_id in new_book_ids:
        db_book = database.query(Book).filter(Book.id == book_id).first()
        if db_book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        association = categorizedas.insert().values(book_2=db_book.id, genre=db_genre.id)
        database.execute(association)
    database.commit()
    database.refresh(db_genre)

    book_ids = database.query(categorizedas.c.book_2).filter(categorizedas.c.genre == db_genre.id).all()
    response_data = {
        "genre": db_genre,
        "book_ids": [x[0] for x in book_ids],
    }
    return response_data


@app.delete("/genre/{genre_id}/", response_model=None, tags=["Genre"])
async def delete_genre(genre_id: int, database: Session = Depends(get_db)):
    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    database.delete(db_genre)
    database.commit()
    return db_genre

@app.post("/genre/{genre_id}/book_2/{book_id}/", response_model=None, tags=["Genre Relationships"])
async def add_book_2_to_genre(genre_id: int, book_id: int, database: Session = Depends(get_db)):
    """Add a Book to this Genre's book_2 relationship"""
    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if relationship already exists
    existing = database.query(categorizedas).filter(
        (categorizedas.c.genre == genre_id) &
        (categorizedas.c.book_2 == book_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = categorizedas.insert().values(genre=genre_id, book_2=book_id)
    database.execute(association)
    database.commit()

    return {"message": "Book added to book_2 successfully"}


@app.delete("/genre/{genre_id}/book_2/{book_id}/", response_model=None, tags=["Genre Relationships"])
async def remove_book_2_from_genre(genre_id: int, book_id: int, database: Session = Depends(get_db)):
    """Remove a Book from this Genre's book_2 relationship"""
    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    # Check if relationship exists
    existing = database.query(categorizedas).filter(
        (categorizedas.c.genre == genre_id) &
        (categorizedas.c.book_2 == book_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = categorizedas.delete().where(
        (categorizedas.c.genre == genre_id) &
        (categorizedas.c.book_2 == book_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Book removed from book_2 successfully"}


@app.get("/genre/{genre_id}/book_2/", response_model=None, tags=["Genre Relationships"])
async def get_book_2_of_genre(genre_id: int, database: Session = Depends(get_db)):
    """Get all Book entities related to this Genre through book_2"""
    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    book_ids = database.query(categorizedas.c.book_2).filter(categorizedas.c.genre == genre_id).all()
    book_list = database.query(Book).filter(Book.id.in_([id[0] for id in book_ids])).all()

    return {
        "genre_id": genre_id,
        "book_2_count": len(book_list),
        "book_2": book_list
    }





############################################
#
#   Author functions
#
############################################

@app.get("/author/", response_model=None, tags=["Author"])
def get_all_author(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Author)
        author_list = query.all()

        # Serialize with relationships included
        result = []
        for author_item in author_list:
            item_dict = author_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)

            # Add many-to-many and one-to-many relationship objects (full details)
            book_list = database.query(Book).join(writtenby, Book.id == writtenby.c.book_1).filter(writtenby.c.author == author_item.id).all()
            item_dict['book_1'] = []
            for book_obj in book_list:
                book_dict = book_obj.__dict__.copy()
                book_dict.pop('_sa_instance_state', None)
                item_dict['book_1'].append(book_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Author).all()


@app.get("/author/count/", response_model=None, tags=["Author"])
def get_count_author(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Author entities"""
    count = database.query(Author).count()
    return {"count": count}


@app.get("/author/paginated/", response_model=None, tags=["Author"])
def get_paginated_author(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Author entities"""
    total = database.query(Author).count()
    author_list = database.query(Author).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": author_list
        }

    result = []
    for author_item in author_list:
        book_ids = database.query(writtenby.c.book_1).filter(writtenby.c.author == author_item.id).all()
        item_data = {
            "author": author_item,
            "book_ids": [x[0] for x in book_ids],
        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/author/search/", response_model=None, tags=["Author"])
def search_author(
    database: Session = Depends(get_db)
) -> list:
    """Search Author entities by attributes"""
    query = database.query(Author)


    results = query.all()
    return results


@app.get("/author/{author_id}/", response_model=None, tags=["Author"])
async def get_author(author_id: int, database: Session = Depends(get_db)) -> Author:
    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    book_ids = database.query(writtenby.c.book_1).filter(writtenby.c.author == db_author.id).all()
    response_data = {
        "author": db_author,
        "book_ids": [x[0] for x in book_ids],
}
    return response_data



@app.post("/author/", response_model=None, tags=["Author"])
async def create_author(author_data: AuthorCreate, database: Session = Depends(get_db)) -> Author:

    if not author_data.book_1 or len(author_data.book_1) < 1:
        raise HTTPException(status_code=400, detail="At least 1 Book(s) required")
    if author_data.book_1:
        for id in author_data.book_1:
            # Entity already validated before creation
            db_book = database.query(Book).filter(Book.id == id).first()
            if not db_book:
                raise HTTPException(status_code=404, detail=f"Book with ID {id} not found")

    db_author = Author(
        authorId=author_data.authorId,        name=author_data.name,        biography=author_data.biography        )

    database.add(db_author)
    database.commit()
    database.refresh(db_author)


    if author_data.book_1:
        for id in author_data.book_1:
            # Entity already validated before creation
            db_book = database.query(Book).filter(Book.id == id).first()
            # Create the association
            association = writtenby.insert().values(author=db_author.id, book_1=db_book.id)
            database.execute(association)
            database.commit()


    book_ids = database.query(writtenby.c.book_1).filter(writtenby.c.author == db_author.id).all()
    response_data = {
        "author": db_author,
        "book_ids": [x[0] for x in book_ids],
    }
    return response_data


@app.post("/author/bulk/", response_model=None, tags=["Author"])
async def bulk_create_author(items: list[AuthorCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Author entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item

            db_author = Author(
                authorId=item_data.authorId,                name=item_data.name,                biography=item_data.biography            )
            database.add(db_author)
            database.flush()  # Get ID without committing
            created_items.append(db_author.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Author entities"
    }


@app.delete("/author/bulk/", response_model=None, tags=["Author"])
async def bulk_delete_author(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Author entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_author = database.query(Author).filter(Author.id == item_id).first()
        if db_author:
            database.delete(db_author)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Author entities"
    }

@app.put("/author/{author_id}/", response_model=None, tags=["Author"])
async def update_author(author_id: int, author_data: AuthorCreate, database: Session = Depends(get_db)) -> Author:
    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    setattr(db_author, 'authorId', author_data.authorId)
    setattr(db_author, 'name', author_data.name)
    setattr(db_author, 'biography', author_data.biography)
    existing_book_ids = [assoc.book_1 for assoc in database.execute(
        writtenby.select().where(writtenby.c.author == db_author.id))]

    books_to_remove = set(existing_book_ids) - set(author_data.book_1)
    for book_id in books_to_remove:
        association = writtenby.delete().where(
            (writtenby.c.author == db_author.id) & (writtenby.c.book_1 == book_id))
        database.execute(association)

    new_book_ids = set(author_data.book_1) - set(existing_book_ids)
    for book_id in new_book_ids:
        db_book = database.query(Book).filter(Book.id == book_id).first()
        if db_book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        association = writtenby.insert().values(book_1=db_book.id, author=db_author.id)
        database.execute(association)
    database.commit()
    database.refresh(db_author)

    book_ids = database.query(writtenby.c.book_1).filter(writtenby.c.author == db_author.id).all()
    response_data = {
        "author": db_author,
        "book_ids": [x[0] for x in book_ids],
    }
    return response_data


@app.delete("/author/{author_id}/", response_model=None, tags=["Author"])
async def delete_author(author_id: int, database: Session = Depends(get_db)):
    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    database.delete(db_author)
    database.commit()
    return db_author

@app.post("/author/{author_id}/book_1/{book_id}/", response_model=None, tags=["Author Relationships"])
async def add_book_1_to_author(author_id: int, book_id: int, database: Session = Depends(get_db)):
    """Add a Book to this Author's book_1 relationship"""
    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if relationship already exists
    existing = database.query(writtenby).filter(
        (writtenby.c.author == author_id) &
        (writtenby.c.book_1 == book_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = writtenby.insert().values(author=author_id, book_1=book_id)
    database.execute(association)
    database.commit()

    return {"message": "Book added to book_1 successfully"}


@app.delete("/author/{author_id}/book_1/{book_id}/", response_model=None, tags=["Author Relationships"])
async def remove_book_1_from_author(author_id: int, book_id: int, database: Session = Depends(get_db)):
    """Remove a Book from this Author's book_1 relationship"""
    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    # Check if relationship exists
    existing = database.query(writtenby).filter(
        (writtenby.c.author == author_id) &
        (writtenby.c.book_1 == book_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = writtenby.delete().where(
        (writtenby.c.author == author_id) &
        (writtenby.c.book_1 == book_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Book removed from book_1 successfully"}


@app.get("/author/{author_id}/book_1/", response_model=None, tags=["Author Relationships"])
async def get_book_1_of_author(author_id: int, database: Session = Depends(get_db)):
    """Get all Book entities related to this Author through book_1"""
    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    book_ids = database.query(writtenby.c.book_1).filter(writtenby.c.author == author_id).all()
    book_list = database.query(Book).filter(Book.id.in_([id[0] for id in book_ids])).all()

    return {
        "author_id": author_id,
        "book_1_count": len(book_list),
        "book_1": book_list
    }





############################################
#
#   BookCopy functions
#
############################################

@app.get("/bookcopy/", response_model=None, tags=["BookCopy"])
def get_all_bookcopy(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(BookCopy)
        query = query.options(joinedload(BookCopy.loan_1))
        bookcopy_list = query.all()

        # Serialize with relationships included
        result = []
        for bookcopy_item in bookcopy_list:
            item_dict = bookcopy_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if bookcopy_item.loan_1:
                related_obj = bookcopy_item.loan_1
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['loan_1'] = related_dict
            else:
                item_dict['loan_1'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            book_list = database.query(Book).filter(Book.bookcopy_id == bookcopy_item.id).all()
            item_dict['book'] = []
            for book_obj in book_list:
                book_dict = book_obj.__dict__.copy()
                book_dict.pop('_sa_instance_state', None)
                item_dict['book'].append(book_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(BookCopy).all()


@app.get("/bookcopy/count/", response_model=None, tags=["BookCopy"])
def get_count_bookcopy(database: Session = Depends(get_db)) -> dict:
    """Get the total count of BookCopy entities"""
    count = database.query(BookCopy).count()
    return {"count": count}


@app.get("/bookcopy/paginated/", response_model=None, tags=["BookCopy"])
def get_paginated_bookcopy(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of BookCopy entities"""
    total = database.query(BookCopy).count()
    bookcopy_list = database.query(BookCopy).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": bookcopy_list
        }

    result = []
    for bookcopy_item in bookcopy_list:
        book_ids = database.query(Book.id).filter(Book.bookcopy_id == bookcopy_item.id).all()
        item_data = {
            "bookcopy": bookcopy_item,
            "book_ids": [x[0] for x in book_ids]        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/bookcopy/search/", response_model=None, tags=["BookCopy"])
def search_bookcopy(
    database: Session = Depends(get_db)
) -> list:
    """Search BookCopy entities by attributes"""
    query = database.query(BookCopy)


    results = query.all()
    return results


@app.get("/bookcopy/{bookcopy_id}/", response_model=None, tags=["BookCopy"])
async def get_bookcopy(bookcopy_id: int, database: Session = Depends(get_db)) -> BookCopy:
    db_bookcopy = database.query(BookCopy).filter(BookCopy.id == bookcopy_id).first()
    if db_bookcopy is None:
        raise HTTPException(status_code=404, detail="BookCopy not found")

    book_ids = database.query(Book.id).filter(Book.bookcopy_id == db_bookcopy.id).all()
    response_data = {
        "bookcopy": db_bookcopy,
        "book_ids": [x[0] for x in book_ids]}
    return response_data



@app.post("/bookcopy/", response_model=None, tags=["BookCopy"])
async def create_bookcopy(bookcopy_data: BookCopyCreate, database: Session = Depends(get_db)) -> BookCopy:

    if bookcopy_data.loan_1 is not None:
        db_loan_1 = database.query(Loan).filter(Loan.id == bookcopy_data.loan_1).first()
        if not db_loan_1:
            raise HTTPException(status_code=400, detail="Loan not found")
    else:
        raise HTTPException(status_code=400, detail="Loan ID is required")

    db_bookcopy = BookCopy(
        copyId=bookcopy_data.copyId,        status=bookcopy_data.status,        loan_1_id=bookcopy_data.loan_1        )

    database.add(db_bookcopy)
    database.commit()
    database.refresh(db_bookcopy)

    if bookcopy_data.book:
        # Validate that all Book IDs exist
        for book_id in bookcopy_data.book:
            db_book = database.query(Book).filter(Book.id == book_id).first()
            if not db_book:
                raise HTTPException(status_code=400, detail=f"Book with id {book_id} not found")

        # Update the related entities with the new foreign key
        database.query(Book).filter(Book.id.in_(bookcopy_data.book)).update(
            {Book.bookcopy_id: db_bookcopy.id}, synchronize_session=False
        )
        database.commit()



    book_ids = database.query(Book.id).filter(Book.bookcopy_id == db_bookcopy.id).all()
    response_data = {
        "bookcopy": db_bookcopy,
        "book_ids": [x[0] for x in book_ids]    }
    return response_data


@app.post("/bookcopy/bulk/", response_model=None, tags=["BookCopy"])
async def bulk_create_bookcopy(items: list[BookCopyCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple BookCopy entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.loan_1:
                raise ValueError("Loan ID is required")

            db_bookcopy = BookCopy(
                copyId=item_data.copyId,                status=item_data.status,                loan_1_id=item_data.loan_1            )
            database.add(db_bookcopy)
            database.flush()  # Get ID without committing
            created_items.append(db_bookcopy.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} BookCopy entities"
    }


@app.delete("/bookcopy/bulk/", response_model=None, tags=["BookCopy"])
async def bulk_delete_bookcopy(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple BookCopy entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_bookcopy = database.query(BookCopy).filter(BookCopy.id == item_id).first()
        if db_bookcopy:
            database.delete(db_bookcopy)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} BookCopy entities"
    }

@app.put("/bookcopy/{bookcopy_id}/", response_model=None, tags=["BookCopy"])
async def update_bookcopy(bookcopy_id: int, bookcopy_data: BookCopyCreate, database: Session = Depends(get_db)) -> BookCopy:
    db_bookcopy = database.query(BookCopy).filter(BookCopy.id == bookcopy_id).first()
    if db_bookcopy is None:
        raise HTTPException(status_code=404, detail="BookCopy not found")

    setattr(db_bookcopy, 'copyId', bookcopy_data.copyId)
    setattr(db_bookcopy, 'status', bookcopy_data.status)
    if bookcopy_data.loan_1 is not None:
        db_loan_1 = database.query(Loan).filter(Loan.id == bookcopy_data.loan_1).first()
        if not db_loan_1:
            raise HTTPException(status_code=400, detail="Loan not found")
        setattr(db_bookcopy, 'loan_1_id', bookcopy_data.loan_1)
    if bookcopy_data.book is not None:
        # Clear all existing relationships (set foreign key to NULL)
        database.query(Book).filter(Book.bookcopy_id == db_bookcopy.id).update(
            {Book.bookcopy_id: None}, synchronize_session=False
        )

        # Set new relationships if list is not empty
        if bookcopy_data.book:
            # Validate that all IDs exist
            for book_id in bookcopy_data.book:
                db_book = database.query(Book).filter(Book.id == book_id).first()
                if not db_book:
                    raise HTTPException(status_code=400, detail=f"Book with id {book_id} not found")

            # Update the related entities with the new foreign key
            database.query(Book).filter(Book.id.in_(bookcopy_data.book)).update(
                {Book.bookcopy_id: db_bookcopy.id}, synchronize_session=False
            )
    database.commit()
    database.refresh(db_bookcopy)

    book_ids = database.query(Book.id).filter(Book.bookcopy_id == db_bookcopy.id).all()
    response_data = {
        "bookcopy": db_bookcopy,
        "book_ids": [x[0] for x in book_ids]    }
    return response_data


@app.delete("/bookcopy/{bookcopy_id}/", response_model=None, tags=["BookCopy"])
async def delete_bookcopy(bookcopy_id: int, database: Session = Depends(get_db)):
    db_bookcopy = database.query(BookCopy).filter(BookCopy.id == bookcopy_id).first()
    if db_bookcopy is None:
        raise HTTPException(status_code=404, detail="BookCopy not found")
    database.delete(db_bookcopy)
    database.commit()
    return db_bookcopy





############################################
#
#   Member functions
#
############################################

@app.get("/member/", response_model=None, tags=["Member"])
def get_all_member(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Member)
        query = query.options(joinedload(Member.loan))
        query = query.options(joinedload(Member.reservation))
        member_list = query.all()

        # Serialize with relationships included
        result = []
        for member_item in member_list:
            item_dict = member_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if member_item.loan:
                related_obj = member_item.loan
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['loan'] = related_dict
            else:
                item_dict['loan'] = None
            if member_item.reservation:
                related_obj = member_item.reservation
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['reservation'] = related_dict
            else:
                item_dict['reservation'] = None


            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Member).all()


@app.get("/member/count/", response_model=None, tags=["Member"])
def get_count_member(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Member entities"""
    count = database.query(Member).count()
    return {"count": count}


@app.get("/member/paginated/", response_model=None, tags=["Member"])
def get_paginated_member(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Member entities"""
    total = database.query(Member).count()
    member_list = database.query(Member).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": member_list
    }


@app.get("/member/search/", response_model=None, tags=["Member"])
def search_member(
    database: Session = Depends(get_db)
) -> list:
    """Search Member entities by attributes"""
    query = database.query(Member)


    results = query.all()
    return results


@app.get("/member/{member_id}/", response_model=None, tags=["Member"])
async def get_member(member_id: int, database: Session = Depends(get_db)) -> Member:
    db_member = database.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    response_data = {
        "member": db_member,
}
    return response_data



@app.post("/member/", response_model=None, tags=["Member"])
async def create_member(member_data: MemberCreate, database: Session = Depends(get_db)) -> Member:

    if member_data.loan is not None:
        db_loan = database.query(Loan).filter(Loan.id == member_data.loan).first()
        if not db_loan:
            raise HTTPException(status_code=400, detail="Loan not found")
    else:
        raise HTTPException(status_code=400, detail="Loan ID is required")
    if member_data.reservation is not None:
        db_reservation = database.query(Reservation).filter(Reservation.id == member_data.reservation).first()
        if not db_reservation:
            raise HTTPException(status_code=400, detail="Reservation not found")
    else:
        raise HTTPException(status_code=400, detail="Reservation ID is required")

    db_member = Member(
        joinDate=member_data.joinDate,        memberId=member_data.memberId,        email=member_data.email,        name=member_data.name,        loan_id=member_data.loan,        reservation_id=member_data.reservation        )

    database.add(db_member)
    database.commit()
    database.refresh(db_member)




    return db_member


@app.post("/member/bulk/", response_model=None, tags=["Member"])
async def bulk_create_member(items: list[MemberCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Member entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.loan:
                raise ValueError("Loan ID is required")
            if not item_data.reservation:
                raise ValueError("Reservation ID is required")

            db_member = Member(
                joinDate=item_data.joinDate,                memberId=item_data.memberId,                email=item_data.email,                name=item_data.name,                loan_id=item_data.loan,                reservation_id=item_data.reservation            )
            database.add(db_member)
            database.flush()  # Get ID without committing
            created_items.append(db_member.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Member entities"
    }


@app.delete("/member/bulk/", response_model=None, tags=["Member"])
async def bulk_delete_member(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Member entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_member = database.query(Member).filter(Member.id == item_id).first()
        if db_member:
            database.delete(db_member)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Member entities"
    }

@app.put("/member/{member_id}/", response_model=None, tags=["Member"])
async def update_member(member_id: int, member_data: MemberCreate, database: Session = Depends(get_db)) -> Member:
    db_member = database.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    setattr(db_member, 'joinDate', member_data.joinDate)
    setattr(db_member, 'memberId', member_data.memberId)
    setattr(db_member, 'email', member_data.email)
    setattr(db_member, 'name', member_data.name)
    if member_data.loan is not None:
        db_loan = database.query(Loan).filter(Loan.id == member_data.loan).first()
        if not db_loan:
            raise HTTPException(status_code=400, detail="Loan not found")
        setattr(db_member, 'loan_id', member_data.loan)
    if member_data.reservation is not None:
        db_reservation = database.query(Reservation).filter(Reservation.id == member_data.reservation).first()
        if not db_reservation:
            raise HTTPException(status_code=400, detail="Reservation not found")
        setattr(db_member, 'reservation_id', member_data.reservation)
    database.commit()
    database.refresh(db_member)

    return db_member


@app.delete("/member/{member_id}/", response_model=None, tags=["Member"])
async def delete_member(member_id: int, database: Session = Depends(get_db)):
    db_member = database.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    database.delete(db_member)
    database.commit()
    return db_member





############################################
#
#   Book functions
#
############################################

@app.get("/book/", response_model=None, tags=["Book"])
def get_all_book(detailed: bool = False, database: Session = Depends(get_db)) -> list:
    from sqlalchemy.orm import joinedload

    # Use detailed=true to get entities with eagerly loaded relationships (for tables with lookup columns)
    if detailed:
        # Eagerly load all relationships to avoid N+1 queries
        query = database.query(Book)
        query = query.options(joinedload(Book.reservation_1))
        query = query.options(joinedload(Book.bookcopy))
        book_list = query.all()

        # Serialize with relationships included
        result = []
        for book_item in book_list:
            item_dict = book_item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)

            # Add many-to-one relationships (foreign keys for lookup columns)
            if book_item.reservation_1:
                related_obj = book_item.reservation_1
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['reservation_1'] = related_dict
            else:
                item_dict['reservation_1'] = None
            if book_item.bookcopy:
                related_obj = book_item.bookcopy
                related_dict = related_obj.__dict__.copy()
                related_dict.pop('_sa_instance_state', None)
                item_dict['bookcopy'] = related_dict
            else:
                item_dict['bookcopy'] = None

            # Add many-to-many and one-to-many relationship objects (full details)
            author_list = database.query(Author).join(writtenby, Author.id == writtenby.c.author).filter(writtenby.c.book_1 == book_item.id).all()
            item_dict['author'] = []
            for author_obj in author_list:
                author_dict = author_obj.__dict__.copy()
                author_dict.pop('_sa_instance_state', None)
                item_dict['author'].append(author_dict)
            genre_list = database.query(Genre).join(categorizedas, Genre.id == categorizedas.c.genre).filter(categorizedas.c.book_2 == book_item.id).all()
            item_dict['genre'] = []
            for genre_obj in genre_list:
                genre_dict = genre_obj.__dict__.copy()
                genre_dict.pop('_sa_instance_state', None)
                item_dict['genre'].append(genre_dict)

            result.append(item_dict)
        return result
    else:
        # Default: return flat entities (faster for charts/widgets without lookup columns)
        return database.query(Book).all()


@app.get("/book/count/", response_model=None, tags=["Book"])
def get_count_book(database: Session = Depends(get_db)) -> dict:
    """Get the total count of Book entities"""
    count = database.query(Book).count()
    return {"count": count}


@app.get("/book/paginated/", response_model=None, tags=["Book"])
def get_paginated_book(skip: int = 0, limit: int = 100, detailed: bool = False, database: Session = Depends(get_db)) -> dict:
    """Get paginated list of Book entities"""
    total = database.query(Book).count()
    book_list = database.query(Book).offset(skip).limit(limit).all()
    # By default, return flat entities (for charts/widgets)
    # Use detailed=true to get entities with relationships
    if not detailed:
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": book_list
        }

    result = []
    for book_item in book_list:
        author_ids = database.query(writtenby.c.author).filter(writtenby.c.book_1 == book_item.id).all()
        genre_ids = database.query(categorizedas.c.genre).filter(categorizedas.c.book_2 == book_item.id).all()
        item_data = {
            "book": book_item,
            "author_ids": [x[0] for x in author_ids],
            "genre_ids": [x[0] for x in genre_ids],
        }
        result.append(item_data)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@app.get("/book/search/", response_model=None, tags=["Book"])
def search_book(
    database: Session = Depends(get_db)
) -> list:
    """Search Book entities by attributes"""
    query = database.query(Book)


    results = query.all()
    return results


@app.get("/book/{book_id}/", response_model=None, tags=["Book"])
async def get_book(book_id: int, database: Session = Depends(get_db)) -> Book:
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    author_ids = database.query(writtenby.c.author).filter(writtenby.c.book_1 == db_book.id).all()
    genre_ids = database.query(categorizedas.c.genre).filter(categorizedas.c.book_2 == db_book.id).all()
    response_data = {
        "book": db_book,
        "author_ids": [x[0] for x in author_ids],
        "genre_ids": [x[0] for x in genre_ids],
}
    return response_data



@app.post("/book/", response_model=None, tags=["Book"])
async def create_book(book_data: BookCreate, database: Session = Depends(get_db)) -> Book:

    if book_data.reservation_1 is not None:
        db_reservation_1 = database.query(Reservation).filter(Reservation.id == book_data.reservation_1).first()
        if not db_reservation_1:
            raise HTTPException(status_code=400, detail="Reservation not found")
    else:
        raise HTTPException(status_code=400, detail="Reservation ID is required")
    if book_data.bookcopy is not None:
        db_bookcopy = database.query(BookCopy).filter(BookCopy.id == book_data.bookcopy).first()
        if not db_bookcopy:
            raise HTTPException(status_code=400, detail="BookCopy not found")
    else:
        raise HTTPException(status_code=400, detail="BookCopy ID is required")
    if not book_data.author or len(book_data.author) < 1:
        raise HTTPException(status_code=400, detail="At least 1 Author(s) required")
    if book_data.author:
        for id in book_data.author:
            # Entity already validated before creation
            db_author = database.query(Author).filter(Author.id == id).first()
            if not db_author:
                raise HTTPException(status_code=404, detail=f"Author with ID {id} not found")
    if book_data.genre:
        for id in book_data.genre:
            # Entity already validated before creation
            db_genre = database.query(Genre).filter(Genre.id == id).first()
            if not db_genre:
                raise HTTPException(status_code=404, detail=f"Genre with ID {id} not found")

    db_book = Book(
        publicationDate=book_data.publicationDate,        summary=book_data.summary,        title=book_data.title,        isbn=book_data.isbn,        reservation_1_id=book_data.reservation_1,        bookcopy_id=book_data.bookcopy        )

    database.add(db_book)
    database.commit()
    database.refresh(db_book)


    if book_data.author:
        for id in book_data.author:
            # Entity already validated before creation
            db_author = database.query(Author).filter(Author.id == id).first()
            # Create the association
            association = writtenby.insert().values(book_1=db_book.id, author=db_author.id)
            database.execute(association)
            database.commit()
    if book_data.genre:
        for id in book_data.genre:
            # Entity already validated before creation
            db_genre = database.query(Genre).filter(Genre.id == id).first()
            # Create the association
            association = categorizedas.insert().values(book_2=db_book.id, genre=db_genre.id)
            database.execute(association)
            database.commit()


    author_ids = database.query(writtenby.c.author).filter(writtenby.c.book_1 == db_book.id).all()
    genre_ids = database.query(categorizedas.c.genre).filter(categorizedas.c.book_2 == db_book.id).all()
    response_data = {
        "book": db_book,
        "author_ids": [x[0] for x in author_ids],
        "genre_ids": [x[0] for x in genre_ids],
    }
    return response_data


@app.post("/book/bulk/", response_model=None, tags=["Book"])
async def bulk_create_book(items: list[BookCreate], database: Session = Depends(get_db)) -> dict:
    """Create multiple Book entities at once"""
    created_items = []
    errors = []

    for idx, item_data in enumerate(items):
        try:
            # Basic validation for each item
            if not item_data.reservation_1:
                raise ValueError("Reservation ID is required")
            if not item_data.bookcopy:
                raise ValueError("BookCopy ID is required")

            db_book = Book(
                publicationDate=item_data.publicationDate,                summary=item_data.summary,                title=item_data.title,                isbn=item_data.isbn,                reservation_1_id=item_data.reservation_1,                bookcopy_id=item_data.bookcopy            )
            database.add(db_book)
            database.flush()  # Get ID without committing
            created_items.append(db_book.id)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        database.rollback()
        raise HTTPException(status_code=400, detail={"message": "Bulk creation failed", "errors": errors})

    database.commit()
    return {
        "created_count": len(created_items),
        "created_ids": created_items,
        "message": f"Successfully created {len(created_items)} Book entities"
    }


@app.delete("/book/bulk/", response_model=None, tags=["Book"])
async def bulk_delete_book(ids: list[int], database: Session = Depends(get_db)) -> dict:
    """Delete multiple Book entities at once"""
    deleted_count = 0
    not_found = []

    for item_id in ids:
        db_book = database.query(Book).filter(Book.id == item_id).first()
        if db_book:
            database.delete(db_book)
            deleted_count += 1
        else:
            not_found.append(item_id)

    database.commit()

    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Successfully deleted {deleted_count} Book entities"
    }

@app.put("/book/{book_id}/", response_model=None, tags=["Book"])
async def update_book(book_id: int, book_data: BookCreate, database: Session = Depends(get_db)) -> Book:
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    setattr(db_book, 'publicationDate', book_data.publicationDate)
    setattr(db_book, 'summary', book_data.summary)
    setattr(db_book, 'title', book_data.title)
    setattr(db_book, 'isbn', book_data.isbn)
    if book_data.reservation_1 is not None:
        db_reservation_1 = database.query(Reservation).filter(Reservation.id == book_data.reservation_1).first()
        if not db_reservation_1:
            raise HTTPException(status_code=400, detail="Reservation not found")
        setattr(db_book, 'reservation_1_id', book_data.reservation_1)
    if book_data.bookcopy is not None:
        db_bookcopy = database.query(BookCopy).filter(BookCopy.id == book_data.bookcopy).first()
        if not db_bookcopy:
            raise HTTPException(status_code=400, detail="BookCopy not found")
        setattr(db_book, 'bookcopy_id', book_data.bookcopy)
    existing_author_ids = [assoc.author for assoc in database.execute(
        writtenby.select().where(writtenby.c.book_1 == db_book.id))]

    authors_to_remove = set(existing_author_ids) - set(book_data.author)
    for author_id in authors_to_remove:
        association = writtenby.delete().where(
            (writtenby.c.book_1 == db_book.id) & (writtenby.c.author == author_id))
        database.execute(association)

    new_author_ids = set(book_data.author) - set(existing_author_ids)
    for author_id in new_author_ids:
        db_author = database.query(Author).filter(Author.id == author_id).first()
        if db_author is None:
            raise HTTPException(status_code=404, detail=f"Author with ID {author_id} not found")
        association = writtenby.insert().values(author=db_author.id, book_1=db_book.id)
        database.execute(association)
    existing_genre_ids = [assoc.genre for assoc in database.execute(
        categorizedas.select().where(categorizedas.c.book_2 == db_book.id))]

    genres_to_remove = set(existing_genre_ids) - set(book_data.genre)
    for genre_id in genres_to_remove:
        association = categorizedas.delete().where(
            (categorizedas.c.book_2 == db_book.id) & (categorizedas.c.genre == genre_id))
        database.execute(association)

    new_genre_ids = set(book_data.genre) - set(existing_genre_ids)
    for genre_id in new_genre_ids:
        db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
        if db_genre is None:
            raise HTTPException(status_code=404, detail=f"Genre with ID {genre_id} not found")
        association = categorizedas.insert().values(genre=db_genre.id, book_2=db_book.id)
        database.execute(association)
    database.commit()
    database.refresh(db_book)

    author_ids = database.query(writtenby.c.author).filter(writtenby.c.book_1 == db_book.id).all()
    genre_ids = database.query(categorizedas.c.genre).filter(categorizedas.c.book_2 == db_book.id).all()
    response_data = {
        "book": db_book,
        "author_ids": [x[0] for x in author_ids],
        "genre_ids": [x[0] for x in genre_ids],
    }
    return response_data


@app.delete("/book/{book_id}/", response_model=None, tags=["Book"])
async def delete_book(book_id: int, database: Session = Depends(get_db)):
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    database.delete(db_book)
    database.commit()
    return db_book

@app.post("/book/{book_id}/author/{author_id}/", response_model=None, tags=["Book Relationships"])
async def add_author_to_book(book_id: int, author_id: int, database: Session = Depends(get_db)):
    """Add a Author to this Book's author relationship"""
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db_author = database.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    # Check if relationship already exists
    existing = database.query(writtenby).filter(
        (writtenby.c.book_1 == book_id) &
        (writtenby.c.author == author_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = writtenby.insert().values(book_1=book_id, author=author_id)
    database.execute(association)
    database.commit()

    return {"message": "Author added to author successfully"}


@app.delete("/book/{book_id}/author/{author_id}/", response_model=None, tags=["Book Relationships"])
async def remove_author_from_book(book_id: int, author_id: int, database: Session = Depends(get_db)):
    """Remove a Author from this Book's author relationship"""
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if relationship exists
    existing = database.query(writtenby).filter(
        (writtenby.c.book_1 == book_id) &
        (writtenby.c.author == author_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = writtenby.delete().where(
        (writtenby.c.book_1 == book_id) &
        (writtenby.c.author == author_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Author removed from author successfully"}


@app.get("/book/{book_id}/author/", response_model=None, tags=["Book Relationships"])
async def get_author_of_book(book_id: int, database: Session = Depends(get_db)):
    """Get all Author entities related to this Book through author"""
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    author_ids = database.query(writtenby.c.author).filter(writtenby.c.book_1 == book_id).all()
    author_list = database.query(Author).filter(Author.id.in_([id[0] for id in author_ids])).all()

    return {
        "book_id": book_id,
        "author_count": len(author_list),
        "author": author_list
    }

@app.post("/book/{book_id}/genre/{genre_id}/", response_model=None, tags=["Book Relationships"])
async def add_genre_to_book(book_id: int, genre_id: int, database: Session = Depends(get_db)):
    """Add a Genre to this Book's genre relationship"""
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db_genre = database.query(Genre).filter(Genre.id == genre_id).first()
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    # Check if relationship already exists
    existing = database.query(categorizedas).filter(
        (categorizedas.c.book_2 == book_id) &
        (categorizedas.c.genre == genre_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")

    # Create the association
    association = categorizedas.insert().values(book_2=book_id, genre=genre_id)
    database.execute(association)
    database.commit()

    return {"message": "Genre added to genre successfully"}


@app.delete("/book/{book_id}/genre/{genre_id}/", response_model=None, tags=["Book Relationships"])
async def remove_genre_from_book(book_id: int, genre_id: int, database: Session = Depends(get_db)):
    """Remove a Genre from this Book's genre relationship"""
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if relationship exists
    existing = database.query(categorizedas).filter(
        (categorizedas.c.book_2 == book_id) &
        (categorizedas.c.genre == genre_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Delete the association
    association = categorizedas.delete().where(
        (categorizedas.c.book_2 == book_id) &
        (categorizedas.c.genre == genre_id)
    )
    database.execute(association)
    database.commit()

    return {"message": "Genre removed from genre successfully"}


@app.get("/book/{book_id}/genre/", response_model=None, tags=["Book Relationships"])
async def get_genre_of_book(book_id: int, database: Session = Depends(get_db)):
    """Get all Genre entities related to this Book through genre"""
    db_book = database.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    genre_ids = database.query(categorizedas.c.genre).filter(categorizedas.c.book_2 == book_id).all()
    genre_list = database.query(Genre).filter(Genre.id.in_([id[0] for id in genre_ids])).all()

    return {
        "book_id": book_id,
        "genre_count": len(genre_list),
        "genre": genre_list
    }







############################################
# Maintaining the server
############################################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



