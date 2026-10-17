#!/usr/bin/env python3

import requests
import sys
import os
from datetime import datetime

class SpeechEnhancementAPITester:
    def __init__(self, base_url="https://speech-clarity-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_file_path = "/tmp/test_noisy.wav"

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=30)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    print(f"   Response: Non-JSON response")
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_upload_audio(self):
        """Test POST /api/upload endpoint"""
        if not os.path.exists(self.test_file_path):
            print(f"❌ Test file not found: {self.test_file_path}")
            return False, {}
        
        with open(self.test_file_path, 'rb') as f:
            files = {'file': ('test_noisy.wav', f, 'audio/wav')}
            success, response = self.run_test("Upload Audio", "POST", "upload", 200, files=files)
            return success, response

    def test_predict_enhancement(self, file_id):
        """Test POST /api/predict/{file_id} endpoint"""
        return self.run_test("Predict Enhancement", "POST", f"predict/{file_id}", 200)

    def test_get_original_audio(self, file_id):
        """Test GET /api/audio/{file_id}/original endpoint"""
        url = f"{self.api_url}/audio/{file_id}/original"
        print(f"\n🔍 Testing Get Original Audio...")
        print(f"   URL: {url}")
        
        self.tests_run += 1
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200 and response.headers.get('content-type') == 'audio/wav':
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_get_enhanced_audio(self, file_id):
        """Test GET /api/audio/{file_id}/enhanced endpoint"""
        url = f"{self.api_url}/audio/{file_id}/enhanced"
        print(f"\n🔍 Testing Get Enhanced Audio...")
        print(f"   URL: {url}")
        
        self.tests_run += 1
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200 and response.headers.get('content-type') == 'audio/wav':
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_download_enhanced(self, file_id):
        """Test GET /api/download/{file_id} endpoint"""
        url = f"{self.api_url}/download/{file_id}"
        print(f"\n🔍 Testing Download Enhanced Audio...")
        print(f"   URL: {url}")
        
        self.tests_run += 1
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200 and response.headers.get('content-type') == 'audio/wav':
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                content_disposition = response.headers.get('content-disposition', '')
                print(f"   Content-Disposition: {content_disposition}")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

def main():
    print("🚀 Starting Speech Enhancement API Tests")
    print("=" * 50)
    
    tester = SpeechEnhancementAPITester()
    
    # Test 1: Root endpoint
    success, _ = tester.test_root_endpoint()
    if not success:
        print("❌ Root endpoint failed, stopping tests")
        return 1

    # Test 2: Upload audio
    success, upload_response = tester.test_upload_audio()
    if not success or 'file_id' not in upload_response:
        print("❌ Upload failed, stopping tests")
        return 1
    
    file_id = upload_response['file_id']
    print(f"\n📁 Using file_id: {file_id}")

    # Test 3: Get original audio (should work after upload)
    if not tester.test_get_original_audio(file_id):
        print("❌ Get original audio failed")

    # Test 4: Predict enhancement
    success, predict_response = tester.test_predict_enhancement(file_id)
    if not success:
        print("❌ Predict enhancement failed")
        return 1

    # Verify predict response has required fields
    required_fields = ['file_id', 'snr', 'si_sdr', 'original_filename', 'enhanced_filename']
    missing_fields = [field for field in required_fields if field not in predict_response]
    if missing_fields:
        print(f"❌ Predict response missing fields: {missing_fields}")
    else:
        print(f"✅ Predict response has all required fields")
        print(f"   SNR: {predict_response.get('snr')} dB")
        print(f"   SI-SDR: {predict_response.get('si_sdr')} dB")

    # Test 5: Get enhanced audio (should work after predict)
    if not tester.test_get_enhanced_audio(file_id):
        print("❌ Get enhanced audio failed")

    # Test 6: Download enhanced audio
    if not tester.test_download_enhanced(file_id):
        print("❌ Download enhanced audio failed")

    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Tests completed: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())