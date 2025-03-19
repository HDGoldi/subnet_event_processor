from flask import Flask, request, jsonify
import json
import sqlite3
import ipaddress
import requests
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
DATABASE_FILE = "webhook_data.db"
TARGET_EVENT_TYPE_ID = 56
WEBHOOK_ENDPOINT = os.environ.get("WEBHOOK_ENDPOINT", "https://your-webhook-endpoint.com/notify")

def init_db():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create table for storing endpoint data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS endpoint_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sim_iccid TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        subnet TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        UNIQUE(sim_iccid, ip_address)
    )
    ''')
    
    # Create table for tracking known subnets
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS known_subnets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subnet TEXT UNIQUE NOT NULL,
        first_seen TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def calculate_subnet(ip_address):
    """Calculate the /24 subnet for a given IP address"""
    try:
        ip = ipaddress.ip_address(ip_address)
        network = ipaddress.ip_network(f"{ip}/24", strict=False)
        return str(network)
    except ValueError as e:
        logger.error(f"Invalid IP address: {ip_address}, error: {str(e)}")
        return None

def is_new_subnet(subnet):
    """Check if the subnet is new (not previously seen)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM known_subnets WHERE subnet = ?", (subnet,))
    result = cursor.fetchone()[0] == 0
    
    conn.close()
    return result

def register_subnet(subnet):
    """Register a new subnet in the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO known_subnets (subnet, first_seen) VALUES (?, ?)",
        (subnet, datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()
    logger.info(f"New subnet registered: {subnet}")

def store_endpoint_data(sim_iccid, ip_address, subnet):
    """Store the endpoint data in the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO endpoint_data (sim_iccid, ip_address, subnet, timestamp) VALUES (?, ?, ?, ?)",
            (sim_iccid, ip_address, subnet, datetime.now().isoformat())
        )
        conn.commit()
        logger.info(f"Stored endpoint data for SIM {sim_iccid}")
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
    finally:
        conn.close()

def notify_new_subnet(sim_iccid, ip_address, subnet):
    """Send a notification about a new subnet to the configured webhook endpoint"""
    payload = {
        "sim_iccid": sim_iccid,
        "ip_address": ip_address,
        "subnet": subnet,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in (200, 201, 202):
            logger.info(f"Successfully notified about new subnet: {subnet}")
            return True
        else:
            logger.error(f"Failed to notify about new subnet: {subnet}, status: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def process_webhook():
    """Process incoming webhook messages"""
    try:
        data = request.json
        
        # Check if this is the event type we're interested in
        event_type_id = data.get("event_type", {}).get("id")
        if event_type_id != TARGET_EVENT_TYPE_ID:
            logger.info(f"Ignoring event of type {event_type_id}")
            return jsonify({"status": "ignored", "reason": "not target event type"}), 200
        
        # Extract required information
        sim_iccid = data.get("sim", {}).get("iccid", "unknown")
        ip_address = data.get("endpoint", {}).get("ip_address")
        
        if not ip_address:
            logger.warning(f"Missing IP address in webhook data for SIM {sim_iccid}")
            return jsonify({"status": "error", "reason": "missing IP address"}), 400
        
        # Calculate subnet
        subnet = calculate_subnet(ip_address)
        if not subnet:
            return jsonify({"status": "error", "reason": "invalid IP address"}), 400
        
        # Store data in SQLite
        store_endpoint_data(sim_iccid, ip_address, subnet)
        
        # Check if this is a new subnet
        if is_new_subnet(subnet):
            # Register the new subnet
            register_subnet(subnet)
            
            # Send notification about the new subnet
            notify_new_subnet(sim_iccid, ip_address, subnet)
            
            logger.info(f"New subnet detected and notification sent: {subnet}")
            return jsonify({
                "status": "processed", 
                "sim_iccid": sim_iccid,
                "ip_address": ip_address,
                "subnet": subnet,
                "is_new_subnet": True
            }), 200
        else:
            logger.info(f"Processed webhook for existing subnet: {subnet}")
            return jsonify({
                "status": "processed", 
                "sim_iccid": sim_iccid,
                "ip_address": ip_address,
                "subnet": subnet,
                "is_new_subnet": False
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Initialize the database before starting the server
    init_db()
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    
    logger.info(f"Starting webhook processor on port {port}")
    app.run(host="0.0.0.0", port=port)
