import os
import subprocess
import secrets
import json
from pathlib import Path

def check_existing_directories():
    print("Checking existing directories...")
    required_directories = ["backend/static", "backend/templates", "backend/database", "configs"]
    for directory in required_directories:
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Required directory '{directory}' is missing. Please ensure all directories are correctly set up.")
    print("All required directories are in place!")

def install_dependencies():
    print("Installing system-wide dependencies...")
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "install", "-y", "python3", "python3-pip", "python3-venv", 
                    "nginx", "mariadb-server", "certbot", "unzip", "wget", 
                    "wireguard", "ufw"], check=True)
    print("All system dependencies installed successfully!")

def setup_virtualenv():
    print("Setting up Python virtual environment...")
    if not os.path.exists("venv"):
        subprocess.run(["python3", "-m", "venv", "venv"], check=True)
    subprocess.run(["venv/bin/pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(["venv/bin/pip", "install", "fastapi", "uvicorn", "jinja2", "python-multipart", 
                    "sqlalchemy", "bcrypt", "cryptography"], check=True)
    print("Virtual environment and Python dependencies are set up!")

def generate_requirements_file():
    print("Generating requirements.txt...")
    requirements = [
        "fastapi",
        "uvicorn",
        "jinja2",
        "python-multipart",
        "sqlalchemy",
        "bcrypt",
        "cryptography"
    ]
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    print("requirements.txt generated successfully!")

def ensure_config_files():
    print("Ensuring necessary config files are in place...")
    # Example Xray configuration
    xray_config_path = Path("/etc/xray/config.json")
    if not xray_config_path.exists():
        xray_config = {
            "log": {"loglevel": "warning"},
            "inbounds": [{"port": 443, "protocol": "vmess", "settings": {"clients": []}}],
            "outbounds": [{"protocol": "freedom", "settings": {}}],
        }
        os.makedirs(xray_config_path.parent, exist_ok=True)
        with open(xray_config_path, "w") as f:
            json.dump(xray_config, f)
        print(f"Xray config created at {xray_config_path}")

    # Example WireGuard configuration
    wireguard_config_path = Path("/etc/wireguard/wg0.conf")
    if not wireguard_config_path.exists():
        wg_config = """
[Interface]
PrivateKey = <YOUR_PRIVATE_KEY>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <YOUR_PEER_PUBLIC_KEY>
AllowedIPs = 0.0.0.0/0
        """
        os.makedirs(wireguard_config_path.parent, exist_ok=True)
        with open(wireguard_config_path, "w") as f:
            f.write(wg_config)
        print(f"WireGuard config created at {wireguard_config_path}")

def verify_and_transfer_files():
    print("Verifying and transferring panel files...")
    panel_files = {
        "backend": "backend/",
        "templates": "backend/templates/",
        "static": "backend/static/"
    }
    for src, dest in panel_files.items():
        if not os.path.exists(src):
            raise FileNotFoundError(f"Required source directory '{src}' is missing.")
        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        print(f"Checked directory: {dest}")
    print("All panel files are in the correct locations!")

def generate_admin_link():
    print("Generating admin link...")
    domain_or_ip = input("Enter your domain or IP (default: 127.0.0.1): ") or "127.0.0.1"
    random_string = secrets.token_urlsafe(16)
    admin_link = f"https://{domain_or_ip}/admin-{random_string}"
    with open("admin_link.txt", "w") as f:
        f.write(admin_link)
    print(f"Admin link generated: {admin_link}")

def setup_certificates():
    print("Setting up SSL certificates...")
    domain_or_ip = input("Enter your domain (or press Enter to skip): ")
    if domain_or_ip:
        subprocess.run(["certbot", "certonly", "--nginx", "-d", domain_or_ip], check=True)
        print("Certificates generated for domain:", domain_or_ip)
    else:
        subprocess.run(["certbot", "certonly", "--standalone", "--register-unsafely-without-email", "-d", "127.0.0.1"], check=True)
        print("Certificates generated for IP address.")

if __name__ == "__main__":
    print("Starting installation...")
    check_existing_directories()  # Checks necessary folders already exist
    install_dependencies()  # Installs necessary system-wide packages
    setup_virtualenv()  # Prepares a Python virtual environment
    generate_requirements_file()  # Generates requirements.txt for the project
    ensure_config_files()  # Ensures configuration files like Xray/WireGuard exist
    verify_and_transfer_files()  # Verifies and transfers panel files
    generate_admin_link()  # Produces admin link
    setup_certificates()  # Sets up SSL certificates
    print("Installation completed successfully! 🚀")
