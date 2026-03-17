"""
Generate Data Engineering video scripts using OpenAI (with fallback topics).
"""
import json
import random
from openai import OpenAI
import config

# Fallback topics if OpenAI is unavailable
FALLBACK_TOPICS = [
    {
        "title": "What is a Data Lake?",
        "hook": "Your company is drowning in data. Here's the life raft.",
        "segments": [
            "A data lake stores raw data in its native format.",
            "Unlike warehouses, data lakes keep data unstructured.",
            "Tools like Apache Spark process data on read.",
            "Schema-on-read gives flexibility but needs governance.",
            "Use cases: ML training, log analytics, IoT streams.",
        ],
        "tags": ["datalake", "dataengineering", "bigdata", "spark", "datapipeline"],
    },
    {
        "title": "ETL vs ELT Explained",
        "hook": "ETL or ELT? Pick wrong and your pipeline breaks.",
        "segments": [
            "ETL transforms data BEFORE loading it.",
            "ELT loads raw data first, transforms inside the warehouse.",
            "Cloud warehouses like BigQuery make ELT powerful.",
            "ETL suits on-prem, ELT suits cloud-native stacks.",
            "Modern data teams prefer ELT for flexibility.",
        ],
        "tags": ["etl", "elt", "dataengineering", "bigquery", "datawarehouse"],
    },
    {
        "title": "Apache Kafka in 60 Seconds",
        "hook": "Billions of events per day. One tool handles it all.",
        "segments": [
            "Kafka is a distributed event streaming platform.",
            "Producers write messages. Consumers read them.",
            "Topics partition data for parallel processing.",
            "Kafka guarantees ordering within a partition.",
            "Used by LinkedIn, Uber, Netflix for real-time data.",
        ],
        "tags": ["kafka", "streaming", "dataengineering", "realtime", "eventdriven"],
    },
    {
        "title": "Why dbt Changed Everything",
        "hook": "SQL just became a full engineering framework.",
        "segments": [
            "dbt lets you transform data using SELECT statements.",
            "It adds version control and testing to SQL.",
            "Models are modular and reusable transformations.",
            "dbt builds a DAG of your entire data pipeline.",
            "Analytics engineers love it. You will too.",
        ],
        "tags": ["dbt", "sql", "dataengineering", "analytics", "datatransformation"],
    },
    {
        "title": "Star Schema vs Snowflake Schema",
        "hook": "Your warehouse schema choice affects EVERYTHING.",
        "segments": [
            "Star schema: one fact table, denormalized dimensions.",
            "Snowflake schema: normalized dimensions with sub-tables.",
            "Star is faster for queries. Snowflake saves storage.",
            "Most modern warehouses prefer star for simplicity.",
            "Choose based on query patterns, not theory.",
        ],
        "tags": ["datamodeling", "starschema", "datawarehouse", "dataengineering", "sql"],
    },
    {
        "title": "Data Partitioning Explained",
        "hook": "One trick to make your queries 100x faster.",
        "segments": [
            "Partitioning splits a table into smaller chunks.",
            "Queries only scan relevant partitions, not the whole table.",
            "Common keys: date, region, customer ID.",
            "Hive-style partitioning uses folder structures.",
            "Over-partitioning creates too many small files. Balance it.",
        ],
        "tags": ["partitioning", "dataengineering", "bigdata", "performance", "sql"],
    },
    {
        "title": "What is Apache Airflow?",
        "hook": "Your data pipelines need an orchestrator. Meet Airflow.",
        "segments": [
            "Airflow schedules and monitors data workflows.",
            "Workflows are defined as Python DAGs.",
            "Tasks run in order with dependency management.",
            "Built-in retry logic and alerting for failures.",
            "Used by Airbnb, Spotify, and thousands of teams.",
        ],
        "tags": ["airflow", "orchestration", "dataengineering", "python", "datapipeline"],
    },
    {
        "title": "CDC: Capture Every Change",
        "hook": "Your database changed. Your pipeline didn't notice.",
        "segments": [
            "CDC stands for Change Data Capture.",
            "It tracks inserts, updates, and deletes in real time.",
            "Debezium reads database transaction logs for CDC.",
            "No more expensive full-table scans every night.",
            "CDC powers real-time analytics and sync.",
        ],
        "tags": ["cdc", "debezium", "dataengineering", "realtime", "database"],
    },
    {
        "title": "Data Quality: The Silent Killer",
        "hook": "Bad data costs companies millions. Here is how to fix it.",
        "segments": [
            "Data quality means accuracy, completeness, and timeliness.",
            "Great Expectations lets you write data tests.",
            "Schema validation catches structural issues early.",
            "Freshness checks ensure data is not stale.",
            "Invest in quality now or pay in bad decisions later.",
        ],
        "tags": ["dataquality", "dataengineering", "testing", "greatexpectations", "data"],
    },
    {
        "title": "Medallion Architecture Explained",
        "hook": "Bronze, Silver, Gold. The layers of modern data.",
        "segments": [
            "Bronze layer: raw ingested data, no transformations.",
            "Silver layer: cleaned, validated, deduplicated data.",
            "Gold layer: business-ready aggregated tables.",
            "Each layer adds quality and trust to the data.",
            "Databricks popularized this pattern. It works everywhere.",
        ],
        "tags": ["medallion", "databricks", "dataengineering", "datalakehouse", "architecture"],
    },
]

SYSTEM_PROMPT = """You are a Data Engineering content creator for YouTube Shorts.
Generate a script for a 50-second vertical video. Return valid JSON only.

Format:
{
  "title": "Short catchy title (max 60 chars)",
  "hook": "Attention-grabbing opening line (max 15 words)",
  "segments": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

Rules:
- Each segment is one concise sentence displayed on screen (~8 seconds each)
- Keep language simple, punchy, and visual
- Cover practical data engineering topics: pipelines, tools, architectures, best practices
- Never repeat a topic from this list: {used_topics}
"""


def generate_script(used_topics: list[str] | None = None) -> dict:
    """Generate a video script. Uses OpenAI if available, else random fallback."""
    used_topics = used_topics or []

    if config.OPENAI_API_KEY:
        try:
            return _generate_with_openai(used_topics)
        except Exception as e:
            print(f"[WARN] OpenAI generation failed: {e}. Using fallback.")

    # Fallback: pick a random topic not yet used
    available = [t for t in FALLBACK_TOPICS if t["title"] not in used_topics]
    if not available:
        available = FALLBACK_TOPICS  # reset if all used
    return random.choice(available)


def _generate_with_openai(used_topics: list[str]) -> dict:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(used_topics=", ".join(used_topics))},
            {"role": "user", "content": "Generate a new Data Engineering YouTube Short script."},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
        max_tokens=500,
    )
    return json.loads(response.choices[0].message.content)
