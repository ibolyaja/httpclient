import socket
import ssl
import sys
import re


def parseurl(url):
    s = url.split("//")
    if s[0] == "http:":
        s1 = s[1].split("/", maxsplit=1)
        if len(s1) == 2:
            return s1[0].strip(), 80, "/" + s1[1].strip()
        else:
            return s1[0].strip(), 80, "/"
    elif s[0] == "https:":
        s1 = s[1].split("/", maxsplit=1)
        if len(s1) == 2:
            return s1[0].strip(), 443, "/" + s1[1].strip()
        else:
            return s1[0].strip(), 443, "/"
    else:
        s1 = s[0].split("/", maxsplit=1)
        if len(s1) == 2:
            return s1[0].strip(), 80, "/" + s1[1].strip()
        else:
            return s1[0].strip(), 80, "/"


def checkredirectstatus(s):
    for code in ("301", "302", "303", "307", "308"):
        if re.search(code, s):
            return True
    return False


if len(sys.argv) != 2:
    sys.exit(1)
url = sys.argv[1]

while True:
    host, port, path = parseurl(url)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

    except socket.error as e:
        print(str(e), file=sys.stderr)
        sys.exit()

    try:
        sock.connect((host, port))
        if port == 443:
            sock = ssl.wrap_socket(sock)

    except socket.error as e:
        print(str(e), file=sys.stderr)
        sys.exit()

    head = dict()
    bytecount = 0
    f = sock.makefile(mode='rwb', encoding='utf-8')

    req = "GET %s HTTP/1.1\r\n" % path
    req += "Host:%s\r\n\r\n" % host
    f.write(req.encode())
    f.flush()
    status = bytes.decode(f.readline()).strip()

    while True:
        l = bytes.decode(f.readline())
        if re.search(":", l):
            tag = l.split(":", 1)
            key = tag[0].strip().lower()
            head[key] = tag[1].strip()
        else:
            break
    if re.search("200", status):
        if "transfer-encoding" in head.keys():
            if head["transfer-encoding"] == "chunked":
                while True:
                    l = f.readline()
                    dl = bytes.decode(l)
                    isnum = False
                    try:
                        bytenum = int(dl, 16)
                        if bytenum == 0:
                            break
                        isnum = True
                    except ValueError as e:
                        isnum = False
                    if not isnum:
                        sys.stdout.buffer.write(l)
                sock.close()
                break
        else:
            while True:
                l = f.readline()
                bytecount += len(l)
                sys.stdout.buffer.write(l)
                if bytecount >= int(head["content-length"]):
                    break
            sock.close()
            break

    elif checkredirectstatus(status):
        url = head["location"].strip()
        sock.close()
    else:
        while True:
            l = f.readline()
            bytecount += len(l)
            print(l, file=sys.stderr)
            if bytecount >= int(head["content-length"]):
                break
        sys.exit(1)
