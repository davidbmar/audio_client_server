For production setup, create a systemd service. Create a file /etc/systemd/system/flask-app.service:

iniCopy[Unit]
Description=Gunicorn instance to serve flask application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/working/audio_client_server/cognito
Environment="PATH=/home/ubuntu/.local/bin"
ExecStart=/home/ubuntu/.local/bin/gunicorn --workers 3 --bind localhost:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target

Enable and start the service:

bashCopysudo systemctl daemon-reload
sudo systemctl start flask-app
sudo systemctl enable flask-app

To check the status and logs:

bashCopysudo systemctl status flask-app
sudo journalctl -u flask-app

