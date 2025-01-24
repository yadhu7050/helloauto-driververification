from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

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
        verification_data = request.json
        status = verification_data.get("status")
        remarks = verification_data.get("remarks", {})
        
        if status not in ["approved", "not approved"]:
            return jsonify({"message": "Invalid status value"}), 400

        driver = captains_collection.find_one({"_id": ObjectId(driver_id)})
        if not driver:
            return jsonify({"message": "Driver not found"}), 404

        # Detailed verification update
        update_data = {
            "verificationStatus": status,
            "status": "active" if status == "approved" else "inactive",
            "verificationDetails": {
                "verifiedAt": datetime.utcnow(),
                "verifiedBy": verification_data.get("verifier_id"),
                "remarks": remarks,
                "documentVerification": {
                    "license": remarks.get("license", "verified"),
                    "vehicleRC": remarks.get("vehicleRC", "verified"),
                    "insurance": remarks.get("insurance", "verified"),
                    "address": remarks.get("address", "verified")
                }
            }
        }
        
        captains_collection.update_one(
            {"_id": ObjectId(driver_id)}, 
            {"$set": update_data}
        )

        return jsonify({
            "message": f"Driver verification {status}",
            "verificationDetails": update_data["verificationDetails"]
        }), 200
        
    except Exception as e:
        return jsonify({
            "message": "Error updating verification status", 
            "error": str(e)
        }), 500

@app.route("/api/drivers/verification-status/<driver_id>", methods=["GET"])
def get_verification_status(driver_id):
    try:
        driver = captains_collection.find_one({"_id": ObjectId(driver_id)})
        if not driver:
            return jsonify({"message": "Driver not found"}), 404
            
        verification_info = {
            "driverId": str(driver["_id"]),
            "status": driver.get("verificationStatus"),
            "verificationDetails": driver.get("verificationDetails", {}),
            "driverDetails": {
                "name": driver.get("name"),
                "phone": driver.get("phone"),
                "email": driver.get("email"),
                "license_number": driver.get("license_number"),
                "vehicle_number": driver.get("vehicle_number")
            }
        }
        
        return jsonify(verification_info), 200
        
    except Exception as e:
        return jsonify({
            "message": "Error fetching verification status",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
