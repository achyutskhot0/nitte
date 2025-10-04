#!/usr/bin/env python3
"""
Simple setup script for Legal Lens
"""
import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Legal Lens Setup")
    print("=" * 30)
    
    # Check if we're in a virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  Warning: Not in a virtual environment")
        print("Consider creating one: python -m venv venv")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Install packages
    print("\n📦 Installing packages...")
    
    # Core packages first
    core_packages = [
        "fastapi",
        "uvicorn[standard]", 
        "python-multipart",
        "PyPDF2",
        "docx2txt",
        "requests"
    ]
    
    for package in core_packages:
        if not run_command(f"pip install {package}"):
            print(f"Failed to install {package}")
            return
    
    # ML packages
    ml_packages = [
        "scikit-learn",
        "joblib", 
        "torch"
    ]
    
    for package in ml_packages:
        if not run_command(f"pip install {package}"):
            print(f"Failed to install {package}")
            return
    
    # NLP packages
    nlp_packages = [
        "spacy",
        "datasets",
        "setfit"
    ]
    
    for package in nlp_packages:
        if not run_command(f"pip install {package}"):
            print(f"Failed to install {package}")
            return
    
    # Utility packages
    utility_packages = [
        "pyyaml",
        "icalendar"
    ]
    
    for package in utility_packages:
        if not run_command(f"pip install {package}"):
            print(f"Failed to install {package}")
            return
    
    # Fix numpy version conflict
    print("\n🔧 Fixing numpy version...")
    run_command("pip install 'numpy<2.0'")
    
    # Download spaCy model
    print("\n📥 Downloading spaCy model...")
    if not run_command("python -m spacy download en_core_web_sm"):
        print("Failed to download spaCy model")
        return
    
    # Create directories
    print("\n📁 Creating directories...")
    os.makedirs("file_queue", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    print("✅ Directories created")
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 To start the application:")
    print("   python start.py")
    print("\n🌐 Then open: http://localhost:8000")

if __name__ == "__main__":
    main()
