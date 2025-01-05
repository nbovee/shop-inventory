# Shop Prototype Repository

This repository is the development repository for the Rowan Shop & Pantry Inventory System. It is built with Django and compiled for Raspberry Pi using the pi-gen tool. VSCode, UV, Docker, and WSL are used for development as they were easy to onboard inexperienced developers with.

<div markdown="1">

[![Build](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nbovee/shop-inventory/badge.svg?branch=main)](https://coveralls.io/github/nbovee/shop-inventory?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>
<hr>

## Django Development

### Initial Setup

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
- `SHOP_WIFI_PASSWORD`: WiFi hotspot password
- `SHOP_DJANGO_SUPERUSER_PASSWORD`: Admin password
- `SHOP_BACKUP_PASSWORD`: Backup encryption password

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

4. Build the image:
```bash
sudo ./build-docker.sh
```

The completed image will be available in `pi-gen/deploy`.

### Raspberry Pi Setup
> TODO: Document the process for setting up a local Raspberry Pi with the inventory system.

## Acknowledgements

We extend our sincere gratitude to:
- Our grant sponsor
- Our dedicated student workers
- The Rowan University Shop & Pantry

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Development Roadmap

- [ ] Support UUID or 6-12 digit string for UPC-A/UPC-E barcodes
- [ ] Implement volunteer and admin user roles
- [ ] Create acknowledgments page

## Contributing

This repository contains the Rowan Shop & Pantry Inventory System. To contribute, please read our [Contributing Guidelines](CONTRIBUTING.md).
