from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__, template_folder="../templates")

MONGO_URI = os.environ.get("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client['bookdb']
books_col = db.books


def serialize_book(book):
    """Convert MongoDB document to JSON-serializable dict."""
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "author": book["author"],
        "genre": book.get("genre", ""),
        "year": book.get("year"),
    }


# ── Frontend ──────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ── REST API ──────────────────────────────────────────────────────────


@app.route("/api/books", methods=["GET"])
def get_books():
    books = books_col.find().sort("_id", -1)
    return jsonify([serialize_book(b) for b in books])


@app.route("/api/books/<book_id>", methods=["GET"])
def get_book(book_id):
    if not ObjectId.is_valid(book_id):
        return jsonify({"error": "Book not found"}), 404
    book = books_col.find_one({"_id": ObjectId(book_id)})
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(serialize_book(book))


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

    doc = {"title": title, "author": author, "genre": genre, "year": year}
    result = books_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(serialize_book(doc)), 201


@app.route("/api/books/<book_id>", methods=["PUT"])
def update_book(book_id):
    if not ObjectId.is_valid(book_id):
        return jsonify({"error": "Book not found"}), 404

    existing = books_col.find_one({"_id": ObjectId(book_id)})
    if existing is None:
        return jsonify({"error": "Book not found"}), 404

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

    books_col.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"title": title, "author": author, "genre": genre, "year": year}},
    )
    updated = books_col.find_one({"_id": ObjectId(book_id)})
    return jsonify(serialize_book(updated))


@app.route("/api/books/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    if not ObjectId.is_valid(book_id):
        return jsonify({"error": "Book not found"}), 404

    result = books_col.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"message": "Book deleted successfully"})
