from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Connect to MongoDB on localhost
db = client["LibraryDB"]  # Select the database 'LibraryDB'
book_collection = db["BookTable"]  # Select the collection 'BookTable'

# Function to fetch and display all the content from 'BookTable'
def display_content():
    books = book_collection.find()  # Fetch all documents from the 'BookTable'
    
    # Loop through each document and print the content
    for book in books:
        print(book)  # Print the entire document as it is
        print("-" * 40)  # Separator for readability

# Call the function to display content
if __name__ == "__main__":
    display_content()

'''from pymongo import MongoClient
from prettytable import PrettyTable

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/LibraryDB"
client = MongoClient(MONGO_URI)
db = client["LibraryDB"]
location_collection = db["LocationTable"]

def view_location_table():
    try:
        # Fetch all records from the LocationTable collection
        records = list(location_collection.find())  # Convert cursor to a list
        
        # Check if the table has data
        if not records:
            print("No data found in LocationTable.")
            return
        
        # Create a pretty table for displaying data
        table = PrettyTable(["Location Barcode", "Book Barcode"])
        
        # Add records to the table
        for record in records:
            table.add_row([record.get("LocationBarcode", "N/A"), record.get("BookBarcode", "N/A")])
        
        # Print the table
        print(table)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

# Call the function to view data
if __name__ == "__main__":
    view_location_table()'''

