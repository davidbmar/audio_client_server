#!/usr/bin/python3
#File: TEST_all_commands_via_apigateway.py#
import requests
import time
import json
import sys

BASE_URL = "https://siykieed1e.execute-api.us-east-2.amazonaws.com/dev"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkZPQ2I2bkFpVTU0b3JINjZCaE5QNSJ9.eyJpc3MiOiJodHRwczovL2Rldi1vbnozZXc2anBoMTdvc3psLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJIS0NBc2d6T3Q3VU1MZDlTTnl2Y2VMTjhvaXhFb3R4R0BjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly93d3cuZGF2aWRibWFyLmNvbSIsImlhdCI6MTcyMDM4NzA1MCwiZXhwIjoxNzIwNDczNDUwLCJzY29wZSI6InJlYWQ6YWRtaW4tbWVzc2FnZXMgcmVhZDpwcm90ZWN0ZWQtbWVzc2FnZXMiLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJhenAiOiJIS0NBc2d6T3Q3VU1MZDlTTnl2Y2VMTjhvaXhFb3R4RyIsInBlcm1pc3Npb25zIjpbInJlYWQ6YWRtaW4tbWVzc2FnZXMiLCJyZWFkOnByb3RlY3RlZC1tZXNzYWdlcyJdfQ.iJw3DzqD8kKGmYozSHmPIPxT7BlvVh4VjcEt7YBwLrDv8DgKi3pW5nEBzAbzopQiDMI_F3V-qeQpXlPFbxOG4W2OcrdyliYZ4sRVS1OkmyEuhUdJOFCte5BXeheAzucUw6uOHdc0GKS10rPMR9V8cKJ4_QpYYnCJ6BlEEIRmAxsbnpq3grreBHv0Hk_S6tPbZmq74wpkbZ9G1K8mPA7IK0BWfnjbvLr9fM2e59FK9tIqi5BbHVeJjNqTnIeiKvU52GgPdeovL-R2OtSuil7JS1AolD9zmY1uWedisTliYkUDmXxONXg0cYBS1W7oDclCwQaO9eQy6MK6F_6X_yKVYg"
MAX_WAIT_TIME = 300  # 5 minutes
POLL_INTERVAL = 10  # 10 seconds
TEST_DELAY = 20  # 12 seconds delay between tests

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f"Next test in: {timer}", end='\r')
        time.sleep(1)
        t -= 1
    print("\nProceeding to next test...")

def wait_for_pod_status(pod_id, desired_status, max_wait_time=MAX_WAIT_TIME):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    start_time = time.time()
    print(f"Waiting for pod {pod_id} to reach status: {desired_status}")
    while time.time() - start_time < max_wait_time:
        print(f"Checking pod status... (Elapsed time: {time.time() - start_time:.2f}s)")
        response = requests.get(f"{BASE_URL}/pods/{pod_id}", headers=headers)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            pod_data = response.json()
            current_status = pod_data.get("status", "Unknown")
            desired_status_from_api = pod_data.get("desiredStatus", "Unknown")
            print(f"Current pod status: {current_status}")
            print(f"Desired pod status: {desired_status_from_api}")
            print(f"Full pod data: {json.dumps(pod_data, indent=2)}")
            if current_status == desired_status or desired_status_from_api == desired_status:
                print(f"Pod {pod_id} reached desired status: {desired_status}")
                return True
            if desired_status in ["STOPPED", "TERMINATED"] and desired_status_from_api == "EXITED":
                print(f"Pod {pod_id} is EXITED, which is equivalent to {desired_status}")
                return True
        elif response.status_code == 404:
            print(f"Pod {pod_id} not found")
            if desired_status == "TERMINATED":
                print(f"Pod {pod_id} is not found, which likely means it's TERMINATED")
                return True
            return False
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text}")
        time.sleep(POLL_INTERVAL)
    print(f"Timeout reached. Pod {pod_id} did not reach status {desired_status} within {MAX_WAIT_TIME} seconds")
    return False

def test_list_pods():
    print("\n--- Testing List Pods ---")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    print(f"Sending GET request to {BASE_URL}/pods")
    response = requests.get(f"{BASE_URL}/pods", headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, f"Failed to list pods. Status code: {response.status_code}"
    return response.json()

def test_create_pod():
    print("\n--- Testing Create Pod ---")
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {
        "name": "test-pod",
        "image": "ubuntu:latest",
        "gpu_type": "NVIDIA GeForce RTX 3070"
    }
    print(f"Sending POST request to {BASE_URL}/pods")
    response = requests.post(f"{BASE_URL}/pods", headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, f"Failed to create pod. Status code: {response.status_code}"
    pod_data = response.json()
    pod_id = pod_data["pod"]["id"]
    print(f"Created pod with ID: {pod_id}")
    assert wait_for_pod_status(pod_id, "RUNNING"), f"Pod {pod_id} did not reach RUNNING status"
    return pod_id

def test_stop_pod(pod_id):
    print(f"\n--- Testing Stop Pod {pod_id} ---")
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {"pod_id": pod_id}
    print(f"Sending POST request to {BASE_URL}/pods/stop")
    response = requests.post(f"{BASE_URL}/pods/stop", headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, f"Failed to stop pod. Status code: {response.status_code}"
    assert wait_for_pod_status(pod_id, "STOPPED"), f"Pod {pod_id} did not reach STOPPED status"

def test_delete_pod(pod_id):
    print(f"\n--- Testing Delete Pod {pod_id} ---")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # First, check the current status of the pod
    response = requests.get(f"{BASE_URL}/pods/{pod_id}", headers=headers)
    if response.status_code == 404:
        print(f"Pod {pod_id} not found. It may have already been deleted.")
        return True
    elif response.status_code == 200:
        pod_data = response.json()
        current_status = pod_data.get("desiredStatus", "Unknown")
        print(f"Current pod status: {current_status}")
    
    # Proceed with deletion
    print(f"Sending DELETE request to {BASE_URL}/pods/{pod_id}")
    response = requests.delete(f"{BASE_URL}/pods/{pod_id}", headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code == 200:
        print("Pod deleted successfully")
        return True
    else:
        print(f"Failed to delete pod. Status code: {response.status_code}")
        return False

# Run tests
print("Starting tests...")
try:
    initial_pods = test_list_pods()
    countdown(TEST_DELAY)
    
    pod_id = test_create_pod()
    countdown(TEST_DELAY)
    
    pods_after_create = test_list_pods()
    countdown(TEST_DELAY)
    
    test_stop_pod(pod_id)
    countdown(TEST_DELAY)

    pods_after_stop = test_list_pods()
    countdown(TEST_DELAY)
    
    for pod in pods_after_stop.get('pods', []):
        if pod['name'] == 'test-pod':  # or whatever criteria you use to identify your test pod
            if test_delete_pod(pod['id']):
                print(f"Successfully deleted pod {pod['id']}")
            else:
                print(f"Failed to delete pod {pod['id']}")
    countdown(TEST_DELAY)
    
    final_pods = test_list_pods()

    print("\nAll tests completed successfully!")
    
    print("\nSummary:")
    print(f"Initial pod count: {len(initial_pods['pods'])}")
    print(f"Pod count after creation: {len(pods_after_create['pods'])}")
    print(f"Pod count after stopping: {len(pods_after_stop['pods'])}")
    print(f"Final pod count: {len(final_pods['pods'])}")
    
except AssertionError as e:
    print(f"\nTest failed: {str(e)}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {str(e)}")
