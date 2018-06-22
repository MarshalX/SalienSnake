# SalienSnake
A simple bot for the Steam 2018 summer sale. Multi-Account Support.

# Requirements
* Python 3
* requests

# Usage

## Single account
```
python3 SalienSnake.py [--token <token>] [--planet <planet id>] [--list-planets] [--language <language>]
```
Arguments:
* **-t, --token (required)** - Token value from https://steamcommunity.com/saliengame/gettoken
* **-p, --planet** - Planet ID
* **-l, --list-planets** - Print list with planet names and IDs
* **--language** - Language (english, russian, etc.)

Examples:
```
python3 SalienSnake.py --token nizqvw1sd9d4gf2nwecrg5n26e1zl80l
python3 SalienSnake.py --token 6ibdq3baf21w1xca1x5gtgx2iwez6mn1 --planet 1
python3 SalienSnake.py --token h0s07sgjfhzhe19fxri1cf9fofm8ubqv --list-planets
```

## Multi-account
```
python3 SalienSnake.py [--file <filename with extension>]
```
Arguments:
* **-f, --file (required)** - File with tokens (one per line)

Example of file with tokens:
```
nizqvw1sd9d4gf2nwecrg5n26e1zl80l
6ibdq3baf21w1xca1x5gtgx2iwez6mn1
h0s07sgjfhzhe19fxri1cf9fofm8ubqv
```

Example use:
```
python3 SalienSnake.py --file tokens.txt
```

# License
GNU General Public License v3.0
