#!/bin/bash

# Sniper Bot Restore Script
# Script untuk restore backup ke lokasi baru

set -e

echo "=== Sniper Bot Restore Script ==="
echo "Tanggal: $(date)"
echo

# Validasi parameter
if [ $# -eq 0 ]; then
    echo "Usage: $0 <target_directory>"
    echo "Contoh: $0 /home/clurut/sniper_production"
    exit 1
fi

TARGET_DIR="$1"
BACKUP_DIR="$(dirname "$0")"

echo "Source (backup): $BACKUP_DIR"
echo "Target: $TARGET_DIR"
echo

# Konfirmasi
read -p "Lanjutkan restore ke $TARGET_DIR? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Restore dibatalkan."
    exit 0
fi

# Buat direktori target
echo "Membuat direktori target..."
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Copy semua file kecuali yang tidak perlu
echo "Menyalin file..."
rsync -av --exclude='logs/*' --exclude='__pycache__' --exclude='*.pyc' "$BACKUP_DIR/" "$TARGET_DIR/"

# Buat direktori log
mkdir -p logs

# Set permissions
echo "Setting permissions..."
chmod +x *.sh
chmod 600 .env .env.bybit 2>/dev/null || true

# Install dependencies jika ada pip
if command -v pip &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️  pip tidak ditemukan. Install dependencies secara manual:"
    echo "   pip install -r requirements.txt"
fi

echo
echo "✅ Restore selesai!"
echo
echo "Langkah selanjutnya:"
echo "1. Edit file .env dan .env.bybit dengan API keys yang benar"
echo "2. Setup Nginx jika diperlukan: sudo cp webhook-nginx.conf /etc/nginx/sites-available/"
echo "3. Setup systemd service: sudo cp systemd/sniper-webhook.service /etc/systemd/system/"
echo "4. Start services: ./start_webhook.sh dan ./manage_secure_server.sh start"
echo "5. Verifikasi: ./check_status.sh"
echo
echo "Dokumentasi lengkap: cat README.md"
