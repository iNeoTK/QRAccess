import requests
import sys
import json
from datetime import datetime

class QRAccessAPITester:
    def __init__(self, base_url="https://qraccess-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        details += f" - {error_data['detail']}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return None

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔍 Testing Authentication...")
        
        # Test login with existing admin
        login_data = {
            "email": "admin@test.com",
            "password": "password123"
        }
        
        response = self.run_test("Admin Login", "POST", "auth/login", 200, login_data)
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Token Extraction", True, "Token obtained successfully")
        else:
            self.log_test("Token Extraction", False, "Failed to get token")
            return False

        # Test /auth/me with token
        self.run_test("Get Current Admin", "GET", "auth/me", 200)

        # Test register new admin
        timestamp = datetime.now().strftime("%H%M%S")
        register_data = {
            "nombre": "Test",
            "apellido": "Admin",
            "email": f"test_admin_{timestamp}@test.com",
            "password": "testpass123"
        }
        
        self.run_test("Register New Admin", "POST", "auth/register", 200, register_data)
        
        return True

    def test_personal_crud(self):
        """Test Personal CRUD operations"""
        print("\n🔍 Testing Personal CRUD...")
        
        if not self.token:
            self.log_test("Personal CRUD", False, "No auth token available")
            return

        # Create personal
        timestamp = datetime.now().strftime("%H%M%S")
        personal_data = {
            "nombre": "Juan",
            "apellido": "Pérez",
            "cedula": f"12345{timestamp}",
            "rol": "Docente"
        }
        
        create_response = self.run_test("Create Personal", "POST", "personal", 200, personal_data)
        if not create_response:
            return

        personal_id = create_response.get('id')
        if not personal_id:
            self.log_test("Personal ID Extraction", False, "No ID in response")
            return

        # Get all personal
        self.run_test("Get All Personal", "GET", "personal", 200)

        # Get specific personal
        self.run_test("Get Personal by ID", "GET", f"personal/{personal_id}", 200)

        # Update personal
        update_data = {
            "nombre": "Juan Carlos",
            "rol": "Director"
        }
        self.run_test("Update Personal", "PUT", f"personal/{personal_id}", 200, update_data)

        # Delete personal
        self.run_test("Delete Personal", "DELETE", f"personal/{personal_id}", 200)

        # Test duplicate cedula
        self.run_test("Create Duplicate Cedula", "POST", "personal", 400, personal_data)

    def test_estudiantes_crud(self):
        """Test Estudiantes CRUD operations"""
        print("\n🔍 Testing Estudiantes CRUD...")
        
        if not self.token:
            self.log_test("Estudiantes CRUD", False, "No auth token available")
            return

        # Create estudiante
        timestamp = datetime.now().strftime("%H%M%S")
        estudiante_data = {
            "nombre": "María",
            "apellido": "González",
            "cedula": f"98765{timestamp}",
            "ano": 3,
            "seccion": "A"
        }
        
        create_response = self.run_test("Create Estudiante", "POST", "estudiantes", 200, estudiante_data)
        if not create_response:
            return

        estudiante_id = create_response.get('id')
        if not estudiante_id:
            self.log_test("Estudiante ID Extraction", False, "No ID in response")
            return

        # Get all estudiantes
        self.run_test("Get All Estudiantes", "GET", "estudiantes", 200)

        # Get specific estudiante
        self.run_test("Get Estudiante by ID", "GET", f"estudiantes/{estudiante_id}", 200)

        # Update estudiante
        update_data = {
            "ano": 4,
            "seccion": "B"
        }
        self.run_test("Update Estudiante", "PUT", f"estudiantes/{estudiante_id}", 200, update_data)

        # Delete estudiante
        self.run_test("Delete Estudiante", "DELETE", f"estudiantes/{estudiante_id}", 200)

    def test_asistencia_system(self):
        """Test attendance system"""
        print("\n🔍 Testing Asistencia System...")
        
        # First create a person to register attendance for
        timestamp = datetime.now().strftime("%H%M%S")
        personal_data = {
            "nombre": "Test",
            "apellido": "Asistencia",
            "cedula": f"11111{timestamp}",
            "rol": "Administrativo"
        }
        
        create_response = self.run_test("Create Person for Attendance", "POST", "personal", 200, personal_data)
        if not create_response:
            return

        cedula = personal_data['cedula']

        # Register attendance (no auth required)
        asistencia_data = {"cedula": cedula}
        self.run_test("Register Attendance", "POST", "asistencia", 200, asistencia_data)

        # Get today's attendances (no auth required)
        self.run_test("Get Today's Attendances", "GET", "asistencias/hoy", 200)

        # Get attendances with auth
        if self.token:
            today = datetime.now().strftime("%Y-%m-%d")
            self.run_test("Get Attendances by Date", "GET", f"asistencias?fecha={today}", 200)

        # Test attendance for non-existent person
        fake_data = {"cedula": "99999999"}
        self.run_test("Register Attendance - Invalid Cedula", "POST", "asistencia", 404, fake_data)

        # Clean up - delete the test person
        if self.token and create_response:
            personal_id = create_response.get('id')
            if personal_id:
                self.run_test("Cleanup Test Person", "DELETE", f"personal/{personal_id}", 200)

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        print("\n🔍 Testing Stats Endpoint...")
        
        if not self.token:
            self.log_test("Stats Endpoint", False, "No auth token available")
            return

        self.run_test("Get Stats", "GET", "stats", 200)

    def test_qr_code_generation(self):
        """Test QR code generation"""
        print("\n🔍 Testing QR Code Generation...")
        
        if not self.token:
            self.log_test("QR Code Generation", False, "No auth token available")
            return

        # Create a person and check if QR code is generated
        timestamp = datetime.now().strftime("%H%M%S")
        personal_data = {
            "nombre": "QR",
            "apellido": "Test",
            "cedula": f"77777{timestamp}",
            "rol": "Obrero"
        }
        
        create_response = self.run_test("Create Person for QR Test", "POST", "personal", 200, personal_data)
        if create_response and 'qr_code' in create_response:
            self.log_test("QR Code Generated", True, "QR code present in response")
            
            # Clean up
            personal_id = create_response.get('id')
            if personal_id:
                self.run_test("Cleanup QR Test Person", "DELETE", f"personal/{personal_id}", 200)
        else:
            self.log_test("QR Code Generated", False, "No QR code in response")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting QR Access Control API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)

        self.test_health_check()
        
        if self.test_authentication():
            self.test_personal_crud()
            self.test_estudiantes_crud()
            self.test_asistencia_system()
            self.test_stats_endpoint()
            self.test_qr_code_generation()
        else:
            print("❌ Authentication failed - skipping authenticated tests")

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")

        return self.tests_passed == self.tests_run

def main():
    tester = QRAccessAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())