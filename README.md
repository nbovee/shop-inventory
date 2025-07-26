# Shop Prototype Repository

This repository is the development repository for the Rowan Shop & Pantry Inventory System. Due to installation constraints where no WAN is available, it is built with [Django](https://www.djangoproject.com/) and compiled for Raspberry Pi using the [pi-gen](https://github.com/RPi-Distro/pi-gen) tool for fully offline deployment. [UV](https://docs.astral.sh/uv/), [Docker](https://docs.docker.com/), [WSL](https://docs.microsoft.com/en-us/windows/wsl/install), and [VSCode](https://code.visualstudio.com/) are used for development as they were easy to onboard inexperienced developers with.

Effort has been taken to make this follow [Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html). This is a design choice, to allow for easy reuse of the build process for other projects or multiple concurrent applications. The service files are used to automatically start the Django server on boot, without the security risks of running as root or with auto-login.

<div markdown="1">

[![Build](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nbovee/shop-inventory/badge.svg?branch=main)](https://coveralls.io/github/nbovee/shop-inventory?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>
<hr>

## Development

### Initial Setup
1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), [Docker Desktop](https://docs.docker.com/engine/install/), and [WSL](https://docs.microsoft.com/en-us/windows/wsl/install) as needed.

2. Clone the repository with submodules and initialize the development environment:
```console
git clone --recursive https://github.com/nbovee/shop-inventory.git
cd shop-inventory
bash init.sh
```

3. Create your config file:
```bash
cp config.example config
```

4. Configure at least the following variables in `config`:
- `DJANGO_SECRET_KEY`: Django's secret key
- `DJANGO_DEBUG`: Development mode ("true"/"false")
- `WIFI_PASS`: WiFi hotspot password
- `DJANGO_SUPERUSER_PASSWORD`: Admin password
- `DJANGO_BACKUP_PASSWORD`: Backup encryption password

> **Security Note**: Never commit the `config` file to version control.

### Running the Application

1. Launch the development server:
   - In VSCode: Run "Simple Debug" from the Run and Debug tab
   - Access the application at [http://127.0.0.1:8000](http://127.0.0.1:8000)

2. Run tests:
```console
uv run pytest
```

> Note: The source code directory is mounted inside the container, allowing real-time code changes to be reflected in the development server.

## Deployment

### Building the Raspberry Pi Image

1. If using WSL (Windows Subsystem for Linux), set up ARM emulation:
```console
sudo apt-get update
sudo apt-get install qemu-user-static
sudo update-binfmts --enable
```

2. Ensure submodules are initialized:
```bash
git submodule update --init
```

3. Set up the links for the build environment and the skip files used by pi-gen:
```bash
bash init.sh
```

4. Build the image (this directs to the build-docker.sh script within pi-gen, as we are using WSL to build the image):
```bash
bash build.sh
```

The completed image will be available in `/deploy`.

### Raspberry Pi Setup
The completed image can be flashed to a Raspberry Pi using the tool Raspberry Pi Imager.

### Backup Drives
As a WLAN network, there is no possibility for an offsite backup. Instead, the RPi scans for connected USB drives containing a file name `.shopbackup`, and exports the database to that drive.
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
