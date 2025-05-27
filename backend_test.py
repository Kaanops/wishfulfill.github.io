
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

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)

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

    def test_statistics_endpoint(self):
        """Test the statistics endpoint"""
        success, response = self.run_test(
            "Statistics Endpoint",
            "GET",
            "api/statistics",
            200
        )
        if success:
            print(f"Statistics response: {response}")
            # Verify the statistics contains all required fields
            required_fields = ['total_wishes', 'fulfilled_wishes', 'total_raised', 'success_rate']
            all_fields_present = all(field in response for field in required_fields)
            if all_fields_present:
                print("✅ All required statistics fields are present")
            else:
                print("❌ Some statistics fields are missing")
                self.tests_passed -= 1
                return False
        return success

    def test_categories_endpoint(self):
        """Test the categories endpoint"""
        success, response = self.run_test(
            "Categories Endpoint",
            "GET",
            "api/categories",
            200
        )
        if success:
            print(f"Categories response: {response}")
            # Verify the categories are returned as expected
            if 'categories' in response and len(response['categories']) > 0:
                print(f"✅ Retrieved {len(response['categories'])} categories")
            else:
                print("❌ No categories found or invalid response format")
                self.tests_passed -= 1
                return False
        return success

    def test_success_stories_endpoint(self):
        """Test the success stories endpoint"""
        success, response = self.run_test(
            "Success Stories Endpoint",
            "GET",
            "api/success-stories",
            200
        )
        if success:
            print(f"Retrieved {len(response)} success stories")
            # Verify we have at least 4 demo success stories
            if len(response) >= 4:
                print("✅ At least 4 success stories found as expected")
                # Check if stories have all required fields
                required_fields = ['id', 'title', 'description', 'amount_fulfilled', 
                                  'donor_count', 'photo_url', 'category']
                sample_story = response[0]
                all_fields_present = all(field in sample_story for field in required_fields)
                if all_fields_present:
                    print("✅ Success story contains all required fields")
                else:
                    print("❌ Some success story fields are missing")
                    self.tests_passed -= 1
                    return False
            else:
                print(f"❌ Expected at least 4 success stories, but found {len(response)}")
                self.tests_passed -= 1
                return False
        return success

    def test_create_wish(self):
        """Test creating a new wish with all new fields"""
        test_wish = {
            "title": f"Test Wish {uuid.uuid4()}",
            "description": "This is a test wish created by the automated test script",
            "amount_needed": 100.0,
            "currency": "USD",
            "creator_name": "Test User",
            "creator_email": "test@example.com",
            "creator_paypal": "paypal@example.com",
            "category": "Education",
            "urgency": "medium",
            "photo_url": "https://images.unsplash.com/photo-1532629345422-7515f3d16bb6"
        }
        
        success, response = self.run_test(
            "Create Wish with New Fields",
            "POST",
            "api/wishes",
            200,  # FastAPI returns 200 for successful POST with response_model
            data=test_wish
        )
        
        if success and 'id' in response:
            self.created_wish_id = response['id']
            print(f"Created wish with ID: {self.created_wish_id}")
            
            # Verify all fields were saved correctly
            for key, value in test_wish.items():
                if key in response and response[key] == value:
                    print(f"✅ Field '{key}' saved correctly")
                else:
                    print(f"❌ Field '{key}' not saved correctly. Expected: {value}, Got: {response.get(key, 'missing')}")
                    self.tests_passed -= 1
                    return False
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

    def test_filter_wishes_by_category(self):
        """Test filtering wishes by category"""
        category = "Education"
        success, response = self.run_test(
            f"Filter Wishes by Category: {category}",
            "GET",
            "api/wishes",
            200,
            params={"category": category}
        )
        
        if success:
            print(f"Retrieved {len(response)} wishes in category '{category}'")
            # Verify all returned wishes have the correct category
            all_correct_category = all(wish['category'] == category for wish in response)
            if all_correct_category or len(response) == 0:
                print(f"✅ All returned wishes have category '{category}'")
            else:
                print(f"❌ Some wishes have incorrect category")
                self.tests_passed -= 1
                return False
        return success

    def test_filter_wishes_by_urgency(self):
        """Test filtering wishes by urgency"""
        urgency = "high"
        success, response = self.run_test(
            f"Filter Wishes by Urgency: {urgency}",
            "GET",
            "api/wishes",
            200,
            params={"urgency": urgency}
        )
        
        if success:
            print(f"Retrieved {len(response)} wishes with urgency '{urgency}'")
            # Verify all returned wishes have the correct urgency
            all_correct_urgency = all(wish['urgency'] == urgency for wish in response)
            if all_correct_urgency or len(response) == 0:
                print(f"✅ All returned wishes have urgency '{urgency}'")
            else:
                print(f"❌ Some wishes have incorrect urgency")
                self.tests_passed -= 1
                return False
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
            # Verify fulfillment_percentage is calculated
            if 'fulfillment_percentage' in response:
                print(f"✅ Fulfillment percentage is calculated: {response['fulfillment_percentage']}%")
            else:
                print("❌ Fulfillment percentage is missing")
                self.tests_passed -= 1
                return False
        return success

    def test_donate_to_wish(self):
        """Test donating to a wish and check progress tracking"""
        if not self.created_wish_id:
            print("❌ Cannot test donation - no wish was created")
            return False
            
        # Get the wish before donation to check initial values
        success, before_wish = self.run_test(
            "Get Wish Before Donation",
            "GET",
            f"api/wishes/{self.created_wish_id}",
            200
        )
        
        if not success:
            return False
            
        initial_percentage = before_wish.get('fulfillment_percentage', 0)
        initial_amount = before_wish.get('donations_received', 0)
        initial_donors = before_wish.get('donor_count', 0)
        
        print(f"Initial state: {initial_percentage}% funded, {initial_amount} received, {initial_donors} donors")
        
        # Make a donation
        donation_amount = 25.0
        success, response = self.run_test(
            f"Donate {donation_amount} to Wish",
            "PUT",
            f"api/wishes/{self.created_wish_id}/donate",
            200,
            params={"amount": donation_amount}
        )
        
        if not success:
            return False
            
        print(f"Donation response: {response}")
        
        # Get the wish after donation to verify progress tracking
        success, after_wish = self.run_test(
            "Get Wish After Donation",
            "GET",
            f"api/wishes/{self.created_wish_id}",
            200
        )
        
        if success:
            new_percentage = after_wish.get('fulfillment_percentage', 0)
            new_amount = after_wish.get('donations_received', 0)
            new_donors = after_wish.get('donor_count', 0)
            
            print(f"After donation: {new_percentage}% funded, {new_amount} received, {new_donors} donors")
            
            # Verify progress tracking
            if new_percentage > initial_percentage:
                print("✅ Fulfillment percentage increased")
            else:
                print("❌ Fulfillment percentage did not increase")
                self.tests_passed -= 1
                return False
                
            if new_amount == initial_amount + donation_amount:
                print("✅ Donation amount was added correctly")
            else:
                print(f"❌ Donation amount was not added correctly. Expected: {initial_amount + donation_amount}, Got: {new_amount}")
                self.tests_passed -= 1
                return False
                
            if new_donors == initial_donors + 1:
                print("✅ Donor count was incremented")
            else:
                print(f"❌ Donor count was not incremented. Expected: {initial_donors + 1}, Got: {new_donors}")
                self.tests_passed -= 1
                return False
        
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
    
    # Test new endpoints
    statistics_ok = tester.test_statistics_endpoint()
    categories_ok = tester.test_categories_endpoint()
    success_stories_ok = tester.test_success_stories_endpoint()
    
    # Test wish creation with new fields
    create_ok = tester.test_create_wish()
    
    # Test filtering
    filter_category_ok = tester.test_filter_wishes_by_category()
    filter_urgency_ok = tester.test_filter_wishes_by_urgency()
    
    # Test basic functionality
    get_all_ok = tester.test_get_wishes()
    get_one_ok = tester.test_get_wish_by_id()
    
    # Test progress tracking
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
