The below proxies to the fastAPI server:
    RewriteEngine On

    # Proxy requests to /get-presigned-url/ to FastAPI server
    ProxyPass /get-presigned-url/ http://localhost:8000/get-presigned-url/
    ProxyPassReverse /get-presigned-url/ http://localhost:8000/get-presigned-url/


To test this:
1.  Go to postman
in POST put: https://dev-onz3ew6jph17oszl.us.auth0.com/oauth/token

in BODY -> RAW
{
  "client_id": <CLIENT_ID_HERE>, 
  "client_secret": <CLIENT_SECRET>,
  "audience": "https://www.davidbmar.com/s3presigned",
  "grant_type": "client_credentials"
}

in the /etc/apache2/sites-available/www.davidbmar.com-le-ssl.conf
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    ServerName davidbmar.com
    ServerAlias www.davidbmar.com

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    Include /etc/letsencrypt/options-ssl-apache.conf

    SSLEngine On
    SSLCertificateFile /etc/letsencrypt/live/davidbmar.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/davidbmar.com/privkey.pem

    <Directory /var/www/html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    RewriteEngine On

    # Proxy requests to /get-presigned-url/ to FastAPI server
    ProxyPass /get-presigned-url/ http://localhost:8000/get-presigned-url/
    ProxyPassReverse /get-presigned-url/ http://localhost:8000/get-presigned-url/

    # Don't rewrite requests for static files
    RewriteCond %{REQUEST_URI} !^/static/
    RewriteCond %{REQUEST_URI} !^/get-presigned-url/
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^ /index.html [L]

    # WebSocket proxy with SSL/TLS for wss://
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteCond %{HTTP:Connection} =Upgrade [NC]
    RewriteRule /ws/(.*) ws://localhost:4040/ws/$1 [P,L]
</VirtualHost>
</IfModule>

