from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import logging
from neo4j import GraphDatabase
from datetime import datetime

# ------------ PostgreSQL Connection ------------ #
conn = psycopg2.connect(
    dbname="Library_Management",
    user="postgres",
    password="",  
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# ------------ Neo4j Conn ------------ #
neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "12345678") 
)

# ------------ Flask Setup ------------ #
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# ------------ Routes ------------ #

@app.route('/')
def home():
    return render_template('index.html')

# -- Books ------------------------------------------------

@app.route('/books', methods=['GET'])
def get_books():
    cur.execute("SELECT * FROM book")
    rows = cur.fetchall()
    books = [{
        'book_id':   r[0],
        'title':     r[1],
        'author':    r[2],
        'genre':     r[3],
        'publisher': r[4],
        'quantity':  r[5],
        'available': r[6],
        'place':     r[7]
    } for r in rows]
    return jsonify(books), 200

@app.route('/books', methods=['POST'])
def add_book():
    try:
        data = request.json
        # You can add a quick sanity check:
        required_keys = ['book_id','title','author','genre','publisher','quantity','available','place']
        for key in required_keys:
            if key not in data:
                return jsonify({'error': f'Missing key "{key}" in JSON payload'}), 400

        cur.execute("""
            INSERT INTO book
              (book_id, title, author, genre, publisher, quantity, available, place)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['book_id'],
            data['title'],
            data['author'],
            data['genre'],
            data['publisher'],
            data['quantity'],
            data['available'],
            data['place']
        ))
        conn.commit()
        return jsonify({'message': f'Book {data["book_id"]} added'}), 201

    except psycopg2.IntegrityError as e:
        conn.rollback()
        # e.pgcode / e.pgerror hold the Postgres-specific code/message
        return jsonify({
            'error': 'Database integrity error',
            'details': str(e)
        }), 400

    except Exception as e:
        conn.rollback()
        # For any other unexpected exception, return a JSON payload:
        return jsonify({
            'error': 'Unexpected server error',
            'details': str(e)
        }), 500

@app.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    cur.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
    conn.commit()
    return jsonify({'message': f'Book {book_id} deleted'}), 200

# -- Borrowing --------------------------------------------

@app.route('/borrow', methods=['POST'])
def borrow_book():
    try:
        data = request.json or {}
        # Pull fields out of JSON
        book_id        = data.get('book_id')
        borrower_email = data.get('borrower_email')
        sd             = data.get('start_date')
        rd             = data.get('return_date')

        # 1) Basic validation: make sure the JSON keys exist
        missing = [k for k in ('book_id','borrower_email','start_date','return_date') if k not in data]
        if missing:
            return jsonify({ 'error': f'Missing JSON keys: {", ".join(missing)}' }), 400

        # 2) Parse dates
        try:
            start_date  = datetime.strptime(sd, '%Y-%m-%d').date()
            return_date = datetime.strptime(rd, '%Y-%m-%d').date()
        except Exception:
            return jsonify({ 'error': 'Invalid date format. Use YYYY-MM-DD.' }), 400

        today = datetime.today().date()
        if start_date < today:
            return jsonify({ 'error': 'Cannot borrow in the past' }), 400
        if return_date < start_date:
            return jsonify({ 'error': 'Return date before borrow date' }), 400

        # 3) Check that borrower exists
        cur.execute("SELECT 1 FROM borrower WHERE email = %s", (borrower_email,))
        if cur.fetchone() is None:
            return jsonify({ 'error': f'No borrower with email {borrower_email}' }), 400

        # 4) Check availability
        cur.execute("SELECT available FROM book WHERE book_id = %s", (book_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({ 'error': f'Book {book_id} not found' }), 404
        if not row[0]:
            return jsonify({ 'error': 'Book not available' }), 400

        # 5) Insert borrowing record
        cur.execute("""
            INSERT INTO borrowing
              (borrower_email, book_id, start_date, return_date, is_it_returned)
            VALUES (%s, %s, %s, %s, %s)
        """, (borrower_email, book_id, start_date, return_date, False))

        # 6) Mark book unavailable
        cur.execute("UPDATE book SET available = FALSE WHERE book_id = %s", (book_id,))
        conn.commit()
        return jsonify({ 'message': 'Book borrowed successfully' }), 201

    except Exception as exc:
        # Roll back on any error
        conn.rollback()
        # Log the full stack trace to the Flask console
        app.logger.exception("Unexpected error in /borrow")
        # Return a JSON error payload with the Python exception string
        return jsonify({
            'error': 'Internal server error in /borrow',
            'details': str(exc)
        }), 500


@app.route('/return', methods=['POST'])
def return_book():
    data          = request.json
    book_id       = data.get('book_id')
    return_date_str = data.get('return_date')

    # Parse return date
    try:
        return_dt = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400

    # 1) Find the latest unreturned borrow
    cur.execute("""
        SELECT borrower_id, start_date
          FROM borrowing
         WHERE book_id = %s
           AND is_it_returned = FALSE
         ORDER BY start_date DESC
         LIMIT 1
    """, (book_id,))
    rec = cur.fetchone()
    if not rec:
        return jsonify({'error': 'No active borrow record'}), 400

    borrower_id, start_dt = rec
    if return_dt < start_dt:
        return jsonify({'error': 'Return date before borrow date'}), 400

    # 2) Mark the borrowing returned
    cur.execute("""
        UPDATE borrowing
           SET return_date = %s,
               is_it_returned = TRUE
         WHERE borrower_id = %s
    """, (return_dt, borrower_id))

    # 3) Mark the book available again
    cur.execute("UPDATE book SET available = TRUE WHERE book_id = %s", (book_id,))
    conn.commit()

    return jsonify({'message': 'Book returned successfully'}), 200

# -- Clear All Borrowing Data ----------------------------

from neo4j.exceptions import ServiceUnavailable

@app.route('/clear-borrowings', methods=['POST'])
def clear_borrowings():
    try:
        # 1) Delete all borrowing records from PostgreSQL
        cur.execute("DELETE FROM borrowing;")
        # 2) Reset every book’s available flag
        cur.execute("UPDATE book SET available = TRUE;")
        conn.commit()

        # 3) Try to clear Neo4j relationships, but ignore if Neo4j isn't up
        try:
            with neo4j_driver.session() as session:
                session.run("MATCH ()-[r:BORROWED]->() DELETE r")
        except ServiceUnavailable:
            app.logger.warning("Could not connect to Neo4j—skipping graph cleanup.")

        return jsonify({'message': 'All borrowing data reset'}), 200

    except Exception as e:
        conn.rollback()
        app.logger.exception("Error in clear-borrowings")
        return jsonify({'error': 'Failed to clear borrowings', 'details': str(e)}), 500


# -- Borrowers --------------------------------------------

@app.route('/borrowers', methods=['POST'])
def add_borrower():
    data = request.json
    cur.execute(
        "INSERT INTO borrower (email, password) VALUES (%s, %s)",
        (data.get('email'), data.get('password'))
    )
    conn.commit()
    return jsonify({'message': 'Borrower registered'}), 201

# -- Neo4j Graph  ------------------------------

@app.route('/graph/books', methods=['GET'])
def graph_books():
    with neo4j_driver.session() as session:
        result = session.run("MATCH (b:Book) RETURN b")
        books = [dict(r["b"].items()) for r in result]
    return jsonify(books), 200

@app.route('/graph/borrowed/<email>', methods=['GET'])
def graph_borrowed(email):
    with neo4j_driver.session() as session:
        result = session.run(
            "MATCH (p:Borrower {email:$email})-[:BORROWED]->(b:Book) RETURN b",
            email=email
        )
        books = [dict(r["b"].items()) for r in result]
    return jsonify(books), 200

@app.route('/graph/borrow', methods=['POST'])
def graph_borrow_book():
    data = request.json
    with neo4j_driver.session() as session:
        session.run("""
            MATCH (p:Borrower {email:$email}), (b:Book {book_id:$book_id})
            CREATE (p)-[:BORROWED {
              start_date: date($start_date),
              return_date: date($return_date),
              is_it_returned: false
            }]->(b)
        """, email=data['borrower_email'],
             book_id=data['book_id'],
             start_date=data['start_date'],
             return_date=data['return_date'])
    return jsonify({'message': 'Graph borrow created'}), 201

@app.route('/graph/return', methods=['POST'])
def graph_return_book():
    data = request.json
    with neo4j_driver.session() as session:
        session.run("""
            MATCH (p:Borrower {email:$email})-[r:BORROWED]->(b:Book {book_id:$book_id})
            SET r.is_it_returned = true
        """, email=data['borrower_email'], book_id=data['book_id'])
    return jsonify({'message': 'Graph return updated'}), 200

# ------------ Run the App ------------ #
if __name__ == '__main__':
    app.run(debug=True)
