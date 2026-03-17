"""
Generate long-form Data Engineering tutorial scripts using OpenAI.
Each tutorial has sections with code blocks, terminal commands, and explanations.
"""
import json
import random
from openai import OpenAI
import config

FALLBACK_TUTORIALS = [
    {
        "title": "Build a Data Pipeline with Apache Airflow",
        "description": "Learn how to build a complete ETL data pipeline using Apache Airflow, from setup to scheduling.",
        "sections": [
            {
                "type": "title_card",
                "heading": "Build a Data Pipeline with Apache Airflow",
                "subheading": "From Zero to Scheduled ETL",
                "narration": "In this tutorial, you'll learn how to build a complete data pipeline using Apache Airflow. We'll go from installation to a fully scheduled ETL workflow.",
            },
            {
                "type": "terminal",
                "heading": "Installing Airflow",
                "content": "$ pip install apache-airflow==2.8.0\n$ airflow db init\n$ airflow users create \\\n    --username admin \\\n    --firstname Admin \\\n    --lastname User \\\n    --role Admin \\\n    --email admin@example.com\n$ airflow webserver --port 8080",
                "narration": "First, let's install Apache Airflow using pip. After installation, we initialize the metadata database with airflow db init. Then we create an admin user and start the webserver on port 8080.",
            },
            {
                "type": "code",
                "heading": "Define the DAG",
                "language": "python",
                "content": "from airflow import DAG\nfrom airflow.operators.python import PythonOperator\nfrom datetime import datetime, timedelta\n\ndefault_args = {\n    'owner': 'data_team',\n    'depends_on_past': False,\n    'start_date': datetime(2024, 1, 1),\n    'retries': 3,\n    'retry_delay': timedelta(minutes=5),\n}\n\ndag = DAG(\n    'etl_pipeline',\n    default_args=default_args,\n    description='Daily ETL Pipeline',\n    schedule_interval='@daily',\n    catchup=False,\n)",
                "narration": "Now let's define our DAG. DAG stands for Directed Acyclic Graph and it represents our workflow. We set default arguments like the owner, start date, and retry policy. The DAG itself is configured to run daily with catchup disabled.",
            },
            {
                "type": "code",
                "heading": "Extract Task",
                "language": "python",
                "content": "import requests\nimport json\n\ndef extract(**kwargs):\n    \"\"\"Extract data from API source.\"\"\"\n    url = 'https://api.example.com/data'\n    response = requests.get(url)\n    data = response.json()\n    \n    # Push to XCom for next task\n    kwargs['ti'].xcom_push(\n        key='raw_data',\n        value=data\n    )\n    print(f'Extracted {len(data)} records')\n    return data\n\nextract_task = PythonOperator(\n    task_id='extract_data',\n    python_callable=extract,\n    dag=dag,\n)",
                "narration": "The extract function pulls data from an API source. We use XCom, which is Airflow's mechanism for passing data between tasks. The function fetches records and pushes them to XCom so the transform task can access them.",
            },
            {
                "type": "code",
                "heading": "Transform Task",
                "language": "python",
                "content": "import pandas as pd\n\ndef transform(**kwargs):\n    \"\"\"Clean and transform extracted data.\"\"\"\n    ti = kwargs['ti']\n    raw_data = ti.xcom_pull(\n        task_ids='extract_data',\n        key='raw_data'\n    )\n    \n    df = pd.DataFrame(raw_data)\n    \n    # Clean: remove nulls, fix types\n    df = df.dropna(subset=['id', 'value'])\n    df['value'] = df['value'].astype(float)\n    df['processed_at'] = pd.Timestamp.now()\n    \n    # Aggregate\n    result = df.groupby('category').agg(\n        total=('value', 'sum'),\n        count=('id', 'count')\n    ).reset_index()\n    \n    ti.xcom_push(key='clean_data',\n                 value=result.to_dict())\n    print(f'Transformed to {len(result)} rows')\n\ntransform_task = PythonOperator(\n    task_id='transform_data',\n    python_callable=transform,\n    dag=dag,\n)",
                "narration": "The transform task pulls the raw data from XCom, converts it to a pandas DataFrame, then cleans and aggregates it. We remove null values, fix data types, add a processing timestamp, and group by category. The cleaned result is pushed back to XCom.",
            },
            {
                "type": "code",
                "heading": "Load Task",
                "language": "python",
                "content": "from sqlalchemy import create_engine\n\ndef load(**kwargs):\n    \"\"\"Load transformed data to warehouse.\"\"\"\n    ti = kwargs['ti']\n    clean_data = ti.xcom_pull(\n        task_ids='transform_data',\n        key='clean_data'\n    )\n    \n    df = pd.DataFrame(clean_data)\n    \n    engine = create_engine(\n        'postgresql://user:pass@host/warehouse'\n    )\n    \n    df.to_sql(\n        'daily_aggregates',\n        engine,\n        if_exists='append',\n        index=False\n    )\n    print(f'Loaded {len(df)} rows to warehouse')\n\nload_task = PythonOperator(\n    task_id='load_data',\n    python_callable=load,\n    dag=dag,\n)\n\n# Define task dependencies\nextract_task >> transform_task >> load_task",
                "narration": "Finally, the load task takes the clean data and writes it to a PostgreSQL data warehouse using SQLAlchemy. We use the append mode so each daily run adds new rows. The last line defines the task order: extract, then transform, then load. That's the classic ETL pattern.",
            },
            {
                "type": "terminal",
                "heading": "Testing the Pipeline",
                "content": "$ airflow dags test etl_pipeline 2024-01-15\n\n[2024-01-15] INFO - Running task: extract_data\n[2024-01-15] INFO - Extracted 1523 records\n[2024-01-15] INFO - Running task: transform_data\n[2024-01-15] INFO - Transformed to 42 rows\n[2024-01-15] INFO - Running task: load_data\n[2024-01-15] INFO - Loaded 42 rows to warehouse\n[2024-01-15] INFO - DAG run completed successfully",
                "narration": "We can test our pipeline using airflow dags test with a specific date. Here you can see all three tasks running in sequence. The extract pulled 1523 records, transform aggregated them to 42 rows, and load pushed them to the warehouse. Everything completed successfully.",
            },
            {
                "type": "title_card",
                "heading": "Key Takeaways",
                "subheading": "What We Learned",
                "narration": "To recap: we installed Airflow, created a DAG with three tasks following the ETL pattern, used XCom for data passing, and tested the pipeline. Airflow handles scheduling, retries, and monitoring for you. Subscribe for more Data Engineering tutorials!",
            },
        ],
        "tags": ["airflow", "etl", "datapipeline", "python", "dataengineering", "tutorial"],
    },
    {
        "title": "Getting Started with dbt for Data Transformation",
        "description": "Learn dbt from scratch: models, tests, documentation, and running your first transformation.",
        "sections": [
            {
                "type": "title_card",
                "heading": "Getting Started with dbt",
                "subheading": "Modern Data Transformation",
                "narration": "dbt, or data build tool, has revolutionized how data teams handle transformations. In this tutorial, you'll learn to set up dbt, write models, add tests, and run transformations against your data warehouse.",
            },
            {
                "type": "terminal",
                "heading": "Install and Initialize dbt",
                "content": "$ pip install dbt-postgres\n$ dbt init my_project\n\nRunning with dbt=1.7.0\nCreating project my_project...\n  Creating dbt_project.yml\n  Creating profiles.yml\n  Creating models/\n  Creating tests/\n  Creating macros/\n\nYour new dbt project is ready!\n\n$ cd my_project\n$ dbt debug\n\nConnection test: OK",
                "narration": "Install dbt with pip, choosing the adapter for your warehouse. Here we use dbt-postgres. Running dbt init creates a project scaffold with folders for models, tests, and macros. After entering the project directory, dbt debug confirms our database connection works.",
            },
            {
                "type": "code",
                "heading": "Staging Model",
                "language": "sql",
                "content": "-- models/staging/stg_orders.sql\n\nWITH source AS (\n    SELECT * FROM {{ source('raw', 'orders') }}\n),\n\nrenamed AS (\n    SELECT\n        id              AS order_id,\n        customer_id,\n        order_date::DATE AS order_date,\n        status,\n        amount::DECIMAL(10,2) AS amount,\n        _loaded_at      AS ingested_at\n    FROM source\n    WHERE id IS NOT NULL\n)\n\nSELECT * FROM renamed",
                "narration": "Our first model is a staging model for orders. Staging models clean raw data by renaming columns, casting types, and filtering nulls. The double curly brace syntax is Jinja templating. The source function references our raw data, which we define in a YAML file.",
            },
            {
                "type": "code",
                "heading": "Mart Model - Revenue by Customer",
                "language": "sql",
                "content": "-- models/marts/fct_customer_revenue.sql\n\nWITH orders AS (\n    SELECT * FROM {{ ref('stg_orders') }}\n),\n\ncustomers AS (\n    SELECT * FROM {{ ref('stg_customers') }}\n),\n\nrevenue AS (\n    SELECT\n        c.customer_id,\n        c.customer_name,\n        c.segment,\n        COUNT(o.order_id)       AS total_orders,\n        SUM(o.amount)           AS total_revenue,\n        MIN(o.order_date)       AS first_order,\n        MAX(o.order_date)       AS last_order\n    FROM customers c\n    LEFT JOIN orders o USING (customer_id)\n    WHERE o.status = 'completed'\n    GROUP BY 1, 2, 3\n)\n\nSELECT * FROM revenue",
                "narration": "Mart models contain business logic and are the tables your analysts query. This model joins staging orders with customers to calculate revenue metrics. The ref function creates dependencies between models, and dbt uses this to build them in the right order.",
            },
            {
                "type": "code",
                "heading": "Schema Tests",
                "language": "yaml",
                "content": "# models/staging/schema.yml\n\nversion: 2\n\nmodels:\n  - name: stg_orders\n    description: \"Cleaned orders from raw source\"\n    columns:\n      - name: order_id\n        description: \"Primary key\"\n        tests:\n          - unique\n          - not_null\n      - name: amount\n        tests:\n          - not_null\n      - name: status\n        tests:\n          - accepted_values:\n              values:\n                - completed\n                - pending\n                - cancelled",
                "narration": "dbt makes testing easy with YAML schema files. Here we define tests for our staging model. We ensure order ID is unique and not null, amount is not null, and status only contains valid values. These tests run automatically and catch data quality issues early.",
            },
            {
                "type": "terminal",
                "heading": "Running dbt",
                "content": "$ dbt run\n\nRunning with dbt=1.7.0\nFound 4 models, 6 tests, 2 sources\n\nConcurrency: 4 threads\n\n1 of 4 START sql view model staging.stg_customers\n2 of 4 START sql view model staging.stg_orders\n2 of 4 OK created view staging.stg_orders      [OK in 0.8s]\n1 of 4 OK created view staging.stg_customers   [OK in 0.9s]\n3 of 4 START sql table model marts.fct_customer_revenue\n3 of 4 OK created table marts.fct_customer_revenue [OK in 1.2s]\n\nCompleted successfully\nDone. PASS=4 WARN=0 ERROR=0\n\n$ dbt test\n\nRunning 6 tests...\nPASS unique_stg_orders_order_id\nPASS not_null_stg_orders_order_id\nPASS not_null_stg_orders_amount\nPASS accepted_values_stg_orders_status\nPASS unique_stg_customers_customer_id\nPASS not_null_stg_customers_customer_id\n\nAll 6 tests passed!",
                "narration": "Running dbt run builds all models in dependency order. Staging models are created as views, the mart model as a table. Everything passes. Then dbt test runs our schema tests. All six tests pass, confirming our data meets quality standards. This is the power of dbt.",
            },
            {
                "type": "title_card",
                "heading": "Key Takeaways",
                "subheading": "dbt Best Practices",
                "narration": "To summarize: dbt turns SQL into a proper engineering workflow with version control, testing, and documentation. Use staging models for cleaning, mart models for business logic, and always add tests. Subscribe for more Data Engineering tutorials every week!",
            },
        ],
        "tags": ["dbt", "sql", "datawarehouse", "dataengineering", "tutorial", "transformation"],
    },
]

SYSTEM_PROMPT = """You are a Data Engineering tutorial creator for YouTube.
Generate a detailed tutorial script for a 10-15 minute video. Return valid JSON only.

Format:
{
  "title": "Tutorial title (max 80 chars)",
  "description": "Brief description for YouTube (max 200 chars)",
  "sections": [
    {
      "type": "title_card",
      "heading": "Main title",
      "subheading": "Subtitle",
      "narration": "Opening narration (2-3 sentences)"
    },
    {
      "type": "terminal",
      "heading": "Section heading",
      "content": "Terminal commands and output (use $ prefix for commands)",
      "narration": "Detailed explanation (3-5 sentences)"
    },
    {
      "type": "code",
      "heading": "Section heading",
      "language": "python|sql|yaml|bash",
      "content": "Code content with proper formatting",
      "narration": "Detailed explanation (3-5 sentences)"
    }
  ],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
}

Rules:
- Include 6-10 sections (title card, 5-8 content sections, closing card)
- Each narration should be 3-5 sentences for depth
- Code/terminal content should be realistic and educational
- Cover practical Data Engineering topics
- Never repeat topics from: {used_topics}
"""


def generate_tutorial(used_topics: list[str] | None = None) -> dict:
    """Generate a long-form tutorial script."""
    used_topics = used_topics or []

    if config.OPENAI_API_KEY:
        try:
            return _generate_with_openai(used_topics)
        except Exception as e:
            print(f"[WARN] OpenAI generation failed: {e}. Using fallback.")

    available = [t for t in FALLBACK_TUTORIALS if t["title"] not in used_topics]
    if not available:
        available = FALLBACK_TUTORIALS
    return random.choice(available)


def _generate_with_openai(used_topics: list[str]) -> dict:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(used_topics=", ".join(used_topics))},
            {"role": "user", "content": "Generate a new Data Engineering tutorial script for a 10-15 minute YouTube video."},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
        max_tokens=4000,
    )
    return json.loads(response.choices[0].message.content)
