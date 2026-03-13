# UzBox Production Deployment Guide

## Minimal talab
- Ubuntu 22.04 LTS
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 20+ (frontend uchun)

## 1. Server sozlash

```bash
# Yangilash
sudo apt update && sudo apt upgrade -y

# Kerakli paketlar
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib redis-server nginx git

# PostgreSQL DB yaratish
sudo -u postgres psql -c "CREATE USER uzbox_user WITH PASSWORD 'STRONG_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE uzbox_db OWNER uzbox_user;"

# Redis ishga tushirish
sudo systemctl enable redis-server && sudo systemctl start redis-server
```

## 2. Backend deploy

```bash
cd /var/www/uzbox/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# .env.production ni .env ga nusxalash va to'ldirish
cp .env.production .env
nano .env  # Barcha qiymatlarni to'ldiring

# Migration va static
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 3. Systemd — Gunicorn

`/etc/systemd/system/uzbox.service`:
```ini
[Unit]
Description=UzBox Django Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/uzbox/backend
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/var/www/uzbox/backend/venv/bin/gunicorn \
    -c gunicorn.conf.py \
    config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable uzbox && sudo systemctl start uzbox
```

## 4. Systemd — Celery Worker

`/etc/systemd/system/uzbox-celery.service`:
```ini
[Unit]
Description=UzBox Celery Worker
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/var/www/uzbox/backend
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/var/www/uzbox/backend/venv/bin/celery \
    -A config.celery worker \
    --loglevel=warning \
    --concurrency=4 \
    -n uzbox_worker@%%h
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable uzbox-celery && sudo systemctl start uzbox-celery
```

## 5. Nginx config

`/etc/nginx/sites-available/uzbox`:
```nginx
server {
    listen 80;
    server_name uzbox.uz www.uzbox.uz;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name uzbox.uz www.uzbox.uz;

    ssl_certificate     /etc/letsencrypt/live/uzbox.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/uzbox.uz/privkey.pem;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin (xavfsiz URL)
    location /uzb-secure-admin/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        # IP whitelist (ixtiyoriy)
        # allow YOUR_IP;
        # deny all;
    }

    # Static fayllar
    location /static/ {
        alias /var/www/uzbox/backend/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/uzbox /etc/nginx/sites-enabled/
sudo certbot --nginx -d uzbox.uz -d www.uzbox.uz
sudo nginx -t && sudo systemctl reload nginx
```

## 6. Frontend deploy

```bash
cd /var/www/uzbox/frontend
npm install
cp .env.production .env.local
npm run build
```

`/etc/systemd/system/uzbox-frontend.service`:
```ini
[Unit]
Description=UzBox Next.js Frontend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/uzbox/frontend
ExecStart=/usr/bin/npm start
Restart=always
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

## 7. SSL sertifikat yangilash (avtomatik)

```bash
sudo crontab -e
# Qo'shing:
0 3 * * 1 certbot renew --quiet && systemctl reload nginx
```

## 8. Monitoring

```bash
# Loglarni kuzatish
journalctl -u uzbox -f
journalctl -u uzbox-celery -f

# Status tekshirish
sudo systemctl status uzbox uzbox-celery uzbox-frontend

# DB backup (har kuni)
# /etc/cron.daily/uzbox-backup:
pg_dump -U uzbox_user uzbox_db | gzip > /backups/uzbox_$(date +%Y%m%d).sql.gz
```

## Tekshirish ro'yxati (checklist)

- [ ] `.env` da barcha qiymatlar to'ldirilgan
- [ ] `SECRET_KEY` o'zgartirilgan (50+ belgi)
- [ ] `DEBUG=False`
- [ ] PostgreSQL ulanishi ishlaydi
- [ ] Redis ishlaydi (`redis-cli ping`)
- [ ] Celery worker ishlaydi
- [ ] Email yuboriladi (test: `python manage.py shell -c "from django.core.mail import send_mail; send_mail('test','test','from@uzbox.uz',['to@email.com'])"`)
- [ ] Click sandbox sinov to'lovi o'tdi
- [ ] Payme sandbox sinov to'lovi o'tdi
- [ ] SSL sertifikat o'rnatildi
- [ ] Nginx konfiguratsiya to'g'ri
- [ ] Superuser yaratildi
- [ ] `collectstatic` bajarildi
