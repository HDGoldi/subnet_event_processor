# Webhook Message Processor

This is a Python application that receives webhook messages in JSON format, processes them, and stores the information in a SQLite database. It specifically handles events with `event_type.id = 56`, extracts endpoint IP address information, calculates the corresponding subnet, and notifies about new subnets.

## Features

- Receives webhook messages via a Flask web server
- Filters for events with event_type ID 56
- Extracts endpoint IP address information
- Calculates the /24 subnet for each IP address
- Stores SIM ICCID, endpoint IP address, and calculated subnet in SQLite
- Tracks known subnets
- Sends notifications when new subnets are detected
- Provides a health check endpoint

## Components

This project includes the following components:

1. **Webhook Processor**: The main application that receives and processes webhook messages
2. **Mock Notification Receiver**: A simple service that receives notifications about new subnets
3. **Test Script**: A script to test the webhook processor with sample data

## Setup

### Option 1: Using Docker Compose (Recommended)

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Run the following command to start all services:
   ```bash
   docker-compose up -d
   ```

### Option 2: Manual Setup

1. Install Python 3.9 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the notification receiver:
   ```bash
   python mock_notification_receiver.py
   ```
4. In a separate terminal, start the webhook processor:
   ```bash
   export WEBHOOK_ENDPOINT=http://localhost:5001/notify
   python webhook_processor.py
   ```

## Usage

The webhook processor listens for HTTP POST requests at `http://localhost:5000/webhook`. Send your JSON webhook messages to this endpoint.

### Running the Test Script

The test script sends example webhook messages to the processor:

```bash
python test_script.py
```

## API Endpoints

### Webhook Processor

- `POST /webhook` - Receives and processes webhook messages
- `GET /health` - Health check endpoint

### Mock Notification Receiver

- `POST /notify` - Receives notifications about new subnets

## Configuration

The webhook processor can be configured using the following environment variables:

- `PORT` - The port to run the webhook processor on (default: 5000)
- `WEBHOOK_ENDPOINT` - The endpoint to send notifications to (default: https://your-webhook-endpoint.com/notify)
- `DATABASE_FILE` - The path to the SQLite database file (default: webhook_data.db)

## Database Schema

The webhook processor uses a SQLite database with the following tables:

### endpoint_data

Stores information about endpoints and their IP addresses.

| Column    | Type   | Description                  |
|-----------|--------|------------------------------|
| id        | INTEGER| Primary key                  |
| sim_iccid | TEXT   | SIM card ICCID               |
| ip_address| TEXT   | Endpoint IP address          |
| subnet    | TEXT   | Calculated /24 subnet        |
| timestamp | TEXT   | Timestamp of data storage    |

### known_subnets

Tracks subnets that have been seen before.

| Column     | Type   | Description                  |
|------------|--------|------------------------------|
| id         | INTEGER| Primary key                  |
| subnet     | TEXT   | Subnet in CIDR notation      |
| first_seen | TEXT   | Timestamp of first detection |

## Notification Format

When a new subnet is detected, the webhook processor sends a notification with the following JSON format:

```json
{
  "sim_iccid": "89012345678901234567",
  "ip_address": "192.168.1.25",
  "subnet": "192.168.1.0/24",
  "timestamp": "2023-03-19T12:34:56.789Z"
}
```