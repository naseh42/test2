import os
import json
import subprocess
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_server_ip():
    """ دریافت آی‌پی عمومی سرور """
    try:
        return subprocess.check_output("curl -s ifconfig.me", shell=True).decode().strip()
    except:
        return "127.0.0.1"

def generate_admin_link(domain_or_ip):
    """ تولید لینک تصادفی برای پنل ادمین """
    print("Generating admin link...")

    if not domain_or_ip:
        domain_or_ip = get_server_ip()
    
    random_string = secrets.token_urlsafe(16)
    admin_link = f"http://{domain_or_ip}/admin-{random_string}"

    link_path = os.path.join(BASE_DIR, "admin_link.txt")
    with open(link_path, "w") as f:
        f.write(f"Admin Panel URL: {admin_link}\n")

    print(f"\n✅ Admin Panel Link: {admin_link}")
    print(f"🔹 Link saved in: {link_path}")

    return admin_link

def setup_nginx(domain_or_ip):
    """ تنظیم خودکار Nginx برای اتصال پنل وب """
    print("🔹 Configuring Nginx...")
    nginx_config = f"""
    server {{
        listen 80;
        server_name {domain_or_ip};

        location / {{
            proxy_pass http://127.0.0.1:8000/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }}

        location /static/ {{
            alias {os.path.join(BASE_DIR, "backend/static")};
        }}

        error_log /var/log/nginx/management_panel_error.log;
        access_log /var/log/nginx/management_panel_access.log;
    }}
    """
    config_path = "/etc/nginx/sites-available/management_panel"
    if os.path.exists("/etc/nginx/sites-enabled/management_panel"):
        print("🔹 Existing symbolic link found. Removing...")
        subprocess.run(["rm", "/etc/nginx/sites-enabled/management_panel"], check=True)

    with open(config_path, "w") as f:
        f.write(nginx_config)
    
    subprocess.run(["ln", "-s", config_path, "/etc/nginx/sites-enabled/"], check=True)
    subprocess.run(["nginx", "-t"], check=True)
    subprocess.run(["systemctl", "restart", "nginx"], check=True)
    print("✅ Nginx configured successfully!")

def setup_ssl(domain=None):
    """ تنظیم و دریافت SSL - اگر دامنه باشد Let’s Encrypt، در غیر اینصورت سلف ساین """
    ssl_path = "/etc/ssl/private"
    os.makedirs(ssl_path, exist_ok=True)
    
    if domain:
        print(f"🔹 Trying to get SSL certificate for {domain} ...")
        try:
            subprocess.run(["apt", "install", "-y", "certbot"], check=True)
            subprocess.run(["certbot", "certonly", "--standalone", "-d", domain, "--non-interactive", "--agree-tos", "-m", "admin@example.com"], check=True)
            print("✅ SSL installed via Let's Encrypt!")
            return f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        except Exception as e:
            print(f"❌ Failed to get SSL certificate: {e}")

    print("🔹 Generating self-signed certificate...")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout", f"{ssl_path}/selfsigned.key",
                    "-out", f"{ssl_path}/selfsigned.crt", "-days", "365", "-nodes", "-subj", "/CN=localhost"], check=True)
    return f"{ssl_path}/selfsigned.crt"

def setup_xray():
    """ دانلود، نصب و تنظیم XRay """
    print("🔹 Setting up Xray...")
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
            {"port": 4433, "protocol": "shadowsocks", "settings": {"method": "aes-128-gcm", "password": "your-password"}},
            {"port": 4434, "protocol": "h2_quic", "settings": {}, "streamSettings": {"network": "h2"}},
        ],
        "outbounds": [{"protocol": "freedom", "settings": {}}],
        "routing": {"rules": [{"type": "field", "inboundTag": ["blocked"], "outboundTag": "blocked"}]},
    }
    
    config_path = "/etc/xray/config.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, "w") as f:
        json.dump(xray_config, f, indent=4)

    print("✅ Xray configured successfully!")

def setup_database():
    """ نصب و تنظیم دیتابیس MariaDB """
    print("🔹 Setting up MariaDB database...")
    subprocess.run(["systemctl", "start", "mariadb"], check=True)
    subprocess.run(["systemctl", "enable", "mariadb"], check=True)

    try:
        print("🔹 Checking if database exists...")
        # بررسی وجود دیتابیس
        check_db_script = "SHOW DATABASES LIKE 'app_db';"
        result = subprocess.run(["mysql", "-e", check_db_script], capture_output=True, text=True)
        
        if 'app_db' in result.stdout:
            print("✅ Database 'app_db' already exists. Skipping creation.")
        else:
            print("🔹 Creating database and user...")
            db_script = """
            CREATE DATABASE app_db;
            CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'strong_password';
            GRANT ALL PRIVILEGES ON app_db.* TO 'app_user'@'localhost';
            FLUSH PRIVILEGES;
            """
            subprocess.run(["mysql", "-e", db_script], check=True)
        
        config_path = os.path.join(BASE_DIR, "database_config.txt")
        with open(config_path, "w") as f:
            f.write("Database Name: app_db\n")
            f.write("Username: app_user\n")
            f.write("Password: strong_password\n")
        
        print(f"✅ Database setup complete! Configuration saved in {config_path}")
    except Exception as e:
        print(f"❌ Error during database setup: {e}")

def run_uvicorn_as_service():
    """ تنظیم و اجرای Uvicorn به عنوان سرویس systemd """
    print("🔹 Configuring Uvicorn as a service...")
    
    service_config = f"""
    [Unit]
    Description=Uvicorn Service
    After=network.target

    [Service]
    User={os.getlogin()}
    WorkingDirectory={BASE_DIR}
    ExecStart={BASE_DIR}/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --proxy-headers
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
    
    print("✅ Uvicorn service configured successfully!")

if __name__ == "__main__":
    print("🚀 Starting setup process...\n")

    domain = input("Enter your domain (leave empty to use server IP): ").strip() or None
    domain_or_ip = domain if domain else get_server_ip()

    admin_link = generate_admin_link(domain_or_ip)
    setup_nginx(domain_or_ip)
    ssl_certificate = setup_ssl(domain)
    setup_xray()
    setup_database()
    run_uvicorn_as_service()

    print("\n✅ **Setup Completed Successfully!**")
    print(f"🔹 **Admin Panel:** {admin_link}")
    print(f"🔹 **SSL Certificate:** {ssl_certificate}")
