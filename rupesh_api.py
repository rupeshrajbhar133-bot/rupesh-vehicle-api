from flask import Flask, request, jsonify
import json
import os
import re

app = Flask(__name__)
JSON_FILE = "vehicleinfo.json"

def clean_rc(rc_str):
    if not rc_str:
        return ""
    return re.sub(r'[^A-Z0-9]', '', str(rc_str).upper())

print("Loading Vehicle Database into memory...")
vehicle_database = {}

if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8", errors="ignore") as file:
        content = file.read()
        matches = re.findall(r'\{[^{}]+\}', content)
        for item in matches:
            try:
                obj = json.loads(item)
                rc_val = obj.get("rc") or obj.get("registration_number")
                if rc_val:
                    vehicle_database[clean_rc(rc_val)] = obj
            except Exception:
                continue

    print(f"Successfully loaded {len(vehicle_database)} vehicle records!")
else:
    print(f"Error: {JSON_FILE} file not found!")

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Active",
        "api_owner": "Rupesh",
        "total_records": len(vehicle_database),
        "message": "Welcome to Rupesh's Live Vehicle Info API"
    })

@app.route("/rupesh/v1/vehicle", methods=["GET"])
def get_vehicle_info():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "Please provide an 'rc' query parameter"}), 400

    search_key = clean_rc(rc)

    if search_key in vehicle_database:
        return jsonify({
            "status": "success",
            "developer": "Rupesh",
            "result": vehicle_database[search_key]
        })

    return jsonify({
        "error": f"Vehicle RC details not found for '{rc}'"
    }), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
