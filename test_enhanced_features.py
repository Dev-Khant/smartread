#!/usr/bin/env python3
"""
Enhanced test script for SmartRead with Gemini + Tavily integration
"""

import asyncio
import time
import requests
import json
import os
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_PDF_URL = "https://arxiv.org/pdf/2301.07041.pdf"  # Sample PDF

class EnhancedSmartReadTester:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.session = requests.Session()
        
    def test_app_info(self) -> Dict[str, Any]:
        """Test application info endpoint"""
        try:
            response = self.session.get(f"{self.backend_url}/info")
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_enhanced_health_check(self) -> Dict[str, Any]:
        """Test enhanced health check"""
        try:
            response = self.session.get(f"{self.backend_url}/health/enhanced")
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_config_endpoint(self) -> Dict[str, Any]:
        """Test configuration endpoint"""
        try:
            response = self.session.get(f"{self.backend_url}/config")
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_enhanced_extraction(self, pdf_url: str, page_number: int = 1) -> Dict[str, Any]:
        """Test enhanced PDF extraction with Gemini + Tavily"""
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.backend_url}/api/extract",
                json={"url": pdf_url, "page_number": page_number},
                timeout=120  # Increased timeout for Gemini processing
            )
            end_time = time.time()
            
            result = {
                "status": "pass" if response.status_code in [200, 202] else "fail",
                "response_time": end_time - start_time,
                "status_code": response.status_code,
            }
            
            if response.status_code in [200, 202]:
                data = response.json()
                result["details"] = data
                result["processing_method"] = data.get("data", {}).get("processing_method", "unknown")
                result["has_gemini_metadata"] = "gemini_metadata" in data.get("data", {})
                result["has_summary"] = bool(data.get("data", {}).get("summary"))
                result["has_key_topics"] = bool(data.get("data", {}).get("key_topics"))
            else:
                result["details"] = response.text
            
            return result
            
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_enhanced_search(self, query: str, search_type: str = "all") -> Dict[str, Any]:
        """Test enhanced search with Tavily"""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.backend_url}/api/search",
                params={"query": query, "search_type": search_type, "max_results": 3},
                timeout=30
            )
            end_time = time.time()
            
            result = {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": end_time - start_time,
                "status_code": response.status_code,
            }
            
            if response.status_code == 200:
                data = response.json()
                result["details"] = data
                result["has_results"] = len(data.get("results", [])) > 0
                result["has_summary"] = bool(data.get("summary"))
                result["total_results"] = data.get("total_results", 0)
            else:
                result["details"] = response.text
            
            return result
            
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_caching_performance_enhanced(self, pdf_url: str) -> Dict[str, Any]:
        """Test enhanced caching performance"""
        # First request (should be slow)
        first_result = self.test_enhanced_extraction(pdf_url)
        
        if first_result["status"] != "pass":
            return {"status": "fail", "error": "First request failed"}
        
        # Wait a moment
        time.sleep(3)
        
        # Second request (should be faster with caching)
        second_result = self.test_enhanced_extraction(pdf_url)
        
        if second_result["status"] != "pass":
            return {"status": "fail", "error": "Second request failed"}
        
        # Compare response times
        improvement = (first_result["response_time"] - second_result["response_time"]) / first_result["response_time"] * 100
        
        return {
            "status": "pass",
            "first_request_time": first_result["response_time"],
            "second_request_time": second_result["response_time"],
            "improvement_percentage": improvement,
            "caching_effective": improvement > 5,  # At least 5% improvement
            "first_processing_method": first_result.get("processing_method", "unknown"),
            "second_processing_method": second_result.get("processing_method", "unknown")
        }
    
    def test_feature_availability(self) -> Dict[str, Any]:
        """Test which features are available"""
        try:
            config_result = self.test_config_endpoint()
            if config_result["status"] == "pass":
                config = config_result["details"]
                features = config.get("features_enabled", {})
                
                return {
                    "status": "pass",
                    "gemini_available": features.get("gemini", False),
                    "tavily_available": features.get("tavily", False),
                    "mistral_available": features.get("mistral", False),
                    "groq_available": features.get("groq", False),
                    "redis_available": features.get("redis", False),
                    "cloudinary_available": features.get("cloudinary", False),
                    "processing_mode": config.get("processing_mode", "unknown"),
                    "rate_limiting_enabled": config.get("rate_limiting", {}).get("enabled", False)
                }
            else:
                return {"status": "fail", "error": "Could not get config"}
                
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_gemini_specific_features(self, pdf_url: str) -> Dict[str, Any]:
        """Test Gemini-specific features"""
        try:
            result = self.test_enhanced_extraction(pdf_url)
            
            if result["status"] == "pass" and result.get("processing_method") == "gemini_tavily":
                details = result.get("details", {}).get("data", {})
                
                return {
                    "status": "pass",
                    "has_gemini_metadata": bool(details.get("gemini_metadata")),
                    "has_summary": bool(details.get("summary")),
                    "has_key_topics": bool(details.get("key_topics")),
                    "summary_length": len(details.get("summary", "")),
                    "key_topics_count": len(details.get("key_topics", [])),
                    "processing_method": details.get("processing_method")
                }
            else:
                return {
                    "status": "warning",
                    "message": "Gemini processing not used",
                    "actual_method": result.get("processing_method", "unknown")
                }
                
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_tavily_specific_features(self) -> Dict[str, Any]:
        """Test Tavily-specific features"""
        try:
            # Test different search types
            search_tests = [
                ("machine learning", "all"),
                ("artificial intelligence", "articles"),
                ("neural networks tutorial", "videos"),
                ("deep learning research", "academic")
            ]
            
            results = {}
            for query, search_type in search_tests:
                result = self.test_enhanced_search(query, search_type)
                results[f"{search_type}_search"] = {
                    "status": result["status"],
                    "has_results": result.get("has_results", False),
                    "has_summary": result.get("has_summary", False),
                    "response_time": result.get("response_time", 0)
                }
            
            # Overall status
            all_passed = all(r["status"] == "pass" for r in results.values())
            
            return {
                "status": "pass" if all_passed else "partial",
                "search_results": results,
                "total_tests": len(search_tests),
                "passed_tests": sum(1 for r in results.values() if r["status"] == "pass")
            }
            
        except Exception as e:
            return {"status": "fail", "error": str(e)}


def run_enhanced_tests():
    """Run all enhanced tests and display results"""
    print("🧪 SmartRead Enhanced Features Test Suite")
    print("=" * 60)
    
    tester = EnhancedSmartReadTester(BACKEND_URL)
    
    tests = [
        ("Application Info", tester.test_app_info),
        ("Enhanced Health Check", tester.test_enhanced_health_check),
        ("Configuration", tester.test_config_endpoint),
        ("Feature Availability", tester.test_feature_availability),
        ("Enhanced PDF Extraction", lambda: tester.test_enhanced_extraction(TEST_PDF_URL)),
        ("Enhanced Search", lambda: tester.test_enhanced_search("machine learning")),
        ("Caching Performance", lambda: tester.test_caching_performance_enhanced(TEST_PDF_URL)),
        ("Gemini Features", lambda: tester.test_gemini_specific_features(TEST_PDF_URL)),
        ("Tavily Features", tester.test_tavily_specific_features),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            
            if result["status"] == "pass":
                print(f"✅ PASSED")
                if "response_time" in result:
                    print(f"   Response time: {result['response_time']:.3f}s")
                if "processing_method" in result:
                    print(f"   Processing method: {result['processing_method']}")
            elif result["status"] == "warning":
                print(f"⚠️  WARNING - {result.get('message', 'Check details')}")
            elif result["status"] == "partial":
                print(f"🔶 PARTIAL - {result.get('passed_tests', 0)}/{result.get('total_tests', 0)} passed")
            else:
                print(f"❌ FAILED - {result.get('error', result.get('details', ''))}")
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            results[test_name] = {"status": "fail", "error": str(e)}
    
    # Enhanced Summary
    print("\n" + "=" * 60)
    print("📊 Enhanced Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r["status"] == "pass")
    partial = sum(1 for r in results.values() if r["status"] == "partial")
    warning = sum(1 for r in results.values() if r["status"] == "warning")
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"🔶 Partial: {partial}/{total}")
    print(f"⚠️  Warning: {warning}/{total}")
    print(f"📈 Success Rate: {(passed + partial * 0.5)/total*100:.1f}%")
    
    # Feature Analysis
    print("\n🔍 Feature Analysis:")
    feature_result = results.get("Feature Availability", {})
    if feature_result.get("status") == "pass":
        features = feature_result
        print(f"🤖 Gemini: {'✅' if features.get('gemini_available') else '❌'}")
        print(f"🔍 Tavily: {'✅' if features.get('tavily_available') else '❌'}")
        print(f"👁️  Mistral: {'✅' if features.get('mistral_available') else '❌'}")
        print(f"⚡ Groq: {'✅' if features.get('groq_available') else '❌'}")
        print(f"💾 Redis: {'✅' if features.get('redis_available') else '❌'}")
        print(f"☁️  Cloudinary: {'✅' if features.get('cloudinary_available') else '❌'}")
        print(f"🔧 Processing Mode: {features.get('processing_mode', 'unknown')}")
    
    # Performance Analysis
    print("\n⚡ Performance Analysis:")
    cache_result = results.get("Caching Performance", {})
    if cache_result.get("status") == "pass":
        improvement = cache_result.get("improvement_percentage", 0)
        print(f"📈 Cache improvement: {improvement:.1f}%")
        print(f"🚀 Caching effective: {'✅' if cache_result.get('caching_effective') else '❌'}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    # Check if enhanced features are being used
    extraction_result = results.get("Enhanced PDF Extraction", {})
    if extraction_result.get("processing_method") == "gemini_tavily":
        print("✅ Using enhanced processing (Gemini + Tavily)")
    elif extraction_result.get("processing_method") in ["mistral_groq", "async"]:
        print("⚠️  Using legacy processing. Consider adding Gemini + Tavily API keys for enhanced features")
    else:
        print("❓ Processing method unclear. Check API key configuration")
    
    # Check search functionality
    search_result = results.get("Enhanced Search", {})
    if search_result.get("status") == "pass":
        print("✅ Enhanced search working with Tavily")
    else:
        print("⚠️  Enhanced search not working. Check Tavily API key")
    
    # Check caching
    if cache_result.get("caching_effective"):
        print("✅ Caching is working effectively")
    else:
        print("⚠️  Caching not effective. Check Redis configuration")
    
    print("\n🎉 Enhanced testing completed!")
    print("\n📚 Next steps:")
    print("1. Configure missing API keys for full functionality")
    print("2. Test with your own documents")
    print("3. Monitor performance in production")
    print("4. Explore advanced Gemini and Tavily features")


if __name__ == "__main__":
    run_enhanced_tests()
