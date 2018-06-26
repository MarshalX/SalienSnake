# SalienSnake
A simple bot written on Python for the Steam 2018 summer sale.

# Features:
* search for high-level zones on all planets;
* maximize experience;
* cross-platform;
* work without a browser;
* stable work (error handling and recovery);
* multi-account support with threading;
* getting a list of active planets;
* specifying  for output of Steam API response;

# Requirements
* [Python 3](https://www.python.org/)
* [requests](https://pypi.org/project/requests/)

# Usage
```
python SalienSnake.py [--token <token>] [--file <filename with extension>] [--language <language>] [--list-planets] [--debug]
```

* Modes:
    * **-t, --token (single account mode)** - Token value from https://steamcommunity.com/saliengame/gettoken
    * **-f, --file (multi-account mode)** - File with tokens (one per line)
* **-l, --list-planets** - Print list with planet names and IDs
* **--language (default: english)** - Language (english, russian, etc.)
* **-d, --debug (default: False)** - Enable debug mode
# Examples
### Single account example:
```
python SalienSnake.py --token nizqvw1sd9d4gf2nwecrg5n26e1zl80l
python SalienSnake.py --token h0s07sgjfhzhe19fxri1cf9fofm8ubqv --list-planets
```

### Multi-account example

Example of file with tokens:
```
nizqvw1sd9d4gf2nwecrg5n26e1zl80l
6ibdq3baf21w1xca1x5gtgx2iwez6mn1
h0s07sgjfhzhe19fxri1cf9fofm8ubqv
```

Example use:
```
python SalienSnake.py --file tokens.txt
python SalienSnake.py --file tokens.txt --language russian
```
# Screenshot
![SalienSnake screenshot](https://i.imgur.com/ByURj1c.png)

# Useful links:
* [Download Python](https://www.python.org/downloads/)
* [How to Install Python on Windows](https://www.howtogeek.com/197947/how-to-install-python-on-windows/)
* [How to install requests module in Python 3](https://stackoverflow.com/questions/30362600/how-to-install-requests-module-in-python-3-4-instead-of-2-7)
* [How to Run a Python Script via a File](https://www.pythoncentral.io/execute-python-script-file-shell/)
* [Post on reddit](https://www.reddit.com/r/salien/comments/8t2fpi/saliensnake_a_simple_bot_for_the_steam_2018/)
* [Setup guide by lappro](https://www.reddit.com/r/salien/comments/8szkv4/best_bot/e15s8m8)

# License
GNU General Public License v3.0
