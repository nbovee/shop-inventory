# Shop Prototype Repository

This repository is the development repository for the Rowan Shop & Pantry Inventory System
To contribute, please read the guidelines here : [Contributing.md](CONTRIBUTING.md)

<div markdown="1">

[![Build](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nbovee/shop-inventory/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nbovee/shop-inventory/badge.svg?branch=main)](https://coveralls.io/github/nbovee/shop-inventory?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>
<hr>

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
============================================================= test session starts ==============================================================
platform win32 -- Python 3.12.5, pytest-8.3.4, pluggy-1.5.0
django: version: 4.2.16, settings: _core.settings (from ini)
rootdir: C:\CODE\shop-inventory
configfile: pyproject.toml
plugins: cov-6.0.0, django-4.9.0
collected 58 items

shop-inventory\tests\checkout\test_views.py ........                                                                                      [ 13%]
shop-inventory\tests\checkout\url_tests.py ..                                                                                             [ 17%]
shop-inventory\tests\checkout\views_tests.py .......                                                                                      [ 29%]
shop-inventory\tests\inventory\test_forms.py ............                                                                                 [ 50%]
shop-inventory\tests\inventory\test_views.py ....................                                                                         [ 84%]
shop-inventory\tests\url_tests.py ........                                                                                                [ 98%]
shop-inventory\tests\inventory\tests.py .                                                                                                 [100%]

---------- coverage: platform win32, python 3.12.5-final-0 -----------
Name                                                       Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------------
shop-inventory\_core\models.py                                 7      1    86%   13
shop-inventory\_core\signals.py                               28      5    82%   18, 39-40, 48-49
shop-inventory\_core\views.py                                 17      1    94%   12
shop-inventory\checkout\forms.py                              79     12    85%   26, 30-32, 45, 83, 105, 124-125, 129-130, 136
shop-inventory\checkout\models.py                             32      3    91%   35, 50, 59
shop-inventory\checkout\templatetags\checkout_filters.py       9      4    56%   10-13
shop-inventory\checkout\views.py                              49      5    90%   20-21, 61-62, 67
shop-inventory\inventory\barcode_gen.py                       27      3    89%   30-38
shop-inventory\inventory\forms.py                             95     12    87%   30-31, 63-65, 98-100, 111-113, 159
shop-inventory\inventory\models.py                            51      6    88%   44-45, 79-80, 83-84
shop-inventory\inventory\signals.py                           35      2    94%   21, 36
shop-inventory\inventory\views.py                            175     51    71%   71, 78-79, 87-88, 101-110, 116-137, 149-155, 196-201, 207-208, 220-226, 256-257, 262
----------------------------------------------------------------------------------------
TOTAL                                                        689    105    85%

8 files skipped due to complete coverage.


============================================================== 58 passed in 7.77s ==============================================================
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
