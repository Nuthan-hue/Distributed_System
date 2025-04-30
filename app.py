from flask import Flask, request, jsonify, render_template
import pandas as pd
from sqlalchemy import create_engine, Table, Column, MetaData
from sqlalchemy.types import String, Float
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Set up the SQLite database engine
#DATABASE_URI = 'sqlite:///API.db'
DATABASE_URI = 'sqlite:////home/ec2-user/API.db'

engine = create_engine(DATABASE_URI, echo=True)

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
            
            # Normalize the data (use StandardScaler for example)
            df_normalized = normalize_data(df)

            # Solution 1: Use SQLAlchemy connection directly
            with engine.connect() as conn:
                df_normalized.to_sql('csv_data', conn, if_exists='append', index=False)
            
            # Solution 2 (alternative): Use pandas.to_sql with minimal parameters
            # df_normalized.to_sql('csv_data', engine, if_exists='append', index=False)
            
            # Solution 3 (alternative): Use raw SQL to insert data
            # conn = engine.raw_connection()
            # cursor = conn.cursor()
            # for _, row in df_normalized.iterrows():
            #     # Create dynamic SQL query based on DataFrame columns
            #     cols = ', '.join(df_normalized.columns)
            #     placeholders = ', '.join(['?' for _ in range(len(df_normalized.columns))])
            #     sql = f"INSERT INTO csv_data ({cols}) VALUES ({placeholders})"
            #     cursor.execute(sql, tuple(row))
            # conn.commit()
            # conn.close()

            return jsonify({"message": "File uploaded and data stored successfully!"}), 200
        except Exception as e:
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file format. Only CSV is allowed."}), 400

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
    return jsonify({
        "sqlalchemy_version": sqlalchemy.__version__,
        "pandas_version": pandas.__version__
    })

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)