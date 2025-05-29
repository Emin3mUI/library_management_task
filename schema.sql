CREATE TABLE IF NOT EXISTS book (
    book_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    author VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    publisher VARCHAR(100),
    quantity INTEGER NOT NULL,
    available BOOLEAN DEFAULT TRUE,
    place VARCHAR(50)
);


-- Create Borrower Table
CREATE TABLE IF NOT EXISTS borrower (
    email VARCHAR(100) PRIMARY KEY,
    password VARCHAR(100) NOT NULL
);

-- Create Borrowing Table
CREATE TABLE IF NOT EXISTS borrowing (
    borrower_id SERIAL PRIMARY KEY,
    borrower_email VARCHAR(100) REFERENCES Borrower(email) ON DELETE CASCADE,
    book_id VARCHAR(50) REFERENCES Book(book_id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    return_date DATE,
    is_it_returned BOOLEAN DEFAULT FALSE,
    CHECK (return_date >= start_date)
);

