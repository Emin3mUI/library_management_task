-- Insert Sample Books
INSERT INTO book (book_id, title, author, genre, publisher, quantity, available, place) VALUES
('BK001', 'The Great Adventure', 'Jane Smith', 'Fiction', 'Penguin Books', 5, TRUE, 'Shelf A3'),
('BK002', 'Database Fundamentals', 'John Doe', 'Education', 'Tech Press', 3, TRUE, 'Shelf B2'),
('BK003', 'Space Exploration', 'Alice Johnson', 'Science', 'Cosmic Pub', 2, FALSE, 'Shelf C1');

-- Insert Sample Borrowers
INSERT INTO borrower (email, password) VALUES
('user1@library.com', 'password123'),
('user2@library.com', 'securepass456');

-- Insert Sample Borrowing Records
INSERT INTO borrowing (borrower_email, book_id, start_date, return_date, is_it_returned) VALUES
('user1@library.com', 'BK001', '2023-08-01', '2023-08-15', TRUE),
('user2@library.com', 'BK002', '2023-08-10', '2023-08-24', FALSE);