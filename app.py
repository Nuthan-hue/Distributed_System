from flask import Flask, request, jsonify, render_template
import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Set up the SQLite database engine
DATABASE_URI = 'sqlite:///API.db'
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

            # Store data into the database
            df_normalized.to_sql('csv_data', con=engine, if_exists='append', index=False)

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
    
    scaler = StandardScaler()
    # Normalize only numeric columns
    df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
    
    return df


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
