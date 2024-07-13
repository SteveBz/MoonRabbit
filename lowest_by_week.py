import sqlite3
import pandas as pd
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_valid_periods_in_chunk(chunk_df, period_minutes=60):
    """
    Identify periods where the value has not gone outside the range [350, 500] for at least an hour within a chunk.
    """
    chunk_df['date'] = pd.to_datetime(chunk_df['date'])
    chunk_df = chunk_df.sort_values('date')
    valid_periods = []

    start_idx = 0
    total_length = len(chunk_df)
    while start_idx < total_length:
        end_idx = start_idx
        while end_idx < total_length and (350 <= chunk_df.iloc[end_idx]['value'] <= 500):
            end_idx += 1
            if end_idx < total_length and (chunk_df.iloc[end_idx]['date'] - chunk_df.iloc[start_idx]['date']).seconds / 60 >= period_minutes:
                period_df = chunk_df.iloc[start_idx:end_idx]
                if (period_df['value'] >= 350).all() and (period_df['value'] <= 500).all():
                    valid_periods.append(period_df)
        start_idx = end_idx + 1

    return valid_periods

def get_lowest_mean_co2_per_week(db_path, chunk_size=10000):
    conn = sqlite3.connect(db_path)
    query = """
    SELECT 
        device_id, 
        id, 
        date, 
        sensor, 
        latitude, 
        longitude, 
        type, 
        value, 
        transferred,
        strftime('%Y-%W', date) AS week
    FROM sensor_measurement
    WHERE type = 'co2' AND value >= 350 AND value <= 500
    ORDER BY date
    """

    logger.info("Starting to process chunks from the database.")
    valid_periods = []
    chunk_counter = 0
    for chunk in tqdm(pd.read_sql_query(query, conn, chunksize=chunk_size), desc="Processing chunks"):
        chunk_counter += 1
        logger.info(f"Processing chunk {chunk_counter}")
        valid_periods.extend(find_valid_periods_in_chunk(chunk))
    
    conn.close()
    logger.info("Finished processing chunks from the database.")

    if not valid_periods:
        logger.info("No valid periods found.")
        return pd.DataFrame()

    logger.info("Calculating mean values for valid periods.")
    valid_means = []
    for period in tqdm(valid_periods, desc="Calculating means"):
        mean_value = period['value'].mean()
        start_date = period['date'].min()
        valid_means.append((start_date, mean_value, period['week'].iloc[0]))
    
    logger.info("Finished calculating mean values.")

    # Convert to DataFrame
    valid_means_df = pd.DataFrame(valid_means, columns=['start_date', 'mean_value', 'week'])

    # Get lowest mean value for each week
    lowest_mean_per_week = valid_means_df.groupby('week').apply(lambda x: x.nsmallest(1, 'mean_value')).reset_index(drop=True)

    # Sort by date
    lowest_mean_per_week = lowest_mean_per_week.sort_values('start_date')
    
    logger.info("Finished processing data and returning results.")
    return lowest_mean_per_week

if __name__ == "__main__":
    db_path = 'measurement.db'
    results = get_lowest_mean_co2_per_week(db_path, chunk_size=10000)
    print(results)
