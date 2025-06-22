from flask import Flask, jsonify, request, send_from_directory
import os
import requests
import psycopg2

app = Flask(__name__, static_folder=".", static_url_path="")

# Existing routes...

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

AIRFLOW_BASE_URL = 
AIRFLOW_AUTH =
DAG_ID = "nasa_apod_postgres"

# POST /trigger-dag
@app.route("/trigger-dag", methods=["POST"])
def trigger_dag():
    response = requests.post(
        f"{AIRFLOW_BASE_URL}/dags/{DAG_ID}/dagRuns",
        auth=AIRFLOW_AUTH,
        json={"conf": {}}
    )
    if response.status_code == 200:
        return jsonify({"message": "DAG triggered!"})
    else:
        return jsonify({"error": response.text}), 500

# GET /dag-status
@app.route("/dag-status", methods=["GET"])
def dag_status():
    response = requests.get(
        f"{AIRFLOW_BASE_URL}/dags/{DAG_ID}/dagRuns?order_by=-execution_date&limit=1",
        auth=AIRFLOW_AUTH
    )
    if response.status_code == 200:
        dag_runs = response.json().get("dag_runs", [])
        if dag_runs:
            return jsonify({
                "state": dag_runs[0]["state"],
                "run_id": dag_runs[0]["dag_run_id"]
            })
        return jsonify({"state": "no_runs"})
    else:
        return jsonify({"error": response.text}), 500

# GET /get-latest-article
@app.route("/get-latest-article", methods=["GET"])
def get_latest_article():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT title, summary, url, published_at
        FROM space_articles
        ORDER BY published_at DESC
        LIMIT 1;
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({
            "title": row[0],
            "summary": row[1],
            "url": row[2],
            "published_at": row[3]
        })
    else:
        return jsonify({"message": "No article found."})

if __name__ == "__main__":
    app.run(debug=True,port=5000)
