#!/usr/bin/env python3
"""
Test registration error handling
"""

import requests
import json

# Test registration with weak password
def test_registration_error_handling():
    url = "http://localhost:8000/api/users/register"
    
    # Test with weak password
    data = {
        "username": "testuser123",
        "email": "test123@example.com", 
        "password": "weak",  # This should trigger a validation error
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 422:
        error_data = response.json()
        print(f"Error detail type: {type(error_data['detail'])}")
        if isinstance(error_data['detail'], list):
            print(f"First error message: {error_data['detail'][0]['msg']}")
    
    # Test with proper password requirements
    data2 = {
        "username": "testuser456",
        "email": "test456@example.com",
        "password": "StrongPassword123!",  # This should work
        "first_name": "Test",
        "last_name": "User"
    }
    
    response2 = requests.post(url, json=data2)
    print(f"\nSecond test Status Code: {response2.status_code}")
    print(f"Second test Response: {response2.text}")

if __name__ == "__main__":
    test_registration_error_handling()
