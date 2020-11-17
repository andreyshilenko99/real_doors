import sqlite3
import urllib.request
import json
import boto3
from urllib.error import HTTPError


def download(channel, name):
    s3 = boto3.resource(service_name='s3',
                        endpoint_url='https://storage.yandexcloud.net',
                        aws_access_key_id='I7sXCXtXe7IOGc6GMq52',
                        aws_secret_access_key='0MscH-WU2XkuA2a2RUIKvcv_9FbndHFwbiK4IdYl')

    bucket = s3.Bucket('video-analytics')
    key = bucket.Object('analized/1/' + channel + '/' + name)

    with open(name, 'rb') as data:
        key.upload_fileobj(data)
        data.close()


def r8(channel, time, name, name_p, room):
    body = {
        "auth": "$2y$10$uzsy1VGyAQ.QuPZKBEfUOeFVJi4/9zV2aP5/JhHL0wxbGL8rxlIGO",
        "hotel_id": "1",
        "cam_id": "0",
        "channel_id": channel,
        "event_time": time,
        "event_type_id": "1",
        "event_record": "s3://video-analytics/analized/1/" + channel + "/" + name,
        "event_picture": "s3://video-analytics/analized/1/" + channel + "/" + name_p,
        "object_type_id": "1",
        "object_id": room
    }
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    myurl = "https://r.8h.ru/api/event/create.php"

    req = urllib.request.Request(myurl)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    print(jsondata)
    cursor.execute("SELECT * FROM requests WHERE request=? AND sent=0;", (jsondata,))
    conn.commit()
    in_table = cursor.fetchone()
    try:

        if in_table is None:
            jsondataasbytes = jsondata.encode('utf-8')  # needs to be bytes
            response = urllib.request.urlopen(req, jsondataasbytes)
            data = json.load(response)
            if not data:
                while True:
                    response = urllib.request.urlopen(req, jsondataasbytes)
                    data = json.load(response)
                    if data:
                        break
            cursor.execute("INSERT INTO requests VALUES(?,?)", (jsondata, 1))
            conn.commit()
            return 1
        else:
            cursor.execute("INSERT INTO requests VALUES(?,?)", (jsondata, 0))
            conn.commit()
            return 0
    except HTTPError:
        cursor.execute("INSERT INTO requests VALUES(?,?)", (jsondata, 0))
        conn.commit()


def r8_short(reqs):
    myurl = "https://r.8h.ru/api/event/create.php"
    req = urllib.request.Request(myurl)
    req.add_header('Content-Type', 'application/json; charset=utf-8')

    jsondata = reqs
    print(jsondata)
    jsondataasbytes = jsondata.encode('utf-8')  # needs to be bytes
    response = urllib.request.urlopen(req, jsondataasbytes)
    data = json.load(response)
    if not data:
        while True:
            response = urllib.request.urlopen(req, jsondataasbytes)
            data = json.load(response)
            if data:
                break
    return data
