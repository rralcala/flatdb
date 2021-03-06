import leveldb
import ujson as json
from flask import request, g

from flatdb import flatdb_app


JSON = {'Content-Type': 'application/json'}
BIN = {'Content-Type': 'application/octet-stream'}


def ensure_db():
    if 'db' not in g:
        g.db = leveldb.LevelDB(flatdb_app.config['DB'])


def put():
    ensure_db()
    keys = request.args.items(multi=True)
    batch = leveldb.WriteBatch()
    for k, v in keys:
        batch.Put(k.encode(), v.encode())
    g.db.Write(batch)
    return '', 201, JSON


def putblob():
    ensure_db()
    key = request.args.get("key")
    batch = leveldb.WriteBatch()
    batch.Put(key.encode(), request.get_data())
    g.db.Write(batch)
    return '', 201, JSON


def get():
    ensure_db()
    keys = request.args.getlist('key')
    if not keys:
        return '', 204, JSON
    response = {}
    for k in keys:
        try:
            response[k] = g.db.Get(k.encode()).decode()
        except KeyError:
            pass
    if not response:
        return '', 404, JSON
    return json.dumps(response), 200, JSON


def getblob():
    ensure_db()
    key = request.args.get('key')
    if not key:
        return '', 204, JSON
    response = None

    try:
        response = g.db.Get(key.encode())
    except KeyError:
        pass
    if not response:
        return '', 404, JSON
    return response, 200, BIN


def getrange():
    ensure_db()
    from_key = request.args.get('from').encode()
    response = {}
    vals = g.db.RangeIter(key_from=from_key)
    for k, v in vals:
        response[k.decode()] = v.decode()
    if not response:
        return '', 404, JSON
    return json.dumps(response), 200, JSON


def delete():
    ensure_db()
    keys = request.args.getlist('key')
    batch = leveldb.WriteBatch()
    for k in keys:
        batch.Delete(k.encode())
    g.db.Write(batch)
    return '', 200, JSON


def define_urls(app):
    app.add_url_rule('/put', view_func=put, methods=['GET'])
    app.add_url_rule('/putblob', view_func=putblob, methods=['PUT'])
    app.add_url_rule('/get', view_func=get, methods=['GET'])
    app.add_url_rule('/getblob', view_func=getblob, methods=['GET'])
    app.add_url_rule('/getrange', view_func=getrange, methods=['GET'])
    app.add_url_rule('/delete', view_func=delete, methods=['GET'])
