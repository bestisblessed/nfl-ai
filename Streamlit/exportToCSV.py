import streamlit as st
import pandas as pd
import numpy as np
import sqlite3

### Download data from nfl.db to csv files
conn = sqlite3.connect('nfl.db')  # Replace 'your_database.db' with your database file path
cursor = conn.cursor()
for table_info in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';"):
    table_name = table_info[0]
    df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
    df.to_csv(f'{table_name}.csv', index=False)
conn.close()