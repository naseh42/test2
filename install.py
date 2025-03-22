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

def setup_trusted_host_middleware():
    print("Updating TrustedHostMiddleware in app.py...")
    server_ip = subprocess.getoutput("curl -s http://checkip.amazonaws.com").strip()
    app_file_path = "backend/app.py"
    with open(app_file_path, "r+") as file:
        content = file.read()
        updated_content = content.replace(
            'allowed_hosts=["*", "localhost", "127.0.0.1"]',
            f'allowed_hosts=["*", "localhost", "127.0.0.1", "{server_ip}"]'
        )
        file.seek(0)
        file.write(updated_content)
        file.truncate()
    print(f"TrustedHostMiddleware updated with server IP: {server_ip}")

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

def setup_certificates():
    print("Setting up SSL certificates...")
    domain_or_ip = subprocess.getoutput("curl -s http://checkip.amazonaws.com").strip()
    print(f"Using server IP: {domain_or_ip}")
    cert_path = f"{BASE_DIR}/configs/selfsigned.crt"
    key_path = f"{BASE_DIR}/configs/selfsigned.key"
    subprocess.run([
        "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048", "-keyout", key_path, "-out", cert_path,
        "-subj", f"/CN={domain_or_ip}"
    ], check=True)
    print(f"Self-signed certificate generated: {cert_path}, {key_path}")
    return domain_or_ip

def generate_admin_link(domain_or_ip):
    print("Generating admin links...")
    random_string = secrets.token_urlsafe(16)
    server_ip = subprocess.getoutput("curl -s http://checkip.amazonaws.com").strip()
    admin_link_ip = f"http://{server_ip}/admin-{random_string}"
    admin_link_domain = None
    if domain_or_ip and domain_or_ip != server_ip:
        admin_link_domain = f"https://{domain_or_ip}/admin-{random_string}"
    
    with open("admin_link.txt", "w") as f:
        if admin_link_domain:
            f.write(f"Domain Link: {admin_link_domain}\n")
        f.write(f"IP Link: {admin_link_ip}\n")
    
    print("\nAdmin Panel Links:")
    print(f"Admin Panel URL (IP): {admin_link_ip}")
    if admin_link_domain:
        print(f"Admin Panel URL (Domain): {admin_link_domain}")
    print(f"Setup log saved in: {os.path.join(BASE_DIR, 'setup.log')}\n")
    
    return admin_link_domain, admin_link_ip

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
            {"port": 443, "protocol": "vmess", "settings": {"clients": []}},
            {"port": 1080, "protocol": "socks", "settings": {}}
        ],
        "outbounds": [{"protocol": "freedom", "settings": {}}]
    }
    config_path = "/etc/xray/config.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(xray_config, f, indent=4)
    print("Xray configured successfully!")

def setup_wireguard():
    print("Setting up WireGuard...")
    wg_config_path = "/etc/wireguard/wg0.conf"

    # Generate keys for WireGuard
    server_private_key = subprocess.getoutput("wg genkey")
    server_public_key = subprocess.getoutput(f"echo {server_private_key} | wg pubkey")
    peer_private_key = subprocess.getoutput("wg genkey")
    peer_public_key = subprocess.getoutput(f"echo {peer_private_key} | wg pubkey")

    wg_config = f"""
    [Interface]
    PrivateKey = {server_private_key}
    Address = 10.0.0.1/24
    ListenPort = 51820

    [Peer]
    PublicKey = {peer_public_key}
    AllowedIPs = 0.0.0.0/0
    """
    os.makedirs(os.path.dirname(wg_config_path), exist_ok=True)
    with open(wg_config_path, "w") as f:
        f.write(wg_config)

    try:
        subprocess.run(["wg-quick", "up", "wg0"], check=True)
        print("WireGuard configured successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error during WireGuard setup: {e}")
        raise

if __name__ == "__main__":
    print("Starting installation...")
    check_and_create_directories()
    install_dependencies()
    setup_virtualenv()
    setup_trusted_host_middleware()
    domain_or_ip = setup_certificates()
    configure_nginx(domain_or_ip)
    generate_admin_link(domain_or_ip)
    setup_xray()
    setup_wireguard()
    print("\nInstallation completed successfully! 🚀")
