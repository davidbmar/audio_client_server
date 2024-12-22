Directory Stucture:
```
cognito/
├── static/             # Frontend assets
│   ├── css/            # CSS files
│   ├── js/             # JavaScript files
│   └── html/           # Standalone HTML files for testing
├── templates/          # Templates for Flask (can include Jinja2 placeholders)
│   └── protected/      # Templates requiring login
├── app.py              # Flask application
├── middleware.py       # Login decorators and middleware
├── requirements.txt    # Dependencies
└── README.md           # Project documentation
```


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

