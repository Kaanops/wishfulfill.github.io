
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
        self.payment_id = None
        self.transaction_id = None
        self.approval_url = None

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
            # Verify PayPal is mentioned in the health response
            if 'payments' in response and response['payments'] == 'paypal':
                print("✅ PayPal payment service is mentioned in health check")
            else:
                print("❌ PayPal payment service is not mentioned in health check")
                self.tests_passed -= 1
                return False
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
            required_fields = ['total_wishes', 'fulfilled_wishes', 'total_raised', 'success_rate', 'posting_fee']
            all_fields_present = all(field in response for field in required_fields)
            if all_fields_present:
                print("✅ All required statistics fields are present")
                # Verify posting fee is 2.0 EUR
                if response['posting_fee'] == 2.0:
                    print("✅ Posting fee is correctly set to 2.0 EUR")
                else:
                    print(f"❌ Posting fee is not 2.0 EUR, got: {response['posting_fee']}")
                    self.tests_passed -= 1
                    return False
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
            "currency": "EUR",
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
                    
            # Verify payment_status field exists and is set to pending
            if 'payment_status' in response:
                if response['payment_status'] == 'pending':
                    print("✅ Payment status is correctly set to 'pending'")
                else:
                    print(f"❌ Payment status should be 'pending', got: {response['payment_status']}")
                    self.tests_passed -= 1
                    return False
            else:
                print("❌ Payment status field is missing")
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
            # Verify paid_only parameter is working (default should be true)
            all_paid = all(wish.get('payment_status') == 'paid' for wish in response)
            if all_paid or len(response) == 0:
                print("✅ All wishes have 'paid' payment status (paid_only=true by default)")
            else:
                print("❌ Some wishes don't have 'paid' payment status despite paid_only=true")
                self.tests_passed -= 1
                return False
        return success

    def test_get_all_wishes_including_unpaid(self):
        """Test getting all wishes including unpaid ones"""
        success, response = self.run_test(
            "Get All Wishes Including Unpaid",
            "GET",
            "api/wishes",
            200,
            params={"paid_only": "false"}
        )
        
        if success:
            print(f"Retrieved {len(response)} wishes (including unpaid)")
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
                
            # Verify payment_status field exists
            if 'payment_status' in response:
                print(f"✅ Payment status field exists: {response['payment_status']}")
            else:
                print("❌ Payment status field is missing")
                self.tests_passed -= 1
                return False
        return success

    def test_create_posting_fee_payment(self):
        """Test creating a payment for posting fee"""
        if not self.created_wish_id:
            print("❌ Cannot test payment creation - no wish was created")
            return False
            
        payment_data = {
            "amount": 2.0,  # Should be overridden by server to POSTING_FEE
            "currency": "EUR",
            "purpose": "posting_fee",
            "wish_id": self.created_wish_id,
            "return_url": "https://example.com/return",
            "cancel_url": "https://example.com/cancel"
        }
        
        success, response = self.run_test(
            "Create Posting Fee Payment",
            "POST",
            "api/payments/create",
            200,
            data=payment_data
        )
        
        if success:
            # Verify response contains required fields
            required_fields = ['payment_id', 'transaction_id', 'approval_url', 'status']
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print("✅ Payment creation response contains all required fields")
                self.payment_id = response['payment_id']
                self.transaction_id = response['transaction_id']
                self.approval_url = response['approval_url']
                
                print(f"Payment ID: {self.payment_id}")
                print(f"Transaction ID: {self.transaction_id}")
                print(f"Approval URL: {self.approval_url}")
                
                # Verify status is 'created'
                if response['status'] == 'created':
                    print("✅ Payment status is correctly set to 'created'")
                else:
                    print(f"❌ Payment status should be 'created', got: {response['status']}")
                    self.tests_passed -= 1
                    return False
                    
                # Verify approval URL is a PayPal URL
                if 'paypal.com' in self.approval_url:
                    print("✅ Approval URL is a PayPal URL")
                else:
                    print(f"❌ Approval URL is not a PayPal URL: {self.approval_url}")
                    self.tests_passed -= 1
                    return False
            else:
                print("❌ Payment creation response is missing required fields")
                self.tests_passed -= 1
                return False
        return success

    def test_create_donation_payment(self):
        """Test creating a payment for donation"""
        if not self.created_wish_id:
            print("❌ Cannot test donation payment creation - no wish was created")
            return False
            
        payment_data = {
            "amount": 25.0,
            "currency": "EUR",
            "purpose": "donation",
            "wish_id": self.created_wish_id,
            "return_url": "https://example.com/return",
            "cancel_url": "https://example.com/cancel"
        }
        
        success, response = self.run_test(
            "Create Donation Payment",
            "POST",
            "api/payments/create",
            200,
            data=payment_data
        )
        
        if success:
            # Verify response contains required fields
            required_fields = ['payment_id', 'transaction_id', 'approval_url', 'status']
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print("✅ Donation payment creation response contains all required fields")
                donation_payment_id = response['payment_id']
                donation_transaction_id = response['transaction_id']
                
                print(f"Donation Payment ID: {donation_payment_id}")
                print(f"Donation Transaction ID: {donation_transaction_id}")
                
                # Verify status is 'created'
                if response['status'] == 'created':
                    print("✅ Donation payment status is correctly set to 'created'")
                else:
                    print(f"❌ Donation payment status should be 'created', got: {response['status']}")
                    self.tests_passed -= 1
                    return False
            else:
                print("❌ Donation payment creation response is missing required fields")
                self.tests_passed -= 1
                return False
        return success

    def test_get_payment_status(self):
        """Test getting payment status"""
        if not self.payment_id:
            print("❌ Cannot test payment status - no payment was created")
            return False
            
        success, response = self.run_test(
            "Get Payment Status",
            "GET",
            f"api/payments/status/{self.payment_id}",
            200
        )
        
        if success:
            # Verify response contains required fields
            required_fields = ['payment_id', 'transaction_id', 'status', 'amount', 'currency', 'purpose']
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print("✅ Payment status response contains all required fields")
                
                # Verify payment details match what we created
                if response['payment_id'] == self.payment_id:
                    print("✅ Payment ID matches")
                else:
                    print(f"❌ Payment ID mismatch. Expected: {self.payment_id}, Got: {response['payment_id']}")
                    self.tests_passed -= 1
                    return False
                    
                if response['transaction_id'] == self.transaction_id:
                    print("✅ Transaction ID matches")
                else:
                    print(f"❌ Transaction ID mismatch. Expected: {self.transaction_id}, Got: {response['transaction_id']}")
                    self.tests_passed -= 1
                    return False
                    
                if response['purpose'] == 'posting_fee':
                    print("✅ Purpose is correctly set to 'posting_fee'")
                else:
                    print(f"❌ Purpose should be 'posting_fee', got: {response['purpose']}")
                    self.tests_passed -= 1
                    return False
                    
                if response['amount'] == 2.0:
                    print("✅ Amount is correctly set to 2.0")
                else:
                    print(f"❌ Amount should be 2.0, got: {response['amount']}")
                    self.tests_passed -= 1
                    return False
            else:
                print("❌ Payment status response is missing required fields")
                self.tests_passed -= 1
                return False
        return success

    def test_legacy_donate_to_wish(self):
        """Test the legacy donation endpoint (should now redirect to payment system)"""
        if not self.created_wish_id:
            print("❌ Cannot test legacy donation - no wish was created")
            return False
            
        donation_amount = 25.0
        success, response = self.run_test(
            f"Legacy Donate {donation_amount} to Wish",
            "PUT",
            f"api/wishes/{self.created_wish_id}/donate",
            200,
            params={"amount": donation_amount}
        )
        
        if success:
            # Verify response contains redirection to new payment system
            if 'payment_endpoint' in response and response['payment_endpoint'] == '/api/payments/create':
                print("✅ Legacy donation endpoint correctly redirects to new payment system")
            else:
                print("❌ Legacy donation endpoint does not redirect to new payment system")
                self.tests_passed -= 1
                return False
                
            if 'purpose' in response and response['purpose'] == 'donation':
                print("✅ Purpose is correctly set to 'donation'")
            else:
                print(f"❌ Purpose should be 'donation', got: {response.get('purpose', 'missing')}")
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
    
    # Test statistics endpoint with posting fee
    statistics_ok = tester.test_statistics_endpoint()
    if not statistics_ok:
        print("❌ Statistics check failed, stopping tests")
        return 1
    
    # Test other basic endpoints
    categories_ok = tester.test_categories_endpoint()
    success_stories_ok = tester.test_success_stories_endpoint()
    
    # Test wish creation with payment_status field
    create_ok = tester.test_create_wish()
    if not create_ok:
        print("❌ Wish creation failed, stopping payment tests")
        return 1
    
    # Test payment creation for posting fee
    posting_fee_payment_ok = tester.test_create_posting_fee_payment()
    if not posting_fee_payment_ok:
        print("❌ Posting fee payment creation failed")
    
    # Test payment status endpoint
    payment_status_ok = tester.test_get_payment_status()
    
    # Test donation payment creation
    donation_payment_ok = tester.test_create_donation_payment()
    
    # Test legacy donation endpoint
    legacy_donate_ok = tester.test_legacy_donate_to_wish()
    
    # Test wish filtering and retrieval
    get_all_ok = tester.test_get_wishes()
    get_all_unpaid_ok = tester.test_get_all_wishes_including_unpaid()
    filter_category_ok = tester.test_filter_wishes_by_category()
    filter_urgency_ok = tester.test_filter_wishes_by_urgency()
    get_one_ok = tester.test_get_wish_by_id()

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
