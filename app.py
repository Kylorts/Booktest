from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "books.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT DEFAULT '',
            year INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


# ── Frontend ──────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ── REST API ──────────────────────────────────────────────────────────


@app.route("/api/books", methods=["GET"])
def get_books():
    conn = get_db()
    books = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(b) for b in books])


@app.route("/api/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(dict(book))


@app.route("/api/books", methods=["POST"])
def create_book():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    genre = (data.get("genre") or "").strip()
    year = data.get("year")

    errors = []
    if not title:
        errors.append("Title is required.")
    if not author:
        errors.append("Author is required.")
    if year is not None and year != "":
        try:
            year = int(year)
            if year < 0 or year > 9999:
                errors.append("Year must be between 0 and 9999.")
        except (ValueError, TypeError):
            errors.append("Year must be a valid number.")
    else:
        year = None

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO books (title, author, genre, year) VALUES (?, ?, ?, ?)",
        (title, author, genre, year),
    )
    conn.commit()
    book_id = cursor.lastrowid
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return jsonify(dict(book)), 201


@app.route("/api/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Book not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        conn.close()
        return jsonify({"error": "Request body must be JSON"}), 400

    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    genre = (data.get("genre") or "").strip()
    year = data.get("year")

    errors = []
    if not title:
        errors.append("Title is required.")
    if not author:
        errors.append("Author is required.")
    if year is not None and year != "":
        try:
            year = int(year)
            if year < 0 or year > 9999:
                errors.append("Year must be between 0 and 9999.")
        except (ValueError, TypeError):
            errors.append("Year must be a valid number.")
    else:
        year = None

    if errors:
        conn.close()
        return jsonify({"error": " ".join(errors)}), 400

    conn.execute(
        "UPDATE books SET title = ?, author = ?, genre = ?, year = ? WHERE id = ?",
        (title, author, genre, year, book_id),
    )
    conn.commit()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return jsonify(dict(book))


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Book deleted successfully"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
