import os
import subprocess
import secrets
import json
import socket
from pathlib import Path

BASE_DIR = os.path.abspath(os.getcwd())

def check_and_create_directories():
    print("Checking and creating missing directories...")
    required_directories = ["backend/static", "backend/templates", "backend/database", "configs"]
    for directory in required_directories:
        if not os.path.exists(directory):
            print(f"Directory '{directory}' is missing. Creating it now...")
            os.makedirs(directory, exist_ok=True)
    print("All required directories are now in place!")

def install_dependencies():
    print("Installing system-wide dependencies...")
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "install", "-y", "python3", "python3-pip", "python3-venv", 
                    "nginx", "mariadb-server", "certbot", "unzip", "wget", 
                    "wireguard", "ufw", "openssl"], check=True)
    print("All system dependencies installed successfully!")

def setup_virtualenv():
    print("Setting up Python virtual environment...")
    if not os.path.exists("venv"):
        subprocess.run(["python3", "-m", "venv", "venv"], check=True)
    subprocess.run(["venv/bin/pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(["venv/bin/pip", "install", "fastapi", "uvicorn", "jinja2", "python-multipart", 
                    "sqlalchemy", "bcrypt", "cryptography", "requests", "qrcode", "pytz"], check=True)
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
        "cryptography",
        "requests",
        "qrcode",
        "pytz"
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

def configure_nginx(domain_or_ip):
    print("Configuring Nginx...")
    nginx_config = f"""
    server {{
        listen 80;
        server_name {domain_or_ip};

        location / {{
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }}
    }}
    """
    nginx_path = "/etc/nginx/sites-available/default"
    with open(nginx_path, "w") as f:
        f.write(nginx_config)
    subprocess.run(["nginx", "-t"], check=True)
    subprocess.run(["systemctl", "restart", "nginx"], check=True)
    print("Nginx configured successfully!")

def verify_and_transfer_files():
    print("Verifying and transferring panel files...")
    panel_files = {
        f"{BASE_DIR}/backend/templates": f"{BASE_DIR}/backend/templates/",
        f"{BASE_DIR}/backend/static": f"{BASE_DIR}/backend/static/",
        f"{BASE_DIR}/backend": f"{BASE_DIR}/backend/"
    }
    for src, dest in panel_files.items():
        print(f"Checking directory: {src}")
        if not os.path.exists(src):
            print(f"Source directory '{src}' is missing.")
            raise FileNotFoundError(f"Required source directory '{src}' is missing.")
        if not os.path.exists(dest):
            print(f"Destination directory '{dest}' is missing. Creating it now...")
            os.makedirs(dest, exist_ok=True)
        print(f"Directory '{dest}' checked or created successfully!")
    print("All panel files are in the correct locations!")

def setup_certificates():
    print("Setting up SSL certificates...")
    domain_or_ip = input("Enter your domain (or press Enter to use the server IP): ").strip()
    if not domain_or_ip:
        domain_or_ip = socket.gethostbyname(socket.gethostname())
        print(f"No domain provided. Using server IP: {domain_or_ip}")
        print("Generating self-signed certificate...")
        cert_path = f"{BASE_DIR}/configs/selfsigned.crt"
        key_path = f"{BASE_DIR}/configs/selfsigned.key"
        subprocess.run([
            "openssl", "req", "-x509", "-nodes", "-days", "365",
            "-newkey", "rsa:2048", "-keyout", key_path, "-out", cert_path,
            "-subj", f"/CN={domain_or_ip}"
        ], check=True)
        print(f"Self-signed certificate generated successfully!")
        print(f"Certificate: {cert_path}")
        print(f"Key: {key_path}")
    else:
        print("Requesting certificate from Let's Encrypt...")
        subprocess.run(["certbot", "certonly", "--nginx", "-d", domain_or_ip], check=True)
        print("Certificates generated for domain:", domain_or_ip)
    return domain_or_ip

def generate_admin_link(domain_or_ip):
    print("Generating admin links...")
    random_string = secrets.token_urlsafe(16)
    
    # لینک ادمین با آی‌پی
    server_ip = socket.gethostbyname(socket.gethostname())
    admin_link_ip = f"http://{server_ip}/admin-{random_string}"
    
    # لینک ادمین با دامنه (اگر وجود داشت)
    admin_link_domain = None
    if domain_or_ip and domain_or_ip != server_ip:
        admin_link_domain = f"https://{domain_or_ip}/admin-{random_string}"
    
    # ذخیره لینک‌ها در فایل
    with open("admin_link.txt", "w") as f:
        if admin_link_domain:
            f.write(f"Domain Link: {admin_link_domain}\n")
        f.write(f"IP Link: {admin_link_ip}\n")
    
    # نمایش لینک‌ها در خروجی
    if admin_link_domain:
        print(f"Admin link with domain: {admin_link_domain}")
    print(f"Admin link with IP: {admin_link_ip}")
    
    return admin_link_domain, admin_link_ip

def run_uvicorn_as_service():
    print("Configuring Uvicorn as a service...")
    service_config = f"""
    [Unit]
    Description=Uvicorn Service
    After=network.target

    [Service]
    User={os.getlogin()}
    WorkingDirectory={BASE_DIR}
    ExecStart={BASE_DIR}/venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    """
    service_path = "/etc/systemd/system/uvicorn.service"
    with open(service_path, "w") as f:
        f.write(service_config)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "start", "uvicorn"], check=True)
    subprocess.run(["systemctl", "enable", "uvicorn"], check=True)
    print("Uvicorn service configured successfully!")

if __name__ == "__main__":
    print("Starting installation...")
    check_and_create_directories()
    install_dependencies()
    setup_virtualenv()
    generate_requirements_file()
    ensure_config_files()
    verify_and_transfer_files()
    domain_or_ip = setup_certificates()
    configure_nginx(domain_or_ip)
    admin_link_domain, admin_link_ip = generate_admin_link(domain_or_ip)
    run_uvicorn_as_service()
    print("\nInstallation completed successfully! 🚀")
