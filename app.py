from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# replace with MongoDB URI
client = MongoClient("mongodb://localhost:27017/") 
# Replace 'auto_verification' with database name
db = client["auto_verification"]
captains_collection = db["captains"]  # Replace 'captains' with collection name

def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/drivers/pending", methods=["GET"])
def get_pending_verifications():
    try:
        pending_drivers = captains_collection.find({"verificationStatus": "pending"})
        return jsonify([serialize_doc(driver) for driver in pending_drivers]), 200
    except Exception as e:
        return jsonify({"message": "Error fetching pending verifications", "error": str(e)}), 500


@app.route("/api/drivers/verify/<driver_id>", methods=["PUT"])
def update_verification_status(driver_id):
    try:
        status = request.json.get("status")
        if status not in ["approved", "not approved"]:
            return jsonify({"message": "Invalid status value"}), 400

        driver = captains_collection.find_one({"_id": ObjectId(driver_id)})
        if not driver:
            return jsonify({"message": "Driver not found"}), 404

        
        update_data = {
            "verificationStatus": status,
            "status": "active" if status == "approved" else "inactive",
        }
        captains_collection.update_one({"_id": ObjectId(driver_id)}, {"$set": update_data})

        return jsonify({"message": f"Driver verification {status}"}), 200
    except Exception as e:
        return jsonify({"message": "Error updating verification status", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
