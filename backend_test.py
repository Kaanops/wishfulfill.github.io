
import requests
import sys
import uuid
import json
from datetime import datetime

class WishFulfillAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_wish_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_endpoint(self):
        """Test the health endpoint"""
        success, response = self.run_test(
            "Health Endpoint",
            "GET",
            "api/health",
            200
        )
        if success:
            print(f"Health response: {response}")
        return success

    def test_create_wish(self):
        """Test creating a new wish"""
        test_wish = {
            "title": f"Test Wish {uuid.uuid4()}",
            "description": "This is a test wish created by the automated test script",
            "amount_needed": 100.0,
            "currency": "USD",
            "creator_name": "Test User",
            "creator_email": "test@example.com",
            "creator_paypal": "paypal@example.com"
        }
        
        success, response = self.run_test(
            "Create Wish",
            "POST",
            "api/wishes",
            200,  # FastAPI returns 200 for successful POST with response_model
            data=test_wish
        )
        
        if success and 'id' in response:
            self.created_wish_id = response['id']
            print(f"Created wish with ID: {self.created_wish_id}")
        return success

    def test_get_wishes(self):
        """Test getting all wishes"""
        success, response = self.run_test(
            "Get All Wishes",
            "GET",
            "api/wishes",
            200
        )
        
        if success:
            print(f"Retrieved {len(response)} wishes")
        return success

    def test_get_wish_by_id(self):
        """Test getting a specific wish by ID"""
        if not self.created_wish_id:
            print("❌ Cannot test get wish by ID - no wish was created")
            return False
            
        success, response = self.run_test(
            "Get Wish by ID",
            "GET",
            f"api/wishes/{self.created_wish_id}",
            200
        )
        
        if success:
            print(f"Retrieved wish: {response['title']}")
        return success

    def test_donate_to_wish(self):
        """Test donating to a wish"""
        if not self.created_wish_id:
            print("❌ Cannot test donation - no wish was created")
            return False
            
        success, response = self.run_test(
            "Donate to Wish",
            "PUT",
            f"api/wishes/{self.created_wish_id}/donate?amount=25.0",
            200
        )
        
        if success:
            print(f"Donation response: {response}")
        return success

def main():
    # Get the backend URL from the frontend .env file
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.strip().split('=')[1].strip('"')
                    break
    except Exception as e:
        print(f"Error reading backend URL: {str(e)}")
        backend_url = "https://b5580f13-8de8-465c-a78b-9a74e3d8cac9.preview.emergentagent.com"

    print(f"Using backend URL: {backend_url}")
    
    # Setup
    tester = WishFulfillAPITester(backend_url)
    
    # Run tests
    health_ok = tester.test_health_endpoint()
    if not health_ok:
        print("❌ Health check failed, stopping tests")
        return 1
        
    create_ok = tester.test_create_wish()
    get_all_ok = tester.test_get_wishes()
    get_one_ok = tester.test_get_wish_by_id()
    donate_ok = tester.test_donate_to_wish()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("✅ All backend API tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
