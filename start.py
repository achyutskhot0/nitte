#!/usr/bin/env python3
"""
Startup script for Legal Lens application
"""
import uvicorn
import os
import sys

def main():
    # Check if we're in the right directory
    if not os.path.exists("glue.py"):
        print("Error: glue.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if required directories exist
    required_dirs = ["frontend", "classifier", "extraction", "summarisers", "nextsteps", "prompts"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"Warning: {dir_name} directory not found. Some features may not work.")
    
    print("Starting Legal Lens application...")
    print("Frontend will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        "glue:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
