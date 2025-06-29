myproject/
├── config/ # Django settings package (not a single settings.py!)
│ ├── **init**.py
│ ├── asgi.py
│ ├── wsgi.py
│ ├── settings/ # Modular settings
│ │ ├── **init**.py
│ │ ├── base.py
│ │ ├── dev.py
│ │ ├── prod.py
│ │ └── test.py
│ ├── urls.py
│ └── celery.py # If using Celery
├── apps/ # All your Django apps go here
│ ├── **init**.py
│ ├── accounts/ # Example app
│ │ ├── admin.py
│ │ ├── apps.py
│ │ ├── migrations/
│ │ ├── models.py
│ │ ├── serializers.py # If using DRF
│ │ ├── tests/
│ │ │ ├── **init**.py
│ │ │ └── test_models.py
│ │ ├── urls.py
│ │ └── views.py
│ └── ... # More apps
├── manage.py
├── requirements/ # Requirements files
│ ├── base.txt
│ ├── dev.txt
│ ├── prod.txt
│ └── test.txt
├── static/ # Project-wide static files
├── templates/ # Project-wide templates
├── locale/ # Translations
├── scripts/ # Custom scripts for maintenance/devops
├── .env # Environment variables (never commit in production)
├── .gitignore
└── README.md

CREATE DATABASE dbname;
CREATE USER dbname WITH PASSWORD '123456';
GRANT ALL PRIVILEGES ON DATABASE dbname TO dbname;