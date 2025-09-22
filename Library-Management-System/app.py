from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId
import cv2
from pyzbar.pyzbar import decode

# Flask app
app = Flask(__name__)

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017/LibraryDB"
client = MongoClient(MONGO_URI)
db = client["LibraryDB"]
book_collection = db["BookTable"]
location_collection = db["LocationTable"]

# Barcode Scanner Function
def scan_barcode():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)  # Set width
    cap.set(4, 480)  # Set height

    print("Scanning for barcode... Press 'q' to quit.")
    barcode_data = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not grab frame from webcam.")
            break

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            print(f"Found barcode: {barcode_data}")
            cap.release()
            cv2.destroyAllWindows()
            return barcode_data

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return barcode_data


# Routes

@app.route("/")
def home():
    return render_template("index.html")


# API for barcode scanning
@app.route("/scan", methods=["GET"])
def scan():
    try:
        barcode = scan_barcode()
        if not barcode:
            return jsonify({"error": "No barcode detected!"}), 400
        return jsonify({"barcode": barcode}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Add Book API
@app.route("/books/add", methods=["POST"])
def add_book():
    try:
        data = request.json
        barcode = data.get("Barcode")

        if not barcode:
            return jsonify({"error": "No barcode provided!"}), 400

        existing_book = book_collection.find_one({"BookBarcode": barcode})
        if existing_book:
            return jsonify({"message": "Book already exists in the system"}), 400

        # Add new book entry
        book = {
            "BookBarcode": barcode,
            "BookName": data.get("BookName"),
            "Author": data.get("Author"),
            "PublishedDate": data.get("PublishedDate"),
            "Genre": data.get("Genre", ""),
            "Quantity": None,  # Set quantity as null initially
            "Location": None,  # No location assigned initially
        }
        result = book_collection.insert_one(book)
        return jsonify({"message": "Book added successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete Book API
@app.route("/books/delete", methods=["POST"])
def delete_book():
    try:
        data = request.json
        barcode = data.get("Barcode")
        if not barcode:
            return jsonify({"error": "No barcode provided!"}), 400

        result = book_collection.delete_one({"BookBarcode": barcode})
        if result.deleted_count == 0:
            return jsonify({"error": "No matching book found!"}), 404

        return jsonify({"message": "Book deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Modify Book API
@app.route("/books/modify", methods=["PUT"])
def modify_book():
    try:
        data = request.json
        barcode = data.get("Barcode")
        if not barcode:
            return jsonify({"error": "No barcode provided!"}), 400

        existing_book = book_collection.find_one({"BookBarcode": barcode})
        if not existing_book:
            return jsonify({"error": "No matching book found!"}), 404

        update_fields = {
            key: data[key]
            for key in data
            if key in ["BookName", "Author", "PublishedDate", "Genre"]
        }
        book_collection.update_one({"BookBarcode": barcode}, {"$set": update_fields})

        return jsonify({"message": "Book updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Retrieve Book API
@app.route("/books/retrieve", methods=["POST"])
def retrieve_book():
    try:
        data = request.json
        barcode = data.get("Barcode")
        if not barcode:
            return jsonify({"error": "No barcode provided!"}), 400

        book = book_collection.find_one({"BookBarcode": barcode})
        if not book:
            return jsonify({"error": "No matching book found!"}), 404

        return jsonify({
            "BookName": book["BookName"],
            "Author": book["Author"],
            "PublishedDate": book["PublishedDate"],
            "Genre": book.get("Genre", "N/A"),
            "Quantity": book["Quantity"] if book["Quantity"] is not None else "Not Set",
            "Location": book.get("Location", "Not Assigned"),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Rack Book API
@app.route("/location/rack", methods=["POST"])
def rack_book():
    try:
        data = request.json
        location_barcode = data.get("LocationBarcode")
        book_barcode = data.get("BookBarcode")
        quantity = data.get("Quantity")

        if not location_barcode or not book_barcode or quantity is None:
            return jsonify({"error": "Location barcode, book barcode, or quantity missing!"}), 400

        # Update location table
        location = {
            "LocationBarcode": location_barcode,
            "BookBarcode": book_barcode,
            "Quantity": quantity  # Store the quantity of the book at the location
        }
        location_collection.insert_one(location)

        # Update book table (set or update quantity in the book table)
        book_collection.update_one(
            {"BookBarcode": book_barcode},
            {"$set": {"Location": location_barcode, "Quantity": quantity}}
        )

        return jsonify({"message": "Book racked successfully with quantity!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Book Lending API
@app.route("/books/lend", methods=["POST"])
def lend_book():
    try:
        data = request.json
        barcode = data.get("Barcode")
        if not barcode:
            return jsonify({"error": "No barcode provided!"}), 400

        # Find the book and check its quantity
        book = book_collection.find_one({"BookBarcode": barcode})
        if not book or book["Quantity"] is None or book["Quantity"] <= 0:
            return jsonify({"error": "Book not available for lending!"}), 404

        # Decrement the quantity
        book_collection.update_one({"BookBarcode": barcode}, {"$inc": {"Quantity": -1}})

        return jsonify({"message": "Book lent successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
