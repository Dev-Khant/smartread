#!/usr/bin/env python3
"""
Test script to verify SmartRead improvements
"""

import asyncio
import time
import requests
import json
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_PDF_URL = "https://arxiv.org/pdf/2301.07041.pdf"  # Sample PDF

class SmartReadTester:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.session = requests.Session()
        
    def test_health_check(self) -> Dict[str, Any]:
        """Test basic health check"""
        try:
            response = self.session.get(f"{self.backend_url}/ping")
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_detailed_health(self) -> Dict[str, Any]:
        """Test detailed health check (improved version only)"""
        try:
            response = self.session.get(f"{self.backend_url}/health")
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_pdf_extraction(self, pdf_url: str, page_number: int = 1) -> Dict[str, Any]:
        """Test PDF extraction"""
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.backend_url}/api/extract",
                json={"url": pdf_url, "page_number": page_number},
                timeout=60
            )
            end_time = time.time()
            
            return {
                "status": "pass" if response.status_code in [200, 202] else "fail",
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "details": response.json() if response.status_code in [200, 202] else response.text
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_caching_performance(self, pdf_url: str) -> Dict[str, Any]:
        """Test caching by making the same request twice"""
        # First request (should be slow)
        first_result = self.test_pdf_extraction(pdf_url)
        
        if first_result["status"] != "pass":
            return {"status": "fail", "error": "First request failed"}
        
        # Wait a moment
        time.sleep(2)
        
        # Second request (should be faster with caching)
        second_result = self.test_pdf_extraction(pdf_url)
        
        if second_result["status"] != "pass":
            return {"status": "fail", "error": "Second request failed"}
        
        # Compare response times
        improvement = (first_result["response_time"] - second_result["response_time"]) / first_result["response_time"] * 100
        
        return {
            "status": "pass",
            "first_request_time": first_result["response_time"],
            "second_request_time": second_result["response_time"],
            "improvement_percentage": improvement,
            "caching_effective": improvement > 10  # At least 10% improvement
        }
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting by making multiple rapid requests"""
        try:
            responses = []
            for i in range(15):  # More than the rate limit
                response = self.session.post(
                    f"{self.backend_url}/api/extract",
                    json={"url": TEST_PDF_URL, "page_number": 1}
                )
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay between requests
            
            # Check if any requests were rate limited (429)
            rate_limited = any(code == 429 for code in responses)
            
            return {
                "status": "pass" if rate_limited else "warning",
                "rate_limited_requests": responses.count(429),
                "total_requests": len(responses),
                "details": "Rate limiting is working" if rate_limited else "Rate limiting not detected"
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid input"""
        try:
            # Test with invalid URL
            response = self.session.post(
                f"{self.backend_url}/api/extract",
                json={"url": "invalid-url", "page_number": 1}
            )
            
            return {
                "status": "pass" if response.status_code == 400 else "fail",
                "status_code": response.status_code,
                "error_message": response.json().get("detail", "") if response.status_code == 400 else "No error message",
                "details": "Error handling working correctly" if response.status_code == 400 else "Error handling not working"
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}

def run_tests():
    """Run all tests and display results"""
    print("🧪 SmartRead Improvement Tests")
    print("=" * 50)
    
    tester = SmartReadTester(BACKEND_URL)
    
    tests = [
        ("Basic Health Check", tester.test_health_check),
        ("Detailed Health Check", tester.test_detailed_health),
        ("PDF Extraction", lambda: tester.test_pdf_extraction(TEST_PDF_URL)),
        ("Caching Performance", lambda: tester.test_caching_performance(TEST_PDF_URL)),
        ("Rate Limiting", tester.test_rate_limiting),
        ("Error Handling", tester.test_error_handling),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            
            if result["status"] == "pass":
                print(f"✅ PASSED - {result.get('details', '')}")
                if "response_time" in result:
                    print(f"   Response time: {result['response_time']:.3f}s")
            elif result["status"] == "warning":
                print(f"⚠️  WARNING - {result.get('details', '')}")
            else:
                print(f"❌ FAILED - {result.get('error', result.get('details', ''))}")
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            results[test_name] = {"status": "fail", "error": str(e)}
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r["status"] == "pass")
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    # Detailed results
    print("\n📋 Detailed Results:")
    for test_name, result in results.items():
        status_emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌"}[result["status"]]
        print(f"{status_emoji} {test_name}: {result['status'].upper()}")
        
        if result["status"] == "pass" and test_name == "Caching Performance":
            print(f"   Cache improvement: {result.get('improvement_percentage', 0):.1f}%")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if results.get("Detailed Health Check", {}).get("status") == "fail":
        print("- You're running the original version. Try the improved version with: ./start-backend.sh improved")
    
    if results.get("Caching Performance", {}).get("caching_effective") == False:
        print("- Caching may not be enabled. Check ENABLE_CACHING in .env")
    
    if results.get("Rate Limiting", {}).get("status") == "warning":
        print("- Rate limiting not detected. Check ENABLE_RATE_LIMITING in .env")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    run_tests()
