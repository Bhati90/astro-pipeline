from airflow import DAG
from airflow.providers.http.operators.http import HttpOperator
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import json


## Define the DAG
with DAG(
    dag_id='nasa_apod_postgres',
    start_date=datetime.now() - timedelta(days=1),
    schedule='@daily',  # Changed from schedule_interval
    catchup=False
) as dag:
    
    ## step 1: Create the table if it doesnt exists

    @task
    def create_table():
        ## initialize the Postgreshook
        postgres_hook=PostgresHook(postgres_conn_id="my_postgres_connection")

        create_table_query = """
        CREATE TABLE IF NOT EXISTS space_articles (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            summary TEXT,
            url TEXT,
            published_at TIMESTAMP
        );
        """
        ## Execute the table creation query
        postgres_hook.run(create_table_query)


    extract_articles = HttpOperator(
        task_id='extract_articles',
        http_conn_id='space_news_api',  # You need to add this in Airflow Connections with base_url=https://api.spaceflightnewsapi.net
        endpoint='/articles?limit=1',
        method='GET',
        response_filter=lambda response: response.json(),  # parses JSON
    )

    

    ## Step 3: Transform the data(Pick the information that i need to save)
    @task
    def transform_article_data(response):
        article = response['results'][0]  # Only first article
        return {
            'title': article.get('title', ''),
            'summary': article.get('summary', ''),
            'url': article.get('url', ''),
            'published_at': article.get('published_at', '')
        }



    ## step 4:  Load the data into Postgres SQL
    @task
    def load_data_to_postgres(article_data):
        postgres_hook = PostgresHook(postgres_conn_id='my_postgres_connection')
        insert_query = """
        INSERT INTO space_articles (title, summary, url, published_at)
        VALUES (%s, %s, %s, %s);
        """
        postgres_hook.run(insert_query, parameters=(
            article_data['title'],
            article_data['summary'],
            article_data['url'],
            article_data['published_at']
        ))

    create_table() >> extract_articles
    transformed = transform_article_data(extract_articles.output)
    load_data_to_postgres(transformed)