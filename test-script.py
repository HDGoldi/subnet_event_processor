import requests
import json
import time

# Test data based on the provided example
test_data = {
    "imsi": {
        "imsi": "12345678901234",
        "id": 1234567,
        "import_date": "2019-01-21T09:36:17Z"
    },
    "event_source": {
        "description": "API",
        "id": 2
    },
    "organisation": {
        "name": "8100xxxx",
        "id": 1234
    },
    "event_severity": {
        "id": 0,
        "description": "Info"
    },
    "sim": {
        "msisdn": "123456789012",
        "iccid": "89012345678901234567",
        "id": 1234567,
        "production_date": "2019-01-21T09:36:17Z"
    },
    "description": "Data quota got assigned with volume of 500.000000 MB. On exhaustion, the data service will be blocked.",
    "alert": True,
    "id": 1234567890,
    "user": None,
    "endpoint": {
        "tags": None,
        "ip_address": "192.168.1.25",
        "name": "Test Endpoint",
        "imei": "123456789012345",
        "id": 1234567
    },
    "event_type": {
        "id": 56,
        "description": "Data quota assigned"
    },
    "detail": "{\"endpoint_quota_id\":123123, \"quota_status_id\": 1,\"action_on_quota_exhaustion_id\": 1,\"volume\": 500.000000, \"expiry_date\": \"2022-03-31T00:00:00Z\", \"peak_throughput\": 128000,\"last_volume_added\": 500.000000,\"last_status_change_date\": \"2022-03-24T12:46:27Z\", \"auto_refill\": true,\"threshold_percentage\": 20,\"threshold_volume\": 100.000000}",
    "timestamp": "2019-01-21T09:36:17Z"
}

# Test with different event type (should be ignored)
test_data_wrong_event = test_data.copy()
test_data_wrong_event["event_type"]["id"] = 55

# Test with another IP in the same subnet (should not trigger new subnet notification)
test_data_same_subnet = test_data.copy()
test_data_same_subnet["endpoint"]["ip_address"] = "192.168.1.100"

# Test with an IP in a different subnet (should trigger new subnet notification)
test_data_new_subnet = test_data.copy()
test_data_new_subnet["endpoint"]["ip_address"] = "10.0.0.25"

def run_test():
    base_url = "http://localhost:5000"
    
    print("=== Testing Webhook Processor ===")
    
    # Test 1: Send a valid event with event type 56
    print("\n1. Sending valid event with event type 56...")
    response = requests.post(f"{base_url}/webhook", json=test_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    time.sleep(1)
    
    # Test 2: Send an event with wrong event type
    print("\n2. Sending event with wrong event type...")
    response = requests.post(f"{base_url}/webhook", json=test_data_wrong_event)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    time.sleep(1)
    
    # Test 3: Send another event with same subnet
    print("\n3. Sending another event with IP in the same subnet...")
    response = requests.post(f"{base_url}/webhook", json=test_data_same_subnet)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    time.sleep(1)
    
    # Test 4: Send an event with a new subnet
    print("\n4. Sending event with IP in a new subnet...")
    response = requests.post(f"{base_url}/webhook", json=test_data_new_subnet)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: Check the health endpoint
    print("\n5. Checking health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    run_test()
