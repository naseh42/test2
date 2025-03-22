import os
import subprocess
import secrets
import json
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
                    "nginx", "certbot", "unzip", "wget", "ufw", "openssl"], check=True)
    print("All system dependencies installed successfully!")

def setup_virtualenv():
    print("Setting up Python virtual environment...")
    if not os.path.exists("venv"):
        subprocess.run(["python3", "-m", "venv", "venv"], check=True)
    subprocess.run(["venv/bin/pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(["venv/bin/pip", "install", "fastapi", "uvicorn", "jinja2", "python-multipart", 
                    "sqlalchemy", "bcrypt", "cryptography", "requests", "qrcode", "pytz"], check=True)
    print("Virtual environment and Python dependencies are set up!")

def prompt_for_domain():
    print("Do you want to use a custom domain? (Leave blank to use the server's IP address)")
    custom_domain = input("Enter your domain (or press Enter to use IP): ").strip()
    if not custom_domain:
        print("No domain provided. Fetching server's IP address...")
        try:
            server_ip = subprocess.getoutput("curl -s http://checkip.amazonaws.com").strip()
            print(f"Using server IP: {server_ip}")
            return server_ip
        except Exception as e:
            print(f"Error fetching server IP: {e}")
            return None
    else:
        print(f"Using custom domain: {custom_domain}")
        return custom_domain

def setup_trusted_host_middleware(domain_or_ip):
    print("Updating TrustedHostMiddleware in app.py...")
    app_file_path = "backend/app.py"
    with open(app_file_path, "r+") as file:
        content = file.read()
        updated_content = content.replace(
            'allowed_hosts=["*", "localhost", "127.0.0.1"]',
            f'allowed_hosts=["*", "localhost", "127.0.0.1", "{domain_or_ip}"]'
        )
        file.seek(0)
        file.write(updated_content)
        file.truncate()
    print(f"TrustedHostMiddleware updated with: {domain_or_ip}")

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
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
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

def setup_certificates(domain_or_ip):
    print("Setting up SSL certificates...")
    cert_path = f"{BASE_DIR}/configs/selfsigned.crt"
    key_path = f"{BASE_DIR}/configs/selfsigned.key"
    subprocess.run([
        "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048", "-keyout", key_path, "-out", cert_path,
        "-subj", f"/CN={domain_or_ip}"
    ], check=True)
    print(f"SSL certificate generated: {cert_path}, {key_path}")

def generate_admin_link(domain_or_ip):
    print("Generating admin links...")
    try:
        if not domain_or_ip:
            raise ValueError("Domain or IP address is empty. Please check the input!")

        random_string = secrets.token_urlsafe(16)
        admin_link = f"http://{domain_or_ip}/admin-{random_string}"

        link_path = os.path.join(BASE_DIR, "admin_link.txt")
        with open(link_path, "w") as f:
            f.write(f"Admin Panel URL: {admin_link}\n")

        print("\nAdmin Panel Link:")
        print(admin_link)
        print(f"Link saved in file: {link_path}\n")

        return admin_link
    except Exception as e:
        print(f"Error generating admin link: {e}")

def setup_xray():
    print("Setting up Xray...")
    xray_path = "/usr/local/bin/xray"
    os.makedirs(xray_path, exist_ok=True)
    subprocess.run(["wget", "-O", "/tmp/Xray-linux-64.zip", "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"], check=True)
    subprocess.run(["unzip", "/tmp/Xray-linux-64.zip", "-d", xray_path], check=True)
    subprocess.run(["chmod", "+x", f"{xray_path}/xray"], check=True)
    xray_config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {"port": 443, "protocol": "vmess", "settings": {"clients": []}, "streamSettings": {"network": "tcp"}},
            {"port": 8443, "protocol": "vless", "settings": {"decryption": "none"}, "streamSettings": {"network": "ws"}},
            {"port": 2083, "protocol": "http", "settings": {}, "streamSettings": {"network": "http"}},
            {"port": 8448, "protocol": "vless", "settings": {"decryption": "none"}, "streamSettings": {"network": "grpc"}},
            {"port": 4433, "protocol": "reality", "settings": {"clients": []}, "streamSettings": {"network": "tcp", "realitySettings": {"show": True}}},
        ],
        "outbounds": [{"protocol": "freedom", "settings": {}}],
        "routing": {"rules": [{"type": "field", "inboundTag": ["blocked"], "outboundTag": "blocked"}]},
    }
    config_path = "/etc/xray/config.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(xray_config, f, indent=4)

    print("Xray configured successfully!")

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
    domain_or_ip = prompt_for_domain()
    setup_trusted_host_middleware(domain_or_ip)
    setup_certificates(domain_or_ip)
    configure_nginx(domain_or_ip)
    generate_admin_link(domain_or_ip)
    setup_xray()
    run_uvicorn_as_service()
    print("\nInstallation completed successfully! 🚀")
