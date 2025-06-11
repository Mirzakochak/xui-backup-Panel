#!/bin/bash

show_menu() {
  echo "=============================="
  echo "  XUI Telegram Backup Bot"
  echo "=============================="
  echo "1) Install & Start Bot"
  echo "2) Uninstall Bot"
  echo "3) Exit"
  echo
}

install_bot() {
  read -p "🔑 Enter your bot token: " TOKEN
  read -p "👤 Enter your Telegram numeric ID (admin): " ADMIN_ID

  if [[ -z "$TOKEN" || -z "$ADMIN_ID" ]]; then
    echo "❌ Both token and admin ID are required!"
    exit 1
  fi

  echo "📦 Installing dependencies..."
  sudo dnf install -y python3 python3-pip
  pip3 install --upgrade pip
  pip3 install aiogram==2.25.1 apscheduler

  echo "🔧 Configuring bot..."
  sed -i "s|API_TOKEN = 'YOUR_BOT_TOKEN'|API_TOKEN = '${TOKEN}'|g" backup.py
  sed -i "s|ADMIN_ID = 123456789|ADMIN_ID = ${ADMIN_ID}|g" backup.py

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
}

uninstall_bot() {
  echo "🧹 Stopping and removing bot..."
  sudo systemctl stop xui-backup-bot
  sudo systemctl disable xui-backup-bot
  sudo rm -f /etc/systemd/system/xui-backup-bot.service
  sudo systemctl daemon-reload
  echo "✅ Bot removed!"
}

while true; do
  show_menu
  read -rp "Select an option [1-3]: " option

  case $option in
    1) install_bot ;;
    2) uninstall_bot ;;
    3) echo "👋 Goodbye!"; exit 0 ;;
    *) echo "❌ Invalid option, try again." ;;
  esac
done
