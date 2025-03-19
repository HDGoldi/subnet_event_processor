from flask import Flask, request, jsonify
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("notification_receiver.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/notify', methods=['POST'])
def receive_notification():
    """Endpoint to receive notifications about new subnets"""
    data = request.json
    logger.info(f"Received new subnet notification: {json.dumps(data, indent=2)}")
    
    # Store notification in a file for reference
    with open("notifications.json", "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "data": data
        }) + "\n")
    
    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    logger.info("Starting mock notification receiver on port 5001")
    app.run(host="0.0.0.0", port=5001)
