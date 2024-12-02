# Shop Prototype Repository


## TODO
barcode should allow uuid or 6-12 digit string for upc-a/upc-e
add volunteer and admin users
Stock Check pulls both locaitons and allows qty changes
- how does qty mismatch need to work?
- allow to go negative
acknowledgesments page for sponsor and students
shop logo/favicon?

This repository is the development repository for the Rowan Shop & Pantry Inventory System
To contribute, please read the guidelines here : [Contributing.md](CONTRIBUTING.md)

<hr>
# Django + Docker = ❤️
<div markdown="1">

[![Build](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nbovee/shop-inventory/badge.svg?branch=main)](https://coveralls.io/github/nbovee/shop-inventory?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>


## How to use

### For Deployment as intended
> TODO Here we will describe the process to setup up a local raspberry pi to run the inventory system.

### For development on your computer

1. Clone the repository to your computer and go to the `shop-inventory` directory:
```console
git clone https://github.com/nbovee/shop-inventory.git
cd shop-inventory
```
Using VSCode, you may launch the debugpy tool into your development server by running "Simple Debug" from the Run and Debug tab of the IDE.

Now you can go to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Go to the Django admin panel and try updating the server code "on the fly".
Everything works just like if you were running the Django development server outside the container.

> Note that we mount the directory with your source code inside the container, so you can work with the project in your IDE, and changes will be visible inside the container, and the Django development server will restart itself.

<details markdown="1">
<summary>SQLite Usage Details</summary>

> Another important point is the use of SQLite3 instead of Postgres, because Postgres is not deployed until Django is run within a Docker Compose environment.
> In our example, we add a volume named `sqlite`. This data is stored persistently and does not disappear between restarts of the Django development server.
> However, if you have a second similar project, it would be better to change the volume name from `sqlite` to something else so that the second project uses its own copy of the database. For example:
>
```console
docker run -it --rm -p 8000:8000 -v another_sqlite:/sqlite -v $(pwd)/shop-inventory:/usr/src/shop-inventory shop-inventory:master python manage.py runserver 0.0.0.0:8000
```
>
>  To better understand how volumes work in Docker, refer to the official [documentation](https://docs.docker.com/storage/volumes/).
</details>

1. Run tests with pytest and coverage ✅:
```console
docker run --rm shop-inventory:master ./pytest.sh
```
The [pytest.sh](/shop-inventory/pytest.sh) script runs tests using pytest and coverage. As a result, you will see an output like this in the terminal:
```console
================== test session starts =====================================
platform linux -- Python 3.11.7, pytest-7.4.4, pluggy-1.3.0
django: version: 4.2.9, settings: core.settings (from ini)
rootdir: /usr/src/core
configfile: pytest.ini
plugins: django-4.7.0
collected 10 items

polls/tests.py .......... [100%]

================== 10 passed in 0.19s ======================================
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
polls/__init__.py                              0      0   100%
polls/admin.py                                12      0   100%
polls/apps.py                                  4      0   100%
polls/migrations/0001_initial.py               6      0   100%
polls/migrations/0002_question_upload.py       4      0   100%
polls/migrations/__init__.py                   0      0   100%
polls/models.py                               20      2    90%   15, 33
polls/tests.py                                57      0   100%
polls/urls.py                                  4      0   100%
polls/views.py                                28      8    71%   39-58
core/__init__.py                            6      0   100%
core/settings.py                           52      2    96%   94, 197
core/urls.py                                6      0   100%
------------------------------------------------------------------------
TOTAL                                        199     12    94%
```

> If you don't want to use pytest (for some reason), you can run the tests without pytest using the command below:
```console
docker run --rm shop-inventory:master python manage.py test
```

#### Django settings

Some Django settings from the [`settings.py`](shop-inventory/_core/settings.py) file are stored in environment variables. You can easily change these settings in the [`.env`](.env) file. This file does not contain all the necessary settings, but many of them. Add additional settings to environment variables if needed.

> It is important to note the following: **never store sensitive settings such as DJANGO_SECRET_KEY or DJANGO_EMAIL_HOST_PASSWORD in your repository!**
> Docker allows you to override environment variable values from additional files, the command line, or the current session. Store passwords and other sensitive information separately from the code and only connect this information at system startup.

Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting any changes.
## Acknowledgements
We would like to extend our sincere gratitude to:

- Our grant sponsor
- Our dedicated student workers who have contributed their time and skills to develop and improve this system
- The Rowan University Shop & Pantry for their support and partnership in creating this inventory management solution

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
