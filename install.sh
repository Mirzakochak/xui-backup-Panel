#!/bin/bash

echo "=============================="
echo "  XUI Telegram Backup Bot"
echo "=============================="

read -p "🔑 Enter your bot token: " TOKEN
read -p "👤 Enter your Telegram numeric ID (admin): " ADMIN_ID

# Validate inputs
if [[ -z "$TOKEN" || -z "$ADMIN_ID" ]]; then
  echo "❌ Both token and admin ID are required!"
  exit 1
fi

echo "📦 Installing dependencies..."
sudo dnf install -y python3 python3-pip
pip3 install --upgrade pip
pip3 install aiogram==2.25.1 apscheduler

echo "🔧 Configuring bot..."

# Replace placeholders in Python file
sed -i "s|API_TOKEN = 'YOUR_BOT_TOKEN'|API_TOKEN = '${TOKEN}'|g" backup.py
sed -i "s|ADMIN_ID = 123456789|ADMIN_ID = ${ADMIN_ID}|g" backup.py

# Create systemd service
cat <<EOF | sudo tee /etc/systemd/system/xui-backup-bot.service
[Unit]
Description=XUI Telegram Backup Bot
After=network.target

[Service]
User=root
WorkingDirectory=$PWD
ExecStart=/usr/bin/python3 $PWD/backup.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable xui-backup-bot
sudo systemctl start xui-backup-bot

echo
echo "✅ Bot installed and started successfully!"
echo "ℹ️ You can now interact with the bot on Telegram."
