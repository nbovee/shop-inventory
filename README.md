# Shop Prototype Repository

This repository is the development repository for the Rowan Shop & Pantry Inventory System. Due to installation constraints where no WAN is available, it is built with Django and compiled for Raspberry Pi using the pi-gen tool. VSCode, UV, Docker, and WSL are used for development as they were easy to onboard inexperienced developers with.

<div markdown="1">

[![Build](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nbovee/shop-inventory/badge.svg?branch=main)](https://coveralls.io/github/nbovee/shop-inventory?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>
<hr>

## Django Development

### Initial Setup
0. Install astral/uv, docker, and wsl as needed.

1. Clone the repository with submodules and initialize the development environment:
```console
git clone --recursive https://github.com/nbovee/shop-inventory.git
cd shop-inventory
bash init.sh
```

2. Create your environment file:
```bash
cp .env.example .env
```

3. Configure the following variables in `.env`:
- `SHOP_DJANGO_SECRET_KEY`: Django's secret key
- `SHOP_DJANGO_DEBUG`: Development mode ("true"/"false")
- `WIFI_PASS`: WiFi hotspot password
- `SHOP_DJANGO_SUPERUSER_PASSWORD`: Admin password
- `DJANGO_BACKUP_PASSWORD`: Backup encryption password

> **Security Note**: Never commit the `.env` file to version control.

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

3. Set up the build environment:
```bash
cp -r pi-gen-pantry/00-shop pi-gen/custom-stage
cp config pi-gen/
cd pi-gen
touch ./stage{3,4,5}/SKIP
touch ./stage{4,5}/SKIP_IMAGES
```

4. Build the image (this directs to the build-docker.sh script within pi-gen, as we are using wsl to build the image):
```bash
sudo ./build.sh
```

The completed image will be available in `/deploy`.

### Raspberry Pi Setup
The completed image can be flashed to a Raspberry Pi using the tool Raspberry Pi Imager.

## Acknowledgements

We extend our sincere gratitude to:
- Our grant sponsor
- Our dedicated student workers
- The Rowan University Shop & Pantry

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

This repository contains the Rowan Shop & Pantry Inventory System. To contribute, please read our [Contributing Guidelines](CONTRIBUTING.md).

## Notes
https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04#configure-nginx-to-proxy-pass-to-gunicorn
https://medium.com/@deltazero/making-kioskpi-custom-raspberry-pi-os-image-using-pi-gen-99aac2cd8cb6
https://github.com/deltazero-cz/kiosk.pi
https://raspberrytips.com/access-point-setup-raspberry-pi/#setting-up-an-access-point-on-raspberry-pi-os-bookworm
https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md
