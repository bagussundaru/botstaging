# Sniper Bot & Dashboard Backup

Backup lengkap untuk sistem Sniper Bot dan Dashboard yang terhubung dengan Bybit API.

## Struktur File

```
botstaging/
├── README.md                    # Dokumentasi ini
├── requirements.txt             # Dependencies Python
├── .env                        # Environment variables (PRODUCTION)
├── .env.bybit                  # Environment variables khusus Bybit
├── config.py                   # Konfigurasi aplikasi
├── bybit_webhook_app.py        # Aplikasi webhook utama
├── run.py                      # Script runner alternatif
├── secure_http_server.py       # Dashboard HTTP aman
├── manage_secure_server.sh     # Script management dashboard
├── bybit_client.py             # Client Bybit API
├── trade_logger.py             # Logger untuk trading
├── datetime_utils.py           # Utilitas waktu
├── multi_account_executor.py   # Executor multi-account
├── monitor_apifan.py           # Monitor untuk akun apifan
├── monitor_apiarif.py          # Monitor untuk akun apiarif
├── start_webhook.sh            # Script start webhook
├── stop_webhook.sh             # Script stop webhook
├── check_status.sh             # Script cek status
├── webhook-nginx.conf          # Konfigurasi Nginx
├── static/                     # Asset statis
│   ├── css/                   # File CSS
│   ├── js/                    # File JavaScript
│   ├── simple_dashboard_apinur.html  # Dashboard apinur (static)
│   ├── simple_dashboard_apifan.html  # Dashboard apifan (static)
│   └── simple_dashboard_apiarif.html # Dashboard apiarif (static)
├── templates/                  # Template HTML
│   ├── dashboard_apifan.html  # Dashboard template apifan
│   ├── dashboard_apiarif.html # Dashboard template apiarif
│   ├── simple_dashboard_apinur.html  # Dashboard template apinur
│   ├── simple_dashboard_apifan.html  # Dashboard template apifan
│   ├── simple_dashboard_apiarif.html # Dashboard template apiarif
│   └── [template lainnya...]  # Template dashboard lainnya
├── logs/                      # Direktori log (kosong)
└── systemd/                   # File service systemd
    └── sniper-webhook.service # Service definition
```

## Komponen Utama

### 1. Webhook Server
- **File**: `bybit_webhook_app.py`
- **Port**: 5001 (production)
- **Endpoint**: `http://103.189.234.15/webhook_v1`
- **Fungsi**: Menerima alert dari TradingView dan eksekusi order ke Bybit

### 2. Dashboard HTTP Aman
- **File**: `secure_http_server.py`
- **Port**: 8080
- **URL**: `http://103.189.234.15:8080/`
- **Fungsi**: Dashboard monitoring dengan autentikasi multi-user

### 3. Multi-Account Dashboard
- **File Monitor**: `monitor_apifan.py`, `monitor_apiarif.py`
- **Executor**: `multi_account_executor.py`
- **Templates**: Dashboard HTML untuk apinur, apifan, apiarif
- **Fungsi**: Monitoring dan eksekusi trading untuk multiple akun

### 4. Konfigurasi
- **Environment**: `.env` dan `.env.bybit`
- **Config**: `config.py`
- **Nginx**: `webhook-nginx.conf`

## Cara Restore/Deploy

### 1. Persiapan Environment
```bash
# Buat direktori kerja
mkdir -p /home/clurut/sniper_restored
cd /home/clurut/sniper_restored

# Copy semua file dari backup
cp -r /home/clurut/botstaging/* .

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Konfigurasi Environment
```bash
# Edit file .env sesuai kebutuhan
nano .env

# Pastikan API keys Bybit sudah benar
nano .env.bybit
```

### 3. Setup Nginx (jika diperlukan)
```bash
# Copy konfigurasi Nginx
sudo cp webhook-nginx.conf /etc/nginx/sites-available/webhook
sudo ln -s /etc/nginx/sites-available/webhook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Setup Systemd Service
```bash
# Copy service file
sudo cp systemd/sniper-webhook.service /etc/systemd/system/

# Edit path di service file jika diperlukan
sudo nano /etc/systemd/system/sniper-webhook.service

# Enable dan start service
sudo systemctl daemon-reload
sudo systemctl enable sniper-webhook.service
sudo systemctl start sniper-webhook.service
```

### 5. Start Services

#### Webhook Server
```bash
# Manual start
./start_webhook.sh

# Atau via systemd
sudo systemctl start sniper-webhook
```

#### Dashboard
```bash
# Start dashboard aman (utama)
./manage_secure_server.sh start

# Start monitor multi-account (opsional)
python monitor_apifan.py &
python monitor_apiarif.py &

# Akses dashboard:
# - Dashboard utama: http://103.189.234.15:8080/
# - Dashboard apinur: http://103.189.234.15:8080/static/simple_dashboard_apinur.html
# - Dashboard apifan: http://103.189.234.15:8080/static/simple_dashboard_apifan.html  
# - Dashboard apiarif: http://103.189.234.15:8080/static/simple_dashboard_apiarif.html
```

### 6. Verifikasi
```bash
# Cek status webhook
./check_status.sh

# Test webhook endpoint
curl -X POST http://103.189.234.15/webhook_v1 \
  -H "Content-Type: application/json" \
  -d '{"action":"test","symbol":"ETHUSDT","price":2000,"token":"sniper-bybit-production-2024"}'

# Test dashboard
curl http://103.189.234.15:8080/
```

## Kredensial Dashboard

Dashboard menggunakan autentikasi multi-user:

- **admin**: admin123
- **trader**: trader456  
- **monitor**: monitor789
- **guest**: guest000

## File Log Penting

Setelah restore, monitor file log berikut:
- `/path/to/restored/logs/bybit_production.log` - Log webhook utama
- `/path/to/restored/logs/secure_server.log` - Log dashboard
- `/path/to/restored/logs/bybit_trades.log` - Log trading

## Troubleshooting

### Webhook tidak menerima alert
1. Cek Nginx config dan restart
2. Pastikan port 5001 terbuka
3. Verifikasi token di TradingView alert

### Dashboard tidak bisa diakses
1. Cek apakah secure_http_server.py berjalan
2. Pastikan port 8080 terbuka
3. Restart dengan `./manage_secure_server.sh restart`

### Trading tidak eksekusi
1. Cek API keys di `.env.bybit`
2. Verifikasi balance di akun Bybit
3. Cek log error di `bybit_production.log`

## Backup Dibuat

Tanggal: $(date)
Dari: /home/clurut/binance_webhook dan /home/clurut/botoktober
Ke: /home/clurut/botstaging

## Catatan Penting

⚠️ **KEAMANAN**: 
- File `.env` berisi API keys sensitif
- Jangan commit ke repository public
- Backup secara terpisah dan aman

⚠️ **PRODUCTION**:
- Backup ini dari environment production
- Test di staging sebelum deploy ke production
- Pastikan tidak ada konflik port

⚠️ **DEPENDENCIES**:
- Memerlukan Python 3.8+
- Nginx untuk proxy
- Systemd untuk service management