# Shop Prototype Repository

This repository is the development repository for the Rowan Shop & Pantry Inventory System
To contribute, please read the guidelines here : [Contributing.md](CONTRIBUTING.md)

<hr>
# Django + uv + VSCode + Docker = ❤️
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

Now you can go to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

> Note that we mount the directory with your source code inside the container, so you can work with the project in your IDE, and changes will be visible inside the container, and the Django development server will restart itself.

2. Run tests with pytest and coverage ✅:
```console
uv run pytest
```
The pytest tool runs tests using pytest-django and pytest-cov (wrapping coverage). As a result, you will see an output like this in the terminal:
```console
uv run pytest
================================= test session starts ==================================
platform win32 -- Python 3.12.5, pytest-8.3.4, pluggy-1.5.0
django: version: 4.2.16, settings: _core.settings (from ini)
rootdir: C:\CODE\shop-inventory
configfile: pyproject.toml
plugins: cov-6.0.0, django-4.9.0
collected 3 items

shop-inventory\_core\tests.py .                                                   [ 33%]
shop-inventory\inventory\tests.py .                                               [ 66%]
shop-inventory\tests\test_exists.py .                                             [100%]

---------- coverage: platform win32, python 3.12.5-final-0 -----------
Name                                                              Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------------
shop-inventory\_core\asgi.py                                          4      4     0%   10-16
shop-inventory\_core\management\commands\backup_db.py                41     41     0%   1-78
shop-inventory\_core\management\commands\loadtestdata.py             13     13     0%   1-19
shop-inventory\_core\management\commands\safecreatesuperuser.py      23     23     0%   6-58
shop-inventory\_core\models.py                                        7      1    86%   13
shop-inventory\_core\settings.py                                     56      1    98%   200
shop-inventory\_core\signals.py                                      28     20    29%   11-18, 24-49
shop-inventory\_core\urls.py                                          6      6     0%   18-34
shop-inventory\_core\views.py                                        17     17     0%   1-31
shop-inventory\_core\wsgi.py                                          4      4     0%   10-16
shop-inventory\checkout\forms.py                                     79     79     0%   1-141
shop-inventory\checkout\models.py                                    32     17    47%   9-35, 50, 59
shop-inventory\checkout\templatetags\checkout_filters.py              9      9     0%   1-13
shop-inventory\checkout\urls.py                                       3      3     0%   1-5
shop-inventory\checkout\views.py                                     42     42     0%   1-71
shop-inventory\inventory\barcode_gen.py                              25     25     0%   1-47
shop-inventory\inventory\forms.py                                    92     92     0%   1-171
shop-inventory\inventory\models.py                                   37     11    70%   16, 19-20, 23-24, 32, 43, 49-50, 53-54
shop-inventory\inventory\signals.py                                  35     23    34%   11-21, 25-44, 51-54, 59-62
shop-inventory\inventory\urls.py                                      3      3     0%   1-4
shop-inventory\inventory\views.py                                   176    176     0%   1-304
-----------------------------------------------------------------------------------------------
TOTAL                                                               748    610    18%

6 files skipped due to complete coverage.


================================== 3 passed in 0.74s ===================================
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


## TODO
barcode should allow uuid or 6-12 digit string for upc-a/upc-e
add volunteer and admin users
- how does qty mismatch need to work?
- allow to go negative
acknowledgesments page for sponsor and students
shop logo/favicon?
