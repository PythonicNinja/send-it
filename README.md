# send it

Project allows to secretly without any dependencies other than ngrok to tunnel directly text / file / directory on p2p.

Only dependencies are installed on your local:
1. python3 (no dependencies, only builtins)
2. ngrok for creation of tunnel with https

usage:

```bash
# sharing text
python3 main.py ala ma kota

# sharing longer text
python3 main.py "lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim ven in culpa qui officia deserunt mollit anim id est laborum. Excepteur sint et sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem ips"

# sharing file
python3 main.py ~/Desktop/your_file.txt

# sharing folder
python3 main.py ~/Desktop/something_to_share

```

example run:
```
|  ~/PycharmProjects/send-it   (main)
| => python3 main.py "client_id=12345, client_secret=321"
Created temporary directory: /var/folders/ty/v5g_gm0x0sv7dtxrh28tg_yc0000gn/T/tmpsc5ekv18
Detected text input, creating index.html
Starting HTTP server on port 8080...

Send this url to access message:
  https://f5b9-2a09-bac1-5bc0-38-00-39b-5d.ngrok-free.app

Press Ctrl+C to stop the server and exit
127.0.0.1 - - [21/Feb/2025 13:19:31] "GET / HTTP/1.1" 200 -
```

![Example Screenshot](https://i.imgur.com/5q7kz5v.png)
