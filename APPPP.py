from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
from pymongo import MongoClient
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key for security

# Define the path to your CSV file
CSV_FILE_PATH = r'C:\Users\moon\MyProject\MyProject\MyProject\CRM\SuccessCRM\filtered_data.csv'

# MongoDB connection
client = MongoClient("mongodb+srv://ceo:RuxSmFVLnV7Za7Om@cluster1.zdfza.mongodb.net/")  # Replace with your MongoDB URI
db = client['test']  # Replace with your database name
users_collection = db['users']  # Replace with your users collection name
mis_collection = db['mis']  # Replace with your MIS collection name

# Route to render Settings page
@app.route('/settings')
def settings():
    return render_template('settings.html')

# Route to Change Password
@app.route('/change_password', methods=['POST'])
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash("New password and confirm password do not match.")
        return redirect(url_for('settings'))
    
    # Verify current password (example: assume current user is "Admin")
    user = users_collection.find_one({"username": "Admin"})
    if user and user['password'] == current_password:
        # Update password in MongoDB
        users_collection.update_one({"username": "Admin"}, {"$set": {"password": new_password, "updatedAt": datetime.now()}})
        flash("Password updated successfully.")
    else:
        flash("Current password is incorrect.")
    
    return redirect(url_for('settings'))

# Route to Create New User
@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    rights = request.form.getlist('rights')  # Get rights as list of strings
    
    # Insert new user into MongoDB
    new_user = {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
        "rights": rights,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    }
    
    users_collection.insert_one(new_user)
    flash(f"User {username} created successfully with role {role}.")
    
    return redirect(url_for('settings'))

if __name__ == '__main__':
    app.run(debug=True)

# Function to update or insert document with `createdAt` and `updatedAt`
def upsert_with_timestamps(phone, update_data):
    # Current timestamp for the operation
    current_timestamp = datetime.now()



@app.route('/data_upload', methods=['GET', 'POST'])
def data_upload():
    if 'username' in session:
        if request.method == 'POST':
            # Check for file upload
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            
            file = request.files['file']
            collection_type = request.form.get('collection_type')  # Get collection type (users or MIS)
            lender_name = request.form.get('lender')  # Get selected lender name
                

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            # Validate file type
            if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
                try:
                    # Read the file with Pandas
                    if file.filename.endswith('.csv'):
                        data = pd.read_csv(file)
                    else:
                        data = pd.read_excel(file)
                    
                    # Convert all data to string format
                    data = data.astype(str)
                    
                    # Add lender name to each record in the data
                    data['Lender'] = lender_name
                    
                    # Convert DataFrame to dictionary format for MongoDB
                    data_dict = data.to_dict(orient='records')
                    
                    # Insert data into the appropriate MongoDB collection
                    if collection_type == 'users':
                        users_collection.insert_many(data_dict)
                        flash(f'User data for {lender_name} uploaded successfully to MongoDB.')
                    elif collection_type == 'mis':
                        mis_collection.insert_many(data_dict)
                        flash(f'MIS data for {lender_name} uploaded successfully to MongoDB.')
                    else:
                        flash('Invalid collection type selected.')
                except Exception as e:
                    flash(f'Error processing file: {e}')
                    print(f'Error processing file: {e}')
            else:
                flash('Only CSV or Excel files are allowed.')
            return redirect(url_for('data_upload'))
        
        return render_template('data_upload.html', username=session['username'])
    else:
        return redirect(url_for('login'))



@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    session['username'] = username  # Store username in session

    if password == '123123':
        session['access_level'] = 'limited'
        return redirect(url_for('home'))
    elif password == '123456':
        session['access_level'] = 'full'
        return redirect(url_for('home'))
    else:
        return "Invalid Credentials", 401

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'], access_level=session['access_level'])
    else:
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session and session['access_level'] == 'full':
        try:
            # Read the CSV file
            df = pd.read_csv(CSV_FILE_PATH)
            # Convert DataFrame to HTML table
            data_html = df.to_html(classes='data', index=False)  # Note: classes='data' is required for DataTables
        except FileNotFoundError:
            data_html = "<p>Error: CSV file not found.</p>"
        except Exception as e:
            data_html = f"<p>Error: {e}</p>"
        
        return render_template('dashboard.html', username=session['username'], data=data_html)
    else:
        return "Unauthorized Access", 403

@app.route('/attendance')
def attendance():
    if 'username' in session:
        return render_template('attendance.html', username=session['username'], access_level=session['access_level'])
    else:
        return redirect(url_for('login'))

@app.route('/settings')
def settings():
    if 'username' in session and session['access_level'] == 'full':
        return render_template('settings.html', username=session['username'])
    else:
        return "Unauthorized Access", 403

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('access_level', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)