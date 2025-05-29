from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
from flask import render_template  
from neo4j import GraphDatabase

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="Library_Management",
    user="postgres",
    password="",  
    host="localhost",
    port="5432"
)
cur = conn.cursor()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)

# -------------------- ROUTES -------------------- #

@app.route('/')
def home():
    return render_template('index.html')

# -------------------- BOOK ROUTES -------------------- #

@app.route('/books', methods=['GET'])
def get_books():
    cur.execute("SELECT * FROM book")
    rows = cur.fetchall()
    books = []
    for row in rows:
        books.append({
            'book_id': row[0],
            'title': row[1],
            'author': row[2],
            'genre': row[3],
            'publisher': row[4],
            'quantity': row[5],
            'available': row[6],
            'place': row[7]
        })
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    cur.execute("""
        INSERT INTO book (book_id, title, author, genre, publisher, quantity, available, place)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['book_id'], data['title'], data['author'], data['genre'],
        data['publisher'], data['quantity'], data['available'], data['place']
    ))
    conn.commit()
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    cur.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
    conn.commit()
    return jsonify({'message': f'Book {book_id} deleted successfully'})

# -------------------- BORROWING ROUTES -------------------- #

@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    book_id = data['book_id']
    borrower_email = data['borrower_email']
    start_date = data['start_date']
    return_date = data['return_date']

    # Check if book is available
    cur.execute("SELECT available FROM book WHERE book_id = %s", (book_id,))
    result = cur.fetchone()
    if not result or not result[0]:  # available is FALSE or book doesn't exist
        return jsonify({'error': 'Book not available'}), 400

    # Insert borrow record
    cur.execute("""
        INSERT INTO borrowing (borrower_email, book_id, start_date, return_date, is_it_returned)
        VALUES (%s, %s, %s, %s, %s)
    """, (borrower_email, book_id, start_date, return_date, False))

    # Mark book unavailable
    cur.execute("UPDATE book SET available = FALSE WHERE book_id = %s", (book_id,))
    conn.commit()
    return jsonify({'message': 'Book borrowed successfully'})

@app.route('/return', methods=['POST'])
def return_book():
    data = request.json
    borrower_id = data['borrower_id']
    book_id = data['book_id']

    # Mark as returned
    cur.execute("""
        UPDATE borrowing SET is_it_returned = TRUE WHERE borrower_id = %s
    """, (borrower_id,))

    # Make book available again
    cur.execute("""
        UPDATE book SET available = TRUE WHERE book_id = %s
    """, (book_id,))
    conn.commit()
    return jsonify({'message': 'Book returned successfully'})

# -------------------- BORROWER ROUTES -------------------- #

@app.route('/borrowers', methods=['POST'])
def add_borrower():
    data = request.json
    cur.execute("""
        INSERT INTO borrower (email, password)
        VALUES (%s, %s)
    """, (data['email'], data['password']))
    conn.commit()
    return jsonify({'message': 'Borrower registered successfully'})



# Neo4j connection setup
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))

# -------------------- NEO4J ROUTES -------------------- #

@app.route('/graph/books', methods=['GET'])
def graph_books():
    with neo4j_driver.session() as session:
        result = session.run("MATCH (b:Book) RETURN b")
        books = [dict(record["b"].items()) for record in result]
        return jsonify(books)

@app.route('/graph/borrowed/<email>', methods=['GET'])
def graph_borrowed(email):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (p:Borrower {email: $email})-[:BORROWED]->(b:Book)
            RETURN b
        """, email=email)
        books = [dict(record["b"].items()) for record in result]
        return jsonify(books)

@app.route('/graph/borrow', methods=['POST'])
def graph_borrow_book():
    data = request.json
    with neo4j_driver.session() as session:
        session.run("""
            MATCH (p:Borrower {email: $email}), (b:Book {book_id: $book_id})
            CREATE (p)-[:BORROWED {
                start_date: date($start_date),
                return_date: date($return_date),
                is_it_returned: false
            }]->(b)
        """, email=data["borrower_email"], book_id=data["book_id"],
             start_date=data["start_date"], return_date=data["return_date"])
    return jsonify({'message': 'Borrowed relationship created in graph'})

@app.route('/graph/return', methods=['POST'])
def graph_return_book():
    data = request.json
    with neo4j_driver.session() as session:
        session.run("""
            MATCH (p:Borrower {email: $email})-[r:BORROWED]->(b:Book {book_id: $book_id})
            SET r.is_it_returned = true
        """, email=data["borrower_email"], book_id=data["book_id"])
    return jsonify({'message': 'Book return updated in graph'})


# -------------------- RUN APP -------------------- #

if __name__ == '__main__':
    app.run(debug=True)