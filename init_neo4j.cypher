// Clear all existing data
MATCH (n) DETACH DELETE n;

// Create Book nodes
CREATE (:Book {book_id: "BK001", title: "The Great Adventure", author: "Jane Smith", genre: "Fiction", publisher: "Penguin Books", quantity: 5, available: true, place: "Shelf A3"});
CREATE (:Book {book_id: "BK002", title: "Database Fundamentals", author: "John Doe", genre: "Education", publisher: "Tech Press", quantity: 3, available: true, place: "Shelf B2"});
CREATE (:Book {book_id: "BK003", title: "Space Exploration", author: "Alice Johnson", genre: "Science", publisher: "Cosmic Pub", quantity: 2, available: false, place: "Shelf C1"});

// Create Borrower nodes
CREATE (:Borrower {email: "user1@library.com", password: "password123"});
CREATE (:Borrower {email: "user2@library.com", password: "securepass456"});

// Create BORROWED relationships
MATCH (b1:Borrower {email: "user1@library.com"}), (bk1:Book {book_id: "BK001"})
CREATE (b1)-[:BORROWED {start_date: date("2023-08-01"), return_date: date("2023-08-15"), is_it_returned: true}]->(bk1);

MATCH (b2:Borrower {email: "user2@library.com"}), (bk2:Book {book_id: "BK002"})
CREATE (b2)-[:BORROWED {start_date: date("2023-08-10"), return_date: date("2023-08-24"), is_it_returned: false}]->(bk2);


// Create the graphs
MATCH (n) RETURN n;
MATCH (b:Borrower)-[r:BORROWED]->(bk:Book) RETURN b, r, bk;

// Show graph with relationships
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
