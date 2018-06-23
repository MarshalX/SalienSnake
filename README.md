# SalienSnake
A simple bot for the Steam 2018 summer sale. Multi-Account Support.

# Requirements
* Python 3
* requests

# Usage

## Single account
```
python SalienSnake.py [--token <token>] [--planet <planet id>] [--list-planets] [--language <language>]
```
Arguments:
* **-t, --token (required)** - Token value from https://steamcommunity.com/saliengame/gettoken
* **-p, --planet** - Planet ID
* **-l, --list-planets** - Print list with planet names and IDs
* **--language** - Language (english, russian, etc.)
* **-d, --debug** - Enable debug mode

Examples:
```
python SalienSnake.py --token nizqvw1sd9d4gf2nwecrg5n26e1zl80l
python SalienSnake.py --token 6ibdq3baf21w1xca1x5gtgx2iwez6mn1 --planet 1
python SalienSnake.py --token h0s07sgjfhzhe19fxri1cf9fofm8ubqv --list-planets
```

## Multi-account
```
python SalienSnake.py [--file <filename with extension>]
```
Arguments:
* **-f, --file (required)** - File with tokens (one per line)
* **-d, --debug** - Enable debug mode

Example of file with tokens:
```
nizqvw1sd9d4gf2nwecrg5n26e1zl80l
6ibdq3baf21w1xca1x5gtgx2iwez6mn1
h0s07sgjfhzhe19fxri1cf9fofm8ubqv
```

Example use:
```
python SalienSnake.py --file tokens.txt
```

# Useful links:
* [Download Python](https://www.python.org/downloads/)
* [How to Install Python on Windows](https://www.howtogeek.com/197947/how-to-install-python-on-windows/)
* [How to install requests module in Python 3](https://stackoverflow.com/questions/30362600/how-to-install-requests-module-in-python-3-4-instead-of-2-7)
* [How to Run a Python Script via a File](https://www.pythoncentral.io/execute-python-script-file-shell/)
* [Post on reddit](https://www.reddit.com/r/salien/comments/8t2fpi/saliensnake_a_simple_bot_for_the_steam_2018/)
* [Setup guide by lappro](https://www.reddit.com/r/salien/comments/8szkv4/best_bot/e15s8m8)

# License
GNU General Public License v3.0
