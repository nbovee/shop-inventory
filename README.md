# Shop Inventory System

This repository contains the Django-based inventory management system for the Rowan Shop & Pantry. The application is designed for offline-only operation using [Django](https://www.djangoproject.com/) with SQLite. [UV](https://docs.astral.sh/uv/) is used for dependency management and development.

<div markdown="1">

[![Build](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nbovee/shop-inventory/badge.svg?branch=main)](https://coveralls.io/github/nbovee/shop-inventory?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>
<hr>

## Development

### Initial Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

2. Clone the repository:
```console
git clone https://github.com/nbovee/shop-inventory.git
cd shop-inventory
```

3. Set up the development environment:
```console
# Install dependencies
uv sync

# Install pre-commit hooks (optional)
uvx pre-commit install
```

4. Create a `.env` file in the Django project directory:
```console
cd src/shop-inventory
cp .env.example .env  # If example exists, otherwise create manually
```

Configure the following environment variables in `.env`:
- `DJANGO_SECRET_KEY`: Django's secret key (generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
- `DJANGO_DEBUG`: Set to "true" for development
- `DJANGO_SUPERUSER_USERNAME`: Admin username (optional, for automated setup)
- `DJANGO_SUPERUSER_PASSWORD`: Admin password (optional)
- `DJANGO_SUPERUSER_EMAIL`: Admin email (optional)

> **Security Note**: Never commit the `.env` file to version control.

### Running the Application

1. Navigate to the Django project directory:
```console
cd src/shop-inventory
```

2. Run database migrations:
```console
python manage.py migrate
```

3. Create a superuser (if not using environment variables):
```console
python manage.py createsuperuser
```

4. Launch the development server:
```console
python manage.py runserver
```

5. Access the application at [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Testing and Code Quality

Run tests:
```console
uv run pytest
```

Generate coverage report:
```console
uv run coverage xml
```

Run linting:
```console
uv run ruff check
uv run ruff format --check
```

Fix formatting:
```console
uv run ruff format
```

## Application Structure

- **_core/**: Main Django application containing settings, base views, authentication, and user management
- **inventory/**: Handles product catalog, stock management, locations, and barcode generation
- **checkout/**: Manages shopping cart functionality and order processing

### Key Features

- Custom user authentication with session timeout (20 minutes)
- Product inventory management with location tracking
- Barcode/QR code generation for inventory items
- Shopping cart and order processing
- Bootstrap-based responsive UI
- SQLite database for simplicity and portability
- USB backup functionality (scans for drives with `.shopbackup` file)

## Acknowledgements

We extend our sincere gratitude to:
- [Rowan University's  The Shop Pantry & Resource Center](https://sites.rowan.edu/theshop/)
- Our grant sponsor, [the New Jersey Office of the Secretary of Higher Education](https://www.nj.gov/highereducation/)
- Our dedicated student team:
  - Erick Ayala-Ortiz
  - Cole Cheman
  - Brian Dalmar
  - Allison Garfield
  - Nik Leckie
  - Layane Neves
  - Juan Palacios
  - Emmy Sagapolutele
  - Solimar Soto
  - James Sunbury
  - Anne-Marie Zamor

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

This repository contains the Rowan Shop & Pantry Inventory System. To contribute, please read our [Contributing Guidelines](CONTRIBUTING.md).

<!-- ## Notes
We found the following resources helpful during development:
https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04#configure-nginx-to-proxy-pass-to-gunicorn
https://github.com/deltazero-cz/kiosk.pi
https://raspberrytips.com/access-point-setup-raspberry-pi/#setting-up-an-access-point-on-raspberry-pi-os-bookworm
https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md -->
