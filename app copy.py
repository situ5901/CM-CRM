# from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify ,send_file
# import pandas as pd
# from pymongo import MongoClient
# import os
# from datetime import datetime
# from markupsafe import Markup   
# from flask import jsonify
# import openpyxl
# from openpyxl.styles import Font
# import io
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
import matplotlib.pyplot as plt
import io
import base64




app = Flask(__name__)
app.secret_key = 'your_secret_key'

CSV_FILE_PATH = r'E:\moon\MyProject\MyProject\MyProject\disbursed_data.csv'

# Existing MongoDB connection string
client = MongoClient("mongodb+srv://ceo:RuxSmFVLnV7Za7Om@cluster1.zdfza.mongodb.net/")
db = client['test']
users_collection = db['users']
mis_collection = db['mis']

# New MongoDB connection string for "All Fields" button
all_fields_client = MongoClient("mongodb+srv://ceo:RuxSmFVLnV7Za7Om@cluster0.2vjepfe.mongodb.net/")
all_fields_db = all_fields_client['test']
all_fields_collection = all_fields_db['users']
    
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
            files = request.files.getlist('file')
            collection_type = request.form.get('collection_type')
            lender_name = request.form.get('lender')

            if not files or files[0].filename == '':
                flash('No selected files')
                return redirect(request.url)

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
                            data = data[data['disbursedamount'].astype(float) > 1]

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

                        # After the lender-specific data processing and before MongoDB insertion,
                        # Add this code to format the disbursaldate:
                        
                        def format_date(date_str):
                            """Convert any date string to DD-MM-YYYY format"""
                            date_formats = [
                                '%Y-%m-%d %H:%M:%S',
                                '%Y-%m-%d',
                                '%d-%m-%Y',
                                '%d/%m/%Y',
                                '%Y/%m/%d',
                                '%m/%d/%Y'
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    return datetime.strptime(str(date_str).strip(), fmt).strftime('%d-%m-%Y')
                                except ValueError:
                                    continue
                            return date_str  # Return original if no format matches

                        # Format the disbursaldate column
                        data['disbursaldate'] = data['disbursaldate'].apply(format_date)

                        # Add common columns
                        data['Lender'] = lender_name
                        data['createdAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Convert data to dictionary format for MongoDB insertion
                        data_dict = data.to_dict(orient='records')

                        # Insert data into MongoDB based on collection type
                        if collection_type == 'users':
                            users_collection.insert_many(data_dict)

                            for record in data_dict:
                            # Convert 'disbursaldate' to 'dd-mm-yyyy' format if it exists
                             if 'disbursaldate' in record and record['disbursaldate']:
                                try:
                                    date_obj = datetime.strptime(record['disbursaldate'], '%Y-%m-%d')
                                    record['disbursaldate'] = date_obj.strftime('%d-%m-%Y')
                                except ValueError:
                                    flash(f"Invalid date format in disbursaldate for {record['phone']}")
                                    continue  # Skip this record if date format is invalid

                            # Check if the document already exists
                            existing_doc = users_collection.find_one({'phone': record['phone']})
                            if existing_doc:
                                # Detect changes
                                fields_to_update = {k: v for k, v in record.items() if existing_doc.get(k) != v}

                                if fields_to_update:
                                    # Only update 'updatedAt' if there's a change
                                    fields_to_update['updatedAt'] = datetime.now()
                                    users_collection.update_one(
                                        {'phone': record['phone']},
                                        {'$set': fields_to_update}
                                    )
                            else:
                                # Insert new document with 'updatedAt'
                                record['updatedAt'] = datetime.now()
                                users_collection.insert_one(record)

                            flash(f'User data for {lender_name} uploaded successfully for file {file.filename}.')
                        elif collection_type == 'mis':
                            mis_collection.insert_many(data_dict)
                            flash(f'MIS data for {lender_name} uploaded successfully for file {file.filename}.')
                        else:
                            flash(f'Invalid collection type selected for file {file.filename}.')
                    except Exception as e:
                        flash(f'Error processing file {file.filename}: {e}')
                        print(f'Error processing file {file.filename}: {e}')
                else:
                    flash(f'Only CSV or Excel files are allowed. Skipping file {file.filename}.')

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
        data = list(mis_collection.find({}, {'_id': 0, 'phone': 1, 'disbursedamount': 1, 'disbursaldate': 1, 'status': 1, 'Lender': 1, 'createdAt': 1}))

        # Format disbursaldate and createdAt
        for record in data:
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

        # Filter out records with missing or blank 'disbursedamount'
        data = [record for record in data if record.get('disbursedamount') not in [None, "", " "]]

        # Calculate total disbursed amount and total count of records
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
    sender_email = "info@credmantra.com"
    sender_password = "ptho pmsy xlla ojxp"  # Replace with the actual password
    recipient_email = "ceo@credmantra.com"
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
    filtered_data = request.get_json().get('data', [])
    
    # Convert the data to a DataFrame and format dates
    df = pd.DataFrame(filtered_data)
    
    # Create an Excel file in memory
    output = io.BytesIO()
    
    # Create Excel writer with xlsxwriter engine
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Data')
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Filtered Data']
        
        # Add some formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        
        # Write the column headers with the header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Auto-adjust columns' width
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            worksheet.set_column(col_idx, col_idx, column_width)
            
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
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

@app.route('/api/ai-query', methods=['POST'])
def handle_ai_query():
    data = request.json
    query = data.get('query').lower()
    
    try:
        # If query is about lender-wise data
        if any(keyword in query for keyword in ['lender', 'lenders', 'show lenders', 'lender wise']):
            # Convert your data to DataFrame (adjust according to your data structure)
            df = pd.DataFrame(list(your_data_collection.find({})))  # Replace with your actual data source
            
            # Get lender-wise counts
            lender_counts = df['Lender'].value_counts()
            
            # Create visualization
            plt.figure(figsize=(10, 6))
            lender_counts.plot(kind='bar')
            plt.title('Lender-wise Distribution')
            plt.xlabel('Lender')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convert plot to base64 string
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png')
            img_buf.seek(0)
            img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
            plt.close()
            
            # Create table data
            table_data = lender_counts.to_dict()
            
            response = {
                'response': 'Here is the lender-wise distribution of data:',
                'visualization': {
                    'type': 'image',
                    'data': img_base64,
                    'table': table_data
                }
            }
            
            return jsonify(response)
        
        # Handle other types of queries
        else:
            return jsonify({
                'response': 'I understand you want to know about: ' + query,
                'visualization': None
            })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
