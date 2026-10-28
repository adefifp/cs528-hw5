import os
import time
import logging
from datetime import datetime
from flask import Flask, request, Response
from google.cloud import storage
from google.cloud.exceptions import NotFound
import pymysql
from dbutils.pooled_db import PooledDB

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

BUCKET_NAME = os.environ.get("BUCKET_NAME", "cs528-pagerank-eddielu-1790373540")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "cs528password")
DB_NAME = os.environ.get("DB_NAME", "cs528_hw5")

BANNED_COUNTRIES = {"North Korea", "Iran", "Cuba", "Myanmar", "Syria"}

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

db_pool = PooledDB(
    creator=pymysql,
    maxconnections=50,
    mincached=15,
    maxcached=30,
    blocking=True,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    autocommit=True
)

perf_stats = {
    "header_parsing": {"total_time": 0.0, "count": 0},
    "gcs_fetch": {"total_time": 0.0, "count": 0},
    "db_insert": {"total_time": 0.0, "count": 0},
    "response_dispatch": {"total_time": 0.0, "count": 0}
}

def extract_and_process_headers(req):
    t0 = time.perf_counter()
    country = req.headers.get("X-country", "Unknown")
    client_ip = req.headers.get("X-client-IP", req.remote_addr)
    gender = req.headers.get("X-gender", "Unknown")
    age = req.headers.get("X-age", "Unknown")
    income = req.headers.get("X-income", "Unknown")
    time_str = req.headers.get("X-time")
    
    if time_str:
        try:
            parsed_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            parsed_time = datetime.utcnow()
    else:
        parsed_time = datetime.utcnow()
        
    is_banned = country in BANNED_COUNTRIES

    data = {
        "country": country,
        "client_ip": client_ip,
        "gender": gender,
        "age": age,
        "income": income,
        "time_of_day": parsed_time,
        "is_banned": is_banned
    }
    elapsed = time.perf_counter() - t0
    perf_stats["header_parsing"]["total_time"] += elapsed
    perf_stats["header_parsing"]["count"] += 1
    return data

def fetch_file_from_storage(filename):
    t0 = time.perf_counter()
    content = None
    try:
        blob_path = f"files/{filename}" if not filename.startswith("files/") else filename
        blob = bucket.blob(blob_path)
        content = blob.download_as_bytes()
    except NotFound:
        content = None
    except Exception:
        content = None
    elapsed = time.perf_counter() - t0
    perf_stats["gcs_fetch"]["total_time"] += elapsed
    perf_stats["gcs_fetch"]["count"] += 1
    return content

def insert_db_record(meta, filename, status_code):
    t0 = time.perf_counter()
    conn = db_pool.connection()
    try:
        with conn.cursor() as cursor:
            if status_code == 200:
                sql = """
                    INSERT INTO successful_requests 
                    (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    meta["country"],
                    meta["client_ip"],
                    meta["gender"],
                    meta["age"],
                    meta["income"],
                    meta["is_banned"],
                    meta["time_of_day"],
                    filename
                ))
            else:
                sql = """
                    INSERT INTO failed_requests 
                    (time_of_request, requested_file, error_code)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (
                    meta["time_of_day"],
                    filename,
                    status_code
                ))
    finally:
        conn.close()
    elapsed = time.perf_counter() - t0
    perf_stats["db_insert"]["total_time"] += elapsed
    perf_stats["db_insert"]["count"] += 1

def build_response(body, status_code, content_type="text/html"):
    t0 = time.perf_counter()
    resp = Response(body, status=status_code, content_type=content_type)
    elapsed = time.perf_counter() - t0
    perf_stats["response_dispatch"]["total_time"] += elapsed
    perf_stats["response_dispatch"]["count"] += 1
    return resp

@app.route('/files/<filename>', methods=['GET'])
def get_file(filename):
    meta = extract_and_process_headers(request)
    file_bytes = fetch_file_from_storage(filename)
    
    if file_bytes is None:
        status_code = 404
        insert_db_record(meta, f"/files/{filename}", status_code)
        return build_response("File Not Found", 404, "text/plain")
        
    status_code = 200
    insert_db_record(meta, f"/files/{filename}", status_code)
    return build_response(file_bytes, 200, "text/html")

@app.route('/stats', methods=['GET'])
def get_stats():
    results = {}
    for stage, data in perf_stats.items():
        count = data["count"]
        total = data["total_time"]
        avg_ms = (total / count * 1000.0) if count > 0 else 0.0
        results[stage] = {
            "total_seconds": round(total, 4),
            "total_invocations": count,
            "average_ms": round(avg_ms, 4)
        }
    return results, 200

@app.errorhandler(405)
def method_not_allowed(e):
    meta = extract_and_process_headers(request)
    insert_db_record(meta, request.path, 501)
    return build_response("Not Implemented", 501, "text/plain")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)
