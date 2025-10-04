#!/usr/bin/env python3
"""
Installation script for Legal Lens
Handles dependency conflicts and provides multiple installation options
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_core_packages():
    """Install core packages first"""
    core_packages = [
        "fastapi>=0.100.0,<0.105.0",
        "uvicorn[standard]>=0.20.0,<0.25.0",
        "python-multipart>=0.0.5,<0.1.0",
        "PyPDF2>=3.0.0",
        "docx2txt>=0.8",
        "requests>=2.30.0,<2.32.0"
    ]
    
    for package in core_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def install_ml_packages():
    """Install machine learning packages"""
    ml_packages = [
        "scikit-learn>=1.3.0,<1.4.0",
        "joblib>=1.3.0,<1.4.0",
        "torch>=2.0.0,<2.2.0"
    ]
    
    for package in ml_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def install_nlp_packages():
    """Install NLP packages"""
    nlp_packages = [
        "spacy>=3.6.0,<3.7.0",
        "datasets>=2.14.0,<2.15.0",
        "setfit>=1.0.0,<1.1.0"
    ]
    
    for package in nlp_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def install_utility_packages():
    """Install utility packages"""
    utility_packages = [
        "pyyaml>=6.0.0,<7.0.0",
        "icalendar>=5.0.0,<6.0.0"
    ]
    
    for package in utility_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def download_spacy_model():
    """Download spaCy model"""
    return run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model")

def main():
    print("🚀 Legal Lens Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  No virtual environment detected. Consider using one:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Installation options
    print("\n📦 Installation Options:")
    print("1. Install all packages (recommended)")
    print("2. Install core packages only")
    print("3. Install from requirements-minimal.txt")
    print("4. Skip installation (manual setup)")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\n🔧 Installing all packages...")
        success = (
            install_core_packages() and
            install_ml_packages() and
            install_nlp_packages() and
            install_utility_packages()
        )
    elif choice == "2":
        print("\n🔧 Installing core packages only...")
        success = install_core_packages()
    elif choice == "3":
        print("\n🔧 Installing from requirements-minimal.txt...")
        success = run_command("pip install -r requirements-minimal.txt", "Installing from requirements file")
    elif choice == "4":
        print("\n⏭️  Skipping installation")
        success = True
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    if not success:
        print("\n❌ Installation failed. Try manual installation:")
        print("   pip install -r requirements-minimal.txt")
        sys.exit(1)
    
    # Download spaCy model
    if choice in ["1", "3"]:
        download_spacy_model()
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    os.makedirs("file_queue", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    print("✅ Directories created")
    
    print("\n🎉 Installation completed!")
    print("\n🚀 To start the application:")
    print("   python start.py")
    print("\n🌐 Then open: http://localhost:8000")

if __name__ == "__main__":
    main()
