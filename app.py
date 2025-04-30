from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
import sqlite3
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
import traceback

app = Flask(__name__)

# Set up the SQLite database path
DB_PATH = '/home/ec2-user/API.db'

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

# Route to upload CSV file
@app.route('/upload', methods=['GET','POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file)
            
            # Normalize the data
            df_normalized = normalize_data(df)
            
            # Use direct SQLite connection instead of SQLAlchemy
            success = insert_to_sqlite(df_normalized, 'csv_data')
            
            if success:
                return jsonify({"message": "File uploaded and data stored successfully!"}), 200
            else:
                return jsonify({"error": "Failed to insert data into database"}), 500
                
        except Exception as e:
            error_detail = traceback.format_exc()
            return jsonify({
                "error": f"This is Error processing file: {str(e)}",
                "detail": error_detail
            }), 500
    else:
        return jsonify({"error": "Invalid file format. Only CSV is allowed."}), 400

# Function to insert data directly using sqlite3
def insert_to_sqlite(df, table_name):
    try:
        # Connect to SQLite
        conn = sqlite3.connect(DB_PATH)
        
        # Check if table exists, if not create it
        cursor = conn.cursor()
        
        # Get column names and types
        columns = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                columns.append(f'"{col}" REAL')
            else:
                columns.append(f'"{col}" TEXT')
        
        # Create table if not exists
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        cursor.execute(create_table_sql)
        
        # Insert data
        for _, row in df.iterrows():
            # Replace NaN values with None (SQL NULL)
            row_values = [None if pd.isna(val) else val for val in row]
            
            placeholders = ', '.join(['?' for _ in range(len(df.columns))])
            column_names = ', '.join([f'"{col}"' for col in df.columns])
            
            insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            cursor.execute(insert_sql, row_values)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error in insert_to_sqlite: {str(e)}")
        return False

# Function to check if the file is a CSV
def allowed_file(filename):
    return filename.endswith('.csv')

# Function to normalize data
def normalize_data(df):
    # Select only numeric columns for normalization
    numeric_columns = df.select_dtypes(include=['number']).columns
    
    if len(numeric_columns) > 0:
        scaler = StandardScaler()
        # Normalize only numeric columns
        df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
    
    return df

# Debug function to print package versions
@app.route('/debug', methods=['GET'])
def debug_versions():
    import sqlalchemy
    import pandas
    import sqlite3
    return jsonify({
        "sqlalchemy_version": sqlalchemy.__version__,
        "pandas_version": pandas.__version__,
        "sqlite3_version": sqlite3.sqlite_version
    })

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)