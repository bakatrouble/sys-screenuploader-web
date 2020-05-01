import json
import re
from xml.etree import ElementTree

from Crypto.Cipher import AES
import requests


with open('keydump.bin', 'rb') as f:
    encryptor = AES.new(f.read())


data = []
xml = requests.get('http://nswdb.com/xml.php').text
root = ElementTree.fromstring(xml)
for release in root.findall('release'):
    name = release.find('name').text
    name = re.sub(r' \[.+?\]', '', name)
    tids = release.find('titleid').text.split()[0]
    tids = tids.replace('[', '')  # id 1794

    if '+' in tids:
        tids = tids.split('+')
    elif '-' in tids:  # id 1434
        prefix = tids[:4]
        tids = [prefix + tid[1:13] for tid in tids[4:].split(',')]
    else:
        tids = [tids]

    for tid in tids:
        tid = tid.replace('\ufeff', '')  # id 1651
        payload = int(tid, 16).to_bytes(16, 'little')
        data.append({
            'name': name,
            'tid': tid,
            'hash': encryptor.encrypt(payload).hex().upper(),
        })

with open('title_db.json', 'w') as f:
    json.dump(data, f, indent=4)
