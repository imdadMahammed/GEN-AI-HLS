from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import pandas as pd
from datetime import datetime
import sqlite3  # For data storage
import logging
import random

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Configuration for Kafka
KAFKA_TOPIC = 'oncology_labvantage_tests'
KAFKA_SERVER = 'localhost:9092'

# Initialize Kafka Producer
def initialize_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_SERVER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info("Kafka Producer initialized successfully.")
        return producer
    except KafkaError as e:
        logging.error(f"Failed to initialize Kafka Producer: {e}")
        raise

# Initialize Kafka Consumer
def initialize_kafka_consumer():
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_SERVER],
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logging.info("Kafka Consumer initialized successfully.")
        return consumer
    except KafkaError as e:
        logging.error(f"Failed to initialize Kafka Consumer: {e}")
        raise

# Simulate data ingestion from LabVantage
def fetch_labvantage_data():
    sample_data = {
        "patient_id": random.randint(1000, 9999),
        "test_id": random.randint(100, 999),
        "test_name": random.choice(["CBC", "Biopsy", "MRI", "CT Scan"]),
        "test_result": random.choice(["Positive", "Negative", "Inconclusive"]),
        "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logging.info(f"Fetched data: {sample_data}")
    return sample_data

# Data transformation
def transform_data(data):
    data['test_date'] = datetime.strptime(data['test_date'], "%Y-%m-%d %H:%M:%S")
    logging.info(f"Transformed data: {data}")
    return data

# Data validation
def validate_data(data):
    required_fields = ["patient_id", "test_id", "test_name", "test_result", "test_date"]
    for field in required_fields:
        if field not in data or data[field] is None:
            logging.error(f"Missing field in data: {field}")
            return False
    logging.info("Data validation passed.")
    return True

# Stream data to Kafka
def stream_to_kafka(producer, data):
    try:
        producer.send(KAFKA_TOPIC, value=data)
        producer.flush()
        logging.info("Data streamed to Kafka successfully.")
    except KafkaError as e:
        logging.error(f"Failed to stream data to Kafka: {e}")
        raise

# Save data to a database
def save_to_database(data):
    conn = sqlite3.connect('oncology_labvantage.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS lab_tests
                 (patient_id INT, test_id INT, test_name TEXT, test_result TEXT, test_date TEXT)''')
    c.execute("INSERT INTO lab_tests VALUES (?, ?, ?, ?, ?)",
              (data['patient_id'], data['test_id'], data['test_name'], data['test_result'], data['test_date'].strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    logging.info("Data saved to database successfully.")

# Retrieve data from the database
def retrieve_data_from_db(query):
    conn = sqlite3.connect('oncology_labvantage.db')
    df = pd.read_sql_query(query, conn)
    conn.close()
    logging.info("Data retrieved from database successfully.")
    return df

# Aggregate data for analysis
def aggregate_data():
    conn = sqlite3.connect('oncology_labvantage.db')
    query = "SELECT test_name, COUNT(*) as test_count FROM lab_tests GROUP BY test_name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    logging.info("Data aggregated successfully.")
    return df

# Visualize data (simple print for this example)
def visualize_data(df):
    logging.info("Data visualization:")
    print(df)

# Error handling and logging
def error_handling_example():
    try:
        # Simulating an operation that could fail
        raise ValueError("An error occurred during processing")
    except ValueError as e:
        logging.error(f"Error: {e}")

# Main function to centralize the process
def centralize_labvantage_tests():
    # Step 1: Initialize Kafka Producer
    producer = initialize_kafka_producer()

    # Step 2: Fetch LabVantage Data
    raw_data = fetch_labvantage_data()

    # Step 3: Transform Data
    transformed_data = transform_data(raw_data)

    # Step 4: Validate Data
    if validate_data(transformed_data):
        # Step 5: Stream to Kafka
        stream_to_kafka(producer, transformed_data)

        # Step 6: Save to Database
        save_to_database(transformed_data)

    # Step 7: Initialize Kafka Consumer
    consumer = initialize_kafka_consumer()

    # Step 8: Consume data from Kafka and process (for example, just print it)
    for message in consumer:
        logging.info(f"Consumed message: {message.value}")
        break

    # Step 9: Retrieve and Aggregate Data
    df = retrieve_data_from_db("SELECT * FROM lab_tests")
    aggregated_df = aggregate_data()

    # Step 10: Visualize Data
    visualize_data(aggregated_df)

    # Example of Error Handling
    error_handling_example()

# Run the centralization process
if __name__ == "__main__":
    centralize_labvantage_tests()
