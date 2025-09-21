#!/usr/bin/env python3
"""
CI/CD test script that doesn't require API keys
"""

import sys
import os

def test_imports():
    try:
        import gradio as gr
        import pytesseract
        import openai
        import numpy as np
        from PIL import Image
        print("All external dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def test_gradio_import():
    try:
        import gradio as gr
        print("Gradio imported successfully")
        return True
    except Exception as e:
        print(f"Gradio import error: {e}")
        return False

def main():
    print("Running CI/CD tests...")
    print("=" * 50)
    
    tests = [
        ("External Dependencies", test_imports),
        ("Gradio Import", test_gradio_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"{test_name} test failed")
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
