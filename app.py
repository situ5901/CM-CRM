from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify ,send_file
import smtplib
import pandas as pd
from pymongo import MongoClient
import os
from datetime import datetime
from markupsafe import Markup   
from flask import jsonify
import openpyxl
from openpyxl.styles import Font
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase    
from email import encoders
from openpyxl import Workbook
from flask import Flask, render_template, request, session
import requests



app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['MONGO_URI'] = os.environ.get('MONGODB_URI', 'mongodb+srv://ceo:m1jZaiWN2ulUH0ux@cluster1.zdfza.mongodb.net/')

CSV_FILE_PATH = r'E:\moon\MyProject\MyProject\MyProject\disbursed_data.csv'

# Update MongoDB connection setup
client = MongoClient("mongodb+srv://ceo:m1jZaiWN2ulUH0ux@cluster1.zdfza.mongodb.net/")
db = client['test']  # Make sure this database name is correct
users_collection = db['users']
mis_collection = db['mis']

# Add error handling and verification
try:
    # Verify connection
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")


    
def format_date(date_str):
    """Attempts to parse a date string and return it in 'dd-mm-yyyy' format, ignoring time if present."""
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime('%d-%m-%Y')
        except ValueError:
            continue
    return None  # Return None if the date string does not match any known format

@app.route('/settings')
def settings():
    if 'username' in session and session['access_level'] == 'full':
        return render_template('settings.html', username=session['username'])
    else:
        return "Unauthorized Access", 403

@app.route('/change_password', methods=['POST'])
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash("New password and confirm password do not match.")
        return redirect(url_for('settings'))

    user = users_collection.find_one({"username": "Admin"})
    if user and user['password'] == current_password:
        users_collection.update_one({"username": "Admin"}, {"$set": {"password": new_password, "updatedAt": datetime.now()}})
        flash("Password updated successfully.")
    else:
        flash("Current password is incorrect.")

    return redirect(url_for('settings'))

@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    rights = request.form.getlist('rights')

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

from markupsafe import Markup   

@app.route('/data_upload', methods=['GET', 'POST'])
def data_upload():
    if 'username' in session:
        if request.method == 'POST':
            try:
                files = request.files.getlist('file')
                collection_type = request.form.get('collection_type')
                lender_name = request.form.get('lender')

                if not files or files[0].filename == '':
                    flash('No selected files')
                    return redirect(request.url)

                # Choose collection based on type
                collection = mis_collection if collection_type == 'mis' else users_collection
                
                # Verify collection exists
                if collection.name not in db.list_collection_names():
                    db.create_collection(collection.name)
                    print(f"Created collection: {collection.name}")

                for file in files:
                    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
                        try:
                            # Read the file
                            if file.filename.endswith('.csv'):
                                data = pd.read_csv(file)
                            else:
                                data = pd.read_excel(file)

                            data = data.astype(str)

                            # Apply lender-specific column selection, renaming, and filter condition
                            if lender_name == "Cashe":
                                data = data[['mobile_no', 'loan_transferred_date', 'loan_amount']]
                                data = data.rename(columns={
                                    'mobile_no': 'phone',
                                    'loan_transferred_date': 'disbursaldate',
                                    'loan_amount': 'disbursedamount'
                                })
                                data = data[data['disbursedamount'].astype(float) > 1]
                            elif lender_name == "Ramfin":
                                data = data[['mobile', 'disbursalDate', 'disbursalAmount']]
                                data = data.rename(columns={
                                    'mobile': 'phone',
                                    'disbursalDate': 'disbursaldate',
                                    'disbursalAmount': 'disbursedamount'
                                })
                                data = data[data['disbursedamount'].astype(float) > 1]
                            elif lender_name == "Fibe":
                                data = data[['mobile_number', 'first_disb_loan_date', 'first_disb_loan_amt']]
                                data = data.rename(columns={
                                    'mobile_number': 'phone',
                                    'first_disb_loan_date': 'disbursaldate',
                                    'first_disb_loan_amt': 'disbursedamount'
                                })
                                data = data[data['disbursedamount'].astype(float) > 1]
                            elif lender_name == "SmartCoin":
                                data = data[['phone_number', 'loan_disbursed_date', 'loan_amount']]
                                data = data.rename(columns={
                                    'phone_number': 'phone',
                                    'loan_disbursed_date': 'disbursaldate',
                                    'loan_amount': 'disbursedamount'
                                })
                                data = data[data['disbursedamount'].astype(float) > 1]
                            elif lender_name == "MV":
                                data = data[['phone_number', 'disbursal_date', 'disbursed_amt']]
                                data = data.rename(columns={
                                    'phone_number': 'phone',
                                    'disbursal_date': 'disbursaldate',
                                    'disbursed_amt': 'disbursedamount'
                                })
                                data = data[data['disbursedamount'].astype(float) > 1]
                            elif lender_name == "Mpokket":
                                data = data[['mobile_number', 'loan_disbursed_timestamp_ist', 'Loan_amount', 'profession']]
                                data = data.rename(columns={
                                    'mobile_number': 'phone',
                                    'loan_disbursed_timestamp_ist': 'disbursaldate',
                                    'Loan_amount': 'disbursedamount',
                                    'profession': 'emp'
                                })

                            elif lender_name == "MoneyView":
                                data = data[(data['current_status'] == "11. Disbursed")][
                                    ['phone_number', 'disbursed_amt', 'disbursal_date', 'current_status', 'employment_type']
                                ]
                                data = data.rename(columns={
                                    'phone_number': 'phone',
                                    'disbursed_amt': 'disbursedamount', 
                                    'disbursal_date': 'disbursaldate', 
                                    'current_status': 'status', 
                                    'employment_type': 'emp' 
                                })

                                data = data[data['disbursedamount'].astype(float) > 1]
                            elif lender_name == "MVCancel":
                                data = data[['phone_number', 'disbursal_date', 'disbursed_amt']]
                                data = data.rename(columns={
                                    'phone_number': 'phone',
                                    'disbursal_date': 'disbursaldate',
                                    'disbursed_amt': 'disbursedamount'
                                })
                                data = data[data['disbursedamount'].astype(float) > 1]

                            # Add common columns
                            data['Lender'] = lender_name
                            data['createdAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Convert data to dictionary format for MongoDB insertion
                            data_dict = data.to_dict(orient='records')

                            # Add debug logging
                            print(f"Processing {len(data_dict)} records for {lender_name}")
                            
                            for record in data_dict:
                                try:
                                    if 'disbursaldate' in record and record['disbursaldate']:
                                        formatted_date = format_date(record['disbursaldate'])
                                        if formatted_date:
                                            record['disbursaldate'] = formatted_date

                                    record['updatedAt'] = datetime.now()
                                    
                                    # Debug print
                                    print(f"Saving record: {record['phone']}")

                                    existing_doc = collection.find_one({'phone': record['phone']})
                                    
                                    if existing_doc:
                                        result = collection.update_one(
                                            {'phone': record['phone']},
                                            {'$set': record}
                                        )
                                        print(f"Updated record: {result.modified_count}")
                                    else:
                                        result = collection.insert_one(record)
                                        print(f"Inserted record: {result.inserted_id}")

                                except Exception as record_error:
                                    print(f"Error processing record: {str(record_error)}")
                                    continue

                            flash(f'Data for {lender_name} uploaded successfully to {collection_type} collection.')
                        except Exception as e:
                            flash(f'Error processing file {file.filename}: {str(e)}')
                            print(f'Error processing file {file.filename}: {str(e)}')
                    else:
                        flash(f'Only CSV or Excel files are allowed. Skipping file {file.filename}.')

                return redirect(url_for('data_upload'))
            except Exception as route_error:
                print(f"Route error: {str(route_error)}")
                flash(f'An error occurred: {str(route_error)}')
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
    session['username'] = username

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

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' in session and session['access_level'] == 'full':
        # Fetch data from the database
        data = list(mis_collection.find({}, {
            '_id': 0, 
            'phone': 1, 
            'disbursedamount': 1, 
            'disbursaldate': 1, 
            'status': 1, 
            'Lender': 1, 
            'createdAt': 1,
            'partner': 1  # Make sure this field is included
        }))

        # Format the data and add default partner value if missing
        for record in data:
            # Format dates as before
            if 'disbursaldate' in record and record['disbursaldate']:
                try:
                    date_obj = datetime.strptime(record['disbursaldate'], '%Y-%m-%d')
                    record['disbursaldate'] = date_obj.strftime('%d-%m-%y')
                except ValueError:
                    pass
            if 'createdAt' in record and record['createdAt']:
                try:
                    date_obj = datetime.strptime(record['createdAt'], '%Y-%m-%d %H:%M:%S')
                    record['createdAt'] = date_obj.strftime('%d-%m-%y')
                except ValueError:
                    pass
            
            # Set a default value for partner if it's missing or None
            if 'partner' not in record or record['partner'] is None:
                record['partner'] = ''  # Empty string instead of 'Unknown'

        # Filter out records with missing or blank 'disbursedamount'
        data = [record for record in data if record.get('disbursedamount') not in [None, "", " "]]

        # Calculate totals
        total_disbursed = sum(float(record['disbursedamount']) for record in data)
        total_count = len(data)

        # Extract unique filter options
        month_options = sorted(set(record['disbursaldate'][3:5] for record in data if 'disbursaldate' in record))
        lender_options = sorted(set(record['Lender'] for record in data if 'Lender' in record))
        created_at_options = sorted(set(record['createdAt'] for record in data if 'createdAt' in record))

        # If POST request, send email
        if request.method == 'POST':
            try:
                send_email_with_excel(data)
                return "Email sent successfully!"
            except Exception as e:
                return f"Error sending email: {str(e)}"

        return render_template(
            'dashboard.html',
            username=session['username'],
            table_data=data,
            total_disbursed=total_disbursed,
            total_count=total_count,
            month_options=month_options,
            lender_options=lender_options,
            created_at_options=created_at_options,
        )
    else:
        return "Unauthorized Access", 403


def send_email_with_excel(data):
    # Generate Excel file
    excel_file_path = "dashboard_data.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Dashboard Data"

    # Add headers
    headers = ['Phone', 'Disbursed Amount', 'Disbursal Date', 'Status', 'Lender', 'Created At']
    sheet.append(headers)

    # Add data
    for record in data:
        sheet.append([
            record.get('phone', ''),
            record.get('disbursedamount', ''),
            record.get('disbursaldate', ''),
            record.get('status', ''),
            record.get('Lender', ''),
            record.get('createdAt', '')
        ])

    # Save the Excel file
    workbook.save(excel_file_path)

    # Email setup
    sender_email = "er.situkumar@gmail.com"
    sender_password = "zzfg eeil yoiw pvdm"  # Replace with the actual password
    recipient_email = "vishugrewal52@gmail.com"
    subject = "CredMantra CRM Data"
    body = "Please find attached the latest dashboard report."

    # Compose email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach Excel file
    with open(excel_file_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(excel_file_path)}'
        )
        msg.attach(part)

    # Send email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()

    # Remove temporary Excel file
    os.remove(excel_file_path)


# @app.route('/dashboard')
# def dashboard():    
#     if 'username' in session and session['access_level'] == 'full':
#         # Query to fetch all data from the 'mis' collection
#         data = list(mis_collection.find({}, {'_id': 0, 'phone': 1, 'disbursedamount': 1, 'disbursaldate': 1, 'status': 1, 'Lender': 1, 'createdAt': 1}))

#         # Format disbursaldate and createdAt to DD-MM-YY
#         for record in data:
#             if 'disbursaldate' in record and record['disbursaldate']:
#                 try:
#                     date_obj = datetime.strptime(record['disbursaldate'], '%Y-%m-%d')
#                     record['disbursaldate'] = date_obj.strftime('%d-%m-%y')
#                 except ValueError:
#                     pass  # Skip formatting if date is not in expected format
#             if 'createdAt' in record and record['createdAt']:
#                 try:
#                     date_obj = datetime.strptime(record['createdAt'], '%Y-%m-%d %H:%M:%S')
#                     record['createdAt'] = date_obj.strftime('%d-%m-%y')
#                 except ValueError:
#                     pass  # Skip formatting if date is not in expected format

#             # # Fetch partner information from all_fields_collection based on phone number
#             # partner_info = all_fields_collection.find_one({'phone': record['phone']}, {'_id': 0, 'partner': 1})
#             # record['partner'] = partner_info['partner'] if partner_info else 'N/A'

#         # Filter out records with missing or blank 'disbursedamount'
#         data = [record for record in data if record.get('disbursedamount') not in [None, "", " "]]

#         # Calculate total disbursed amount and total count of records
#         total_disbursed = sum(float(record['disbursedamount']) for record in data)
#         total_count = len(data)

#         # Extract unique months, lenders, and createdAt dates for filter dropdowns
#         month_options = sorted(set(record['disbursaldate'][3:5] for record in data if 'disbursaldate' in record))  # Extract MM
#         lender_options = sorted(set(record['Lender'] for record in data if 'Lender' in record))
#         created_at_options = sorted(set(record['createdAt'] for record in data if 'createdAt' in record))
#         partner_options = sorted(set(record['partner'] for record in data if 'partner' in record))

#         return render_template(
#             'dashboard.html',
#             username=session['username'],
#             table_data=data,
#             total_disbursed=total_disbursed,
#             total_count=total_count,
#             month_options=month_options,
#             lender_options=lender_options,
#             created_at_options=created_at_options,
#             partner_options=partner_options  # Pass partner options to template
#         )
#     else:
#         return "Unauthorized Access", 403



@app.route('/dashboard_copy')
def dashboard_copy():
    if 'username' in session and session['access_level'] == 'full':
        # Query to fetch all data from the 'mis' collection
        data = list(mis_collection.find({}, {'_id': 0, 'phone': 1, 'disbursedamount': 1, 'disbursaldate': 1, 'status': 1, 'Lender': 1, 'createdAt': 1}))

        # Format disbursaldate and createdAt to DD-MM-YY
        for record in data:
            if 'disbursaldate' in record and record['disbursaldate']:
                try:
                    date_obj = datetime.strptime(record['disbursaldate'], '%Y-%m-%d')
                    record['disbursaldate'] = date_obj.strftime('%d-%m-%y')
                except ValueError:
                    pass  # Skip formatting if date is not in expected format
            if 'createdAt' in record and record['createdAt']:
                try:
                    date_obj = datetime.strptime(record['createdAt'], '%Y-%m-%d %H:%M:%S')
                    record['createdAt'] = date_obj.strftime('%d-%m-%y')
                except ValueError:
                    pass  # Skip formatting if date is not in expected format

            # # Fetch partner information from all_fields_collection based on phone number
            # partner_info = all_fields_collection.find_one({'phone': record['phone']}, {'_id': 0, 'partner': 1})
            # record['partner'] = partner_info['partner'] if partner_info else 'N/A'

        # Filter out records with missing or blank 'disbursedamount'
        data = [record for record in data if record.get('disbursedamount') not in [None, "", " "]]

        # Calculate total disbursed amount and total count of records
        total_disbursed = sum(float(record['disbursedamount']) for record in data)
        total_count = len(data)

        # Extract unique months, lenders, and createdAt dates for filter dropdowns
        month_options = sorted(set(record['disbursaldate'][3:5] for record in data if 'disbursaldate' in record))  # Extract MM
        lender_options = sorted(set(record['Lender'] for record in data if 'Lender' in record))
        created_at_options = sorted(set(record['createdAt'] for record in data if 'createdAt' in record))
        partner_options = sorted(set(record['partner'] for record in data if 'partner' in record))

        return render_template(
            'dashboard_copy.html',
            username=session['username'],
            table_data=data,
            total_disbursed=total_disbursed,
            total_count=total_count,
            month_options=month_options,
            lender_options=lender_options,
            created_at_options=created_at_options,
            partner_options=partner_options  # Pass partner options to template
        )
    else:
        return "Unauthorized Access", 403




@app.route('/filtered_data', methods=['POST'])
def filtered_data():
    filters = request.get_json()
    selected_created_at_range = filters.get('createdAtRange', [])

    # MongoDB query for filtering based on createdAt date range
    query = {}

    if selected_created_at_range:
        start_date, end_date = selected_created_at_range
        query['createdAt'] = {
            '$gte': datetime.strptime(start_date, '%Y-%m-%d'),
            '$lte': datetime.strptime(end_date, '%Y-%m-%d')
        }

    # Fetch filtered data from MongoDB based on createdAt range
    data = list(mis_collection.find(query, {'_id': 0, 'phone': 1, 'disbursedamount': 1, 'disbursaldate': 1, 'status': 1, 'Lender': 1, 'createdAt': 1}))

    # Calculate totals based on the filtered data
    total_disbursed = sum(float(record.get('disbursedamount', 0)) for record in data)
    total_count = len(data)


    return jsonify({
        'data': data,   
        'totalDisbursed': total_disbursed,
        'totalCount': total_count
    })



from flask import send_file
import pandas as pd
import io

@app.route('/download_filtered_data', methods=['POST'])
def download_filtered_data():
    # Extract filtered data from the request
    filtered_data = request.get_json().get('data', [])

    # Convert the data to a DataFrame
    df = pd.DataFrame(filtered_data)

    # Create an Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Data')
        writer.save()
    output.seek(0)

    # Send the file as a downloadable attachment    
    return send_file(
        output,
        as_attachment=True,
        download_name="filtered_data.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Route for the "All Fields" button
from flask import Flask, render_template, request, session
from pymongo import MongoClient


@app.route('/all_fields', methods=['GET', 'POST'])
def all_fields():   
    if 'username' in session and session['access_level'] == 'full':
        if request.method == 'POST':
            # Search by phone number
            phone = request.form.get('phone')
            query = {'phone': phone} if phone else {}
        else:
            # Fetch all data if no search
            query = {}

        # Fetch data from MongoDB based on query
        data = list(all_fields_collection.find(query, {'_id': 0}))
        total_count = len(data)
        total_disbursed = sum(float(record.get('disbursedamount', 0)) for record in data)

        return render_template(
            'all_fields.html',
            username=session['username'],
            table_data=data,
            total_disbursed=total_disbursed,
            total_count=total_count
        )
    else:
        return "Unauthorized Access", 403

    


@app.route('/attendance')
def attendance():
    if 'username' in session:
        return render_template('attendance.html', username=session['username'], access_level=session['access_level'])
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('access_level', None)
    return redirect(url_for('login'))

@app.route('/get_content/<page>')
def get_content(page):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if page == 'home':
        return render_template('home_content.html')
    elif page == 'dashboard':
        return render_template('dashboard.html')
    elif page == 'attendance':
        return render_template('content/attendance_content.html')
    elif page == 'settings':
        return render_template('content/settings_content.html')
    elif page == 'upload':
        return render_template('content/upload_content.html')
    else:
        return "Page not found", 404

@app.route('/get_partners', methods=['POST'])
def get_partners():
    try:
        data = request.get_json()
        phones = data.get('phones', [])

        if not phones:
            return jsonify({"error": "No phone numbers provided"}), 400

        api_url = "https://credmantra.com/api/v1/crm/getPartners"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(
            api_url, 
            json={"phones": phones},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            partner_list = response.json()
            partner_data = {}
            
            # Convert list to dictionary format
            if isinstance(partner_list, list):
                for item in partner_list:
                    if isinstance(item, dict) and 'phone' in item and 'partner' in item:
                        partner_data[item['phone']] = {
                            'partner': item['partner']
                        }
                        # Update MongoDB
                        mis_collection.update_one(
                            {"phone": item['phone']},
                            {"$set": {
                                "partner": item['partner'],
                                "updatedAt": datetime.now()
                            }}
                        )
            
            return jsonify({
                "success": True,
                "data": partner_data
            })
        else:
            return jsonify({"error": f"API request failed: {response.text}"}), response.status_code

    except Exception as e:
        print(f"Error in get_partners: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/update-partners', methods=['POST'])
def update_partners():
    try:
        # Get partner data from request
        data = request.get_json()
        partner_data = data.get('partnerData', {})

        if not partner_data:
            return jsonify({"error": "No partner data provided"}), 400

        # Update records in MongoDB
        updates = {}
        for phone, info in partner_data.items():
            # Find existing document
            existing = mis_collection.find_one({"phone": phone})
            
            if existing:
                old_partner = existing.get('partner', None)
                new_partner = info.get('partner')
                
                # Only update if partner is different
                if old_partner != new_partner:
                    mis_collection.update_one(
                        {"phone": phone},
                        {"$set": {
                            "partner": new_partner,
                            "updatedAt": datetime.now()
                        }}
                    )
                    updates[phone] = {
                        "old_partner": old_partner,
                        "new_partner": new_partner
                    }

        return jsonify({
            "message": "Partner information updated successfully",
            "updatedCount": len(updates),
            "updates": updates
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analytical')
def analytical():
    # Initialize default values
    total_disbursed = 0
    total_count = 0
    avg_ticket = 0
    top_lender = "N/A"
    top_partner = "N/A"
    
    # Get username from session
    username = session.get('username', 'Guest')
    
    # Sample data for charts (replace with your actual data)
    monthly_data = [
        {"_id": {"month": 1, "year": 2024}, "amount": 0, "count": 0},
        {"_id": {"month": 2, "year": 2024}, "amount": 0, "count": 0}
    ]
    
    amount_distribution = [
        {"range": "0-5K", "count": 0},
        {"range": "5K-25K", "count": 0},
        {"range": "25K-50K", "count": 0},
        {"range": "50K-100K", "count": 0},
        {"range": "100K+", "count": 0}
    ]
    
    # Sample filter options (replace with your actual data)
    lenders = ["Lender 1", "Lender 2"]
    partners = ["Partner 1", "Partner 2"]
    statuses = ["Approved", "Pending", "Rejected"]
    amount_ranges = ["0-5,000", "5,000-25,000", "25,000-50,000", "50,000-100,000", "100,000+"]

    return render_template('analytical.html',
        username=username,
        total_disbursed=total_disbursed,
        total_count=total_count,
        avg_ticket=avg_ticket,
        top_lender=top_lender,
        top_partner=top_partner,
        lenders=lenders,
        partners=partners,
        statuses=statuses,
        amount_ranges=amount_ranges,
        monthly_data=monthly_data,
        amount_distribution=amount_distribution
    )

# Add this new route to handle saving partner data to DB
@app.route('/save_partners_to_db', methods=['POST'])
def save_partners_to_db():
    try:
        # Get phones from all records in mis_collection
        all_records = mis_collection.find({}, {'phone': 1, '_id': 0})
        phones = [record['phone'] for record in all_records]

        if not phones:
            return jsonify({"error": "No phone numbers found"}), 400

        # Call getPartners API
        api_url = "https://credmantra.com/api/v1/crm/getPartners"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(
            api_url, 
            json={"phones": phones},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            partner_list = response.json()
            
            # Create or get the getpartner collection
            getpartner_collection = db['getpartner']
            
            # Clear existing data in getpartner collection
            getpartner_collection.delete_many({})
            
            # Prepare documents for insertion
            documents = []
            for item in partner_list:
                if isinstance(item, dict) and 'phone' in item and 'partner' in item:
                    document = {
                        'phone': item['phone'],
                        'partner': item['partner'],
                        'createdAt': datetime.now(),
                        'updatedAt': datetime.now()
                    }
                    documents.append(document)
            
            # Insert documents in bulk if there are any
            if documents:
                getpartner_collection.insert_many(documents)
                
                return jsonify({
                    "success": True,
                    "message": f"Successfully saved {len(documents)} partner records to database",
                    "count": len(documents)
                })
            else:
                return jsonify({
                    "error": "No valid partner data found to save"
                }), 400
                
        else:
            return jsonify({
                "error": f"API request failed: {response.text}"
            }), response.status_code

    except Exception as e:
        print(f"Error in save_partners_to_db: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
