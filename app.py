from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime,time
import os
from dotenv import load_dotenv
import openpyxl
from io import BytesIO,StringIO
from reportlab.lib.pagesizes import landscape, A3
import csv
from reportlab.pdfgen import canvas
import pandas as pd
import traceback
import re
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from dotenv import load_dotenv
import os, smtplib, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from pytz import timezone
india = timezone('Asia/Kolkata')


load_dotenv()

 
def parse_integrity_error(err):
    msg = str(err.orig).lower()
    if 'employee_id' in msg or 'user_table_pkey' in msg:
        return "Employee ID already exists."
    if 'username' in msg:
        return "Username already exists."
    if 'email' in msg:
        return "Email already exists."
    if 'phone' in msg:
        return "Mobile number already exists."
    if 'id_no' in msg:
        return "Part ID already exists."
    if 'not-null' in msg or 'null value' in msg:
        return "Required field missing."
    return "Duplicate or invalid entry."

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', os.getenv('DATABASE_URL', 'postgresql://postgres:your_password@localhost/Table_name'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'user_table'
    employee_id = db.Column(db.String(50), primary_key=True)
    user_type = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=True) 
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.String(50))
    modified_date = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)

    def get_id(self):
        return self.employee_id

class FQCPart(db.Model):
    __tablename__ = 'fqc_part_table'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('user_table.employee_id'))
    user_type = db.Column(db.String(50))
    username = db.Column(db.String(50))
    unit = db.Column(db.String(50))
    location = db.Column(db.String(50))
    timestamp = db.Column(db.String(50))
    shift = db.Column(db.String(10))
    crown_scan = db.Column(db.String(100))
    pinion_scan = db.Column(db.String(100))
    crown_id_no = db.Column(db.String(50))
    pinion_id_no = db.Column(db.String(50))
    crown_set_no = db.Column(db.String(50))
    pinion_set_no = db.Column(db.String(50))
    ed_no = db.Column(db.String(50))
    repeat_no = db.Column(db.String(50))
    set_match = db.Column(db.String(10))
    part_match = db.Column(db.String(10))
    overall_status = db.Column(db.String(10))

class AddPart(db.Model):
    __tablename__ = 'add_part_table'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('user_table.employee_id'))
    user_type = db.Column(db.String(50))
    username = db.Column(db.String(50))
    id_no = db.Column(db.String(50), unique=True)
    ed = db.Column(db.String(50))
    status = db.Column(db.String(20))
    created_date = db.Column(db.String(50))
    modified_date = db.Column(db.String(50))

class LoginLog(db.Model):
    __tablename__ = 'login_table'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('user_table.employee_id'))
    user_type = db.Column(db.String(50))
    username = db.Column(db.String(50))
    last_login = db.Column(db.String(50))
    
    
class QR2Part(db.Model):
    __tablename__ = 'qr2_parts'
    id = db.Column(db.Integer, primary_key=True)
    crown_id = db.Column(db.String(50))
    crown_ed_no = db.Column(db.String(50))
    pinion_id = db.Column(db.String(50))
    pinion_ed_no = db.Column(db.String(50))
    ed_no = db.Column(db.Text)
    employee_id = db.Column(db.String(50))
    user_type = db.Column(db.String(50))
    username = db.Column(db.String(100))
    unit = db.Column(db.String(100))
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class QR2ScanLog(db.Model):
    __tablename__ = 'qr2_scan_logs'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50))
    username = db.Column(db.String(100))
    user_type = db.Column(db.String(50))
    unit = db.Column(db.String(50))
    location = db.Column(db.String(50), default="CWP-FQC")  # ✅ Default value
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # ✅ String timestamp
    shift = db.Column(db.String(10))
    crown_scan = db.Column(db.Text)
    pinion_scan = db.Column(db.Text)
    crown_id = db.Column(db.String(50))
    pinion_id = db.Column(db.String(50))
    crown_set = db.Column(db.String(50))
    pinion_set = db.Column(db.String(50))
    ed_no = db.Column(db.Text)
    set_match = db.Column(db.String(10))
    ed_match = db.Column(db.String(10))
    overall_status = db.Column(db.String(10))
    repeat_no = db.Column(db.Integer)
    




@login_manager.user_loader
def load_user(employee_id):
    return User.query.get(employee_id)

login_manager.login_view = 'index'  # your homepage route name


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        password = request.form.get('password')
        
        user = User.query.filter_by(employee_id=employee_id, user_type=user_type).first()
        
        if user and user.password == password and user.is_active:
            login_user(user)
            
            # Log login
            login_log = LoginLog(
                employee_id=user.employee_id,
                user_type=user.user_type,
                username=user.username,
                last_login=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(login_log)
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        flash('Invalid credentials or inactive account')
    return render_template('login.html', user_type=user_type)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/scan_parts')
@login_required
def scan_parts():
    return render_template('scan_parts.html')

def get_current_shift():
    now = datetime.now().time()
    if time(7, 30) <= now < time(16, 0):
        return 'A'
    elif time(16, 0) <= now < time(23, 59, 59):
        return 'B'
    else:
        return 'C'

@app.route('/scan_qr2')
@login_required
def scan_qr2():
    if current_user.user_type not in ['OPERATOR', 'ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))
    return render_template('scan_qr2.html')



# @app.route('/process_scan', methods=['POST'])
@app.route('/process_scan_qr1', methods=['POST'])
@login_required
def process_scan_qr1():
    import re
    try:
        data = request.get_json()
        crown_scan = data.get('crown_scan', '').strip().upper()
        pinion_scan = data.get('pinion_scan', '').strip().upper()

        def extract_id(scan):
            match = re.search(r'p([a-z]+)(\d+)', scan, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                digits = match.group(2)
                return f"{prefix}{digits}"
            return 'N/A'

        def extract_set(scan):
            match = re.search(r'#t([^#]+)#', scan, re.IGNORECASE)
            return match.group(1).upper() if match else 'N/A'

        crown_id = extract_id(crown_scan)
        pinion_id = extract_id(pinion_scan)
        crown_set = extract_set(crown_scan)
        pinion_set = extract_set(pinion_scan)

        crown_part = AddPart.query.filter_by(id_no=crown_id).first()
        pinion_part = AddPart.query.filter_by(id_no=pinion_id).first()

        if not crown_part or crown_part.status.upper() != 'ACTIVE':
            return jsonify({'status': 'error', 'message': f'Crown part \"{crown_id}\" is not active or not found'}), 400
        if not pinion_part or pinion_part.status.upper() != 'ACTIVE':
            return jsonify({'status': 'error', 'message': f'Pinion part \"{pinion_id}\" is not active or not found'}), 400

        part_match = 'YES' if crown_id != 'N/A' and pinion_id != 'N/A' and crown_id == pinion_id else 'NO'
        set_match = 'YES' if crown_set != 'N/A' and pinion_set != 'N/A' and crown_set == pinion_set else 'NO'
        overall_status = 'OK' if set_match == 'YES' and part_match == 'YES' else 'NOT_OK'
        ed_no = crown_part.ed if part_match == 'YES' and set_match == 'YES' and crown_part else 'N/A'

        repeat_count = FQCPart.query.filter_by(
            crown_scan=crown_scan,
            pinion_scan=pinion_scan
        ).count()
        repeat_no = '' if repeat_count == 0 else str(repeat_count + 1)

        new_scan = FQCPart(
            employee_id=current_user.employee_id,
            user_type=current_user.user_type,
            username=current_user.username,
            unit='UNIT-1',
            location='CWPFQC',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            shift=get_current_shift(),
            crown_scan=crown_scan,
            pinion_scan=pinion_scan,
            crown_id_no=crown_id,
            pinion_id_no=pinion_id,
            crown_set_no=crown_set,
            pinion_set_no=pinion_set,
            ed_no=ed_no,
            repeat_no=repeat_no,
            set_match=set_match,
            part_match=part_match,
            overall_status=overall_status
        )
        db.session.add(new_scan)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'match': overall_status == 'OK',
            'username': current_user.username,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'shift': get_current_shift(),
            'crown_scan': crown_scan,
            'pinion_scan': pinion_scan,
            'details': {
                'crown_id': crown_id,
                'pinion_id': pinion_id,
                'crown_set': crown_set,
                'pinion_set': pinion_set,
                'ed_no': ed_no,
                'repeat_no': repeat_no,
                'set_match': set_match,
                'part_match': part_match,
                'overall_status': overall_status
            }
        })

    except Exception as e:
        print("🚨 SCAN PROCESSING ERROR:", str(e))
        return jsonify({
            'status': 'error',
            'message': 'Something went wrong while processing scan'
        }), 500

# --- QR2 Scan Processing ---
@app.route('/process_scan_qr2', methods=['POST'])
@login_required
def process_scan_qr2():
    data = request.get_json()
    crown_scan = data.get("crown_scan", "").strip().upper()
    pinion_scan = data.get("pinion_scan", "").strip().upper()

    def extract_parts(scan):
        if "#" in scan:
            parts = scan.split("#")
            part_id = parts[0]
            set_no = parts[1] if len(parts) > 1 else ""
        elif "-" in scan:
            split_parts = scan.split("-")
            part_id = split_parts[0]
            set_no = "-".join(split_parts[1:]) if len(split_parts) > 1 else ""
        else:
            part_id = scan
            set_no = ""
        return part_id.strip(), set_no.strip()

    crown_id, crown_set = extract_parts(crown_scan)
    pinion_id, pinion_set = extract_parts(pinion_scan)

    set_match = "YES" if crown_set == pinion_set else "NO"
    part_match = "NO"
    shift = get_current_shift()
    location = "CWP-FQC"
    unit = getattr(current_user, "unit", "1")

    part = QR2Part.query.filter_by(crown_id=crown_id).first()
    if not part:
        return jsonify({"status": "error", "message": f"Crown ID {crown_id} not found."}), 400

    if part.status.lower() != "active":
        return jsonify({"status": "error", "message": f"Crown ID {crown_id} is inactive."}), 400

    if pinion_id == part.pinion_id:
        part_match = "YES"
    else:
        return jsonify({"status": "error", "message": f"Pinion ID mismatch with Crown ID {crown_id}."}), 400

    if part.crown_id == part.pinion_id:
        ed_no = part.crown_ed_no
        ed_match = "YES" if ed_no == part.ed_no or part.ed_no == f"{ed_no}/{ed_no}" else "NO"
    else:
        ed_no = f"{part.crown_ed_no}/{part.pinion_ed_no}"
        ed_match = "YES" if ed_no == part.ed_no else "NO"
    overall_status = "OK" if set_match == "YES" and ed_match == "YES" else "NOT_OK"

    repeat_no = QR2ScanLog.query.filter_by(
        crown_id=crown_id,
        pinion_id=pinion_id,
        crown_set=crown_set,
        pinion_set=pinion_set
    ).count() + 1

    log = QR2ScanLog(
        employee_id=current_user.employee_id,
        username=current_user.username,
        user_type=current_user.user_type,
        unit=unit,
        location=location,
        shift=shift,
        crown_scan=crown_scan,
        pinion_scan=pinion_scan,
        crown_id=crown_id,
        pinion_id=pinion_id,
        crown_set=crown_set,
        pinion_set=pinion_set,
        ed_no=ed_no,
        set_match=set_match,
        ed_match=ed_match,
        overall_status=overall_status,
        repeat_no=repeat_no
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "status": "success",
        "username": current_user.username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "unit": unit,
        "shift": shift,
        "crown_scan": crown_scan,
        "pinion_scan": pinion_scan,
        "details": {
            "crown_id": crown_id,
            "pinion_id": pinion_id,
            "crown_set": crown_set,
            "pinion_set": pinion_set,
            "ed_no": ed_no,
            "set_match": set_match,
            "part_match": part_match,
            "ed_match": ed_match,
            "overall_status": overall_status,
            "repeat_no": str(repeat_no)
        }
    })    
    
@app.route('/manage_operators')
@login_required
def manage_operators():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))
    operators = User.query.filter_by(user_type='OPERATOR').all()
    return render_template('manage_operators.html', operators=operators)

@app.route('/add_operator', methods=['POST'])
@login_required
def add_operator():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    try:
        new_operator = User(
            employee_id=data['employee_id'],
            user_type='OPERATOR',
            username=data['username'],
            password=data['password'],  # Should be hashed in production
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email', '').strip() or None,
            phone_number=data.get('phone_number', '').strip() or None,
            created_by=current_user.employee_id,
            created_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            modified_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            is_active=True,
            is_deleted=False
        )
        db.session.add(new_operator)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Operator added successfully',
            'operator': {
                'employee_id': new_operator.employee_id,
                'username': new_operator.username,
                'full_name': f'{new_operator.first_name} {new_operator.last_name}',
                'email': new_operator.email,
                'phone_number': new_operator.phone_number,
                'is_active': new_operator.is_active
            }
        })
        
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/update_operator/<employee_id>', methods=['PUT'])
@login_required
def update_operator(employee_id):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    operator = User.query.get(employee_id)
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    data = request.get_json()
    try:
        operator.username = data.get('username', operator.username)
        operator.first_name = data.get('first_name', operator.first_name)
        operator.last_name = data.get('last_name', operator.last_name)
        operator.email = data.get('email', operator.email).strip() or None
        operator.phone_number = data.get('phone_number', operator.phone_number).strip() or None
        if 'password' in data:
            operator.password = data['password']  # Should be hashed in production
        operator.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Operator updated successfully',
            'operator': {
                'employee_id': operator.employee_id,
                'username': operator.username,
                'full_name': f'{operator.first_name} {operator.last_name}',
                'email': operator.email,
                'phone_number': operator.phone_number,
                'is_active': operator.is_active
            }
        })
        
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/operator/<employee_id>', methods=['GET'])
@login_required
def get_operator(employee_id):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403

    operator = User.query.get(employee_id)
    if not operator or operator.user_type != 'OPERATOR':
        return jsonify({'error': 'Operator not found'}), 404

    return jsonify({
        'employee_id': operator.employee_id,
        'username': operator.username,
        'first_name': operator.first_name,
        'last_name': operator.last_name,
        'email': operator.email,
        'phone_number': operator.phone_number,
        'is_active': operator.is_active
    })


@app.route('/toggle_operator/<employee_id>', methods=['POST'])
@login_required
def toggle_operator(employee_id):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    operator = User.query.get(employee_id)
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    try:
        operator.is_active = not operator.is_active
        operator.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Operator {"activated" if operator.is_active else "deactivated"} successfully',
            'is_active': operator.is_active
        })
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/manage_parts')
@login_required
def manage_parts():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))
    
    qr1_parts = AddPart.query.all()
    qr2_parts = QR2Part.query.all()
    return render_template('manage_parts.html', qr1_parts=qr1_parts, qr2_parts=qr2_parts,active_tab='qr1')


@app.route('/add_part', methods=['POST'])
@login_required
def add_part():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    try:
        id_no_upper = data['id_no'].upper()  # ✅ Convert to uppercase

        # Check for existing part using uppercase ID
        existing_part = AddPart.query.filter_by(id_no=id_no_upper).first()
        if existing_part:
            return jsonify({'status': 'error', 'error': 'Part ID already exists'}), 400

        new_part = AddPart(
            employee_id=current_user.employee_id,
            user_type=current_user.user_type,
            username=current_user.username,
            id_no=id_no_upper,  # ✅ Store uppercase
            ed=data['ed'],
            status='ACTIVE',
            created_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            modified_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        db.session.add(new_part)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Part added successfully',
            'part': {
                'id': new_part.id,
                'id_no': new_part.id_no,
                'ed': new_part.ed,
                'status': new_part.status
            }
        })
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
        
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/update_part/<int:part_id>', methods=['PUT'])
@login_required
def update_part(part_id):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    part = AddPart.query.get(part_id)
    if not part:
        return jsonify({'error': 'Part not found'}), 404
    
    data = request.get_json()
    try:
        part.id_no = data.get('id_no', part.id_no)
        part.ed = data.get('ed', part.ed)
        part.status = data.get('status', part.status)
        part.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Part updated successfully',
            'part': {
                'id': part.id,
                'id_no': part.id_no,
                'ed': part.ed,
                'status': part.status
            }
        })
        
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
@app.route('/part/<int:part_id>', methods=['GET'])
@login_required
def get_part(part_id):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403

    part = AddPart.query.get(part_id)
    if not part:
        return jsonify({'error': 'Part not found'}), 404

    return jsonify({
        'id': part.id,
        'id_no': part.id_no,
        'ed': part.ed,
        'status': part.status
    })

@app.route('/api/parts/<string:id_no>', methods=['GET'])
@login_required
def get_part_by_id(id_no):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403

    part = AddPart.query.filter_by(id_no=id_no).first()
    if not part:
        return jsonify({'error': 'Part not found'}), 404

    return jsonify({
        'id': part.id,
        'id_no': part.id_no,
        'ed': part.ed,
        'status': part.status
    })

@app.route('/delete_part/<int:part_id>', methods=['DELETE'])
@login_required
def delete_part(part_id):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    part = AddPart.query.get(part_id)
    if not part:
        return jsonify({'error': 'Part not found'}), 404
    
    try:
        db.session.delete(part)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Part deleted successfully'
        })
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/update_part/<string:id_no>', methods=['PUT'])
@login_required
def update_part_by_id_no(id_no):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403

    part = AddPart.query.filter_by(id_no=id_no).first()
    if not part:
        return jsonify({'error': 'Part not found'}), 404

    data = request.get_json()
    try:
        part.ed = data.get('ed', part.ed)
        part.status = data.get('status', part.status)
        part.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Part updated successfully',
            'part': {
                'id': part.id,
                'id_no': part.id_no,
                'ed': part.ed,
                'status': part.status
            }
        })
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/parts/<string:id_no>/toggle', methods=['PATCH'])
@login_required
def toggle_qr1_part_status(id_no):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403

    part = AddPart.query.filter_by(id_no=id_no).first()
    if not part:
        return jsonify({'error': 'Part not found'}), 404

    data = request.get_json()
    new_status = data.get('status', '').upper()

    if new_status not in ['ACTIVE', 'NOT_ACTIVE']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        part.status = new_status
        part.modified_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Status changed to {new_status}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@app.route('/api/parts/<string:id_no>', methods=['DELETE'])
@login_required
def delete_part_by_id_no(id_no):
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403

    part = AddPart.query.filter_by(id_no=id_no).first()
    if not part:
        return jsonify({'error': 'Part not found'}), 404

    try:
        db.session.delete(part)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Part deleted successfully'
        })
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# -- QR2 Manage Parts --
@app.route('/manage_parts_qr2')
@login_required
def manage_parts_qr2():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))
    parts = QR2Part.query.all()
    return render_template('manage_parts_qr2.html', parts=parts)

from datetime import datetime
from flask_login import current_user
from werkzeug.utils import secure_filename
import pandas as pd
import os

@app.route('/add_part_qr2', methods=['POST'])
@login_required
def add_part_qr2():
    data = request.get_json()

    # Convert to uppercase
    crown_id = data['crown_id'].strip().upper()
    crown_ed_no = data['crown_ed_no'].strip().upper()
    pinion_id = data['pinion_id'].strip().upper()
    pinion_ed_no = data['pinion_ed_no'].strip().upper()
    status = data['status'].strip().upper()

    try:
        existing = QR2Part.query.filter_by(crown_id=crown_id).first()
        if existing:
            return jsonify({'status': 'error', 'message': 'Crown ID already exists'}), 400

        ed_no = crown_ed_no if crown_ed_no == pinion_ed_no else f"{crown_ed_no}/{pinion_ed_no}"

        new_part = QR2Part(
            crown_id=crown_id,
            crown_ed_no=crown_ed_no,
            pinion_id=pinion_id,
            pinion_ed_no=pinion_ed_no,
            ed_no=ed_no,
            employee_id=current_user.employee_id,
            user_type=current_user.user_type,
            username=current_user.username,
            status=status,
        )
        db.session.add(new_part)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'FQC-THANE part added'})
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/update_part_qr2/<int:part_id>', methods=['PUT'])
@login_required
def update_qr2_part(part_id):
    data = request.get_json()
    part = QR2Part.query.get_or_404(part_id)

    # Convert to uppercase
    part.crown_id = data.get('crown_id', '').strip().upper()
    part.crown_ed_no = data.get('crown_ed_no', '').strip().upper()
    part.pinion_id = data.get('pinion_id', '').strip().upper()
    part.pinion_ed_no = data.get('pinion_ed_no', '').strip().upper()
    part.status = data.get('status', '').strip().upper()

    part.ed_no = f"{part.crown_ed_no}/{part.pinion_ed_no}"
    part.modified_by = current_user.username
    part.modified_at = datetime.now()

    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "FQC-THANE part updated"})
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 400
@app.route('/api/qr2_parts/<int:part_id>/toggle', methods=['PATCH'])
def toggle_qr2_part_status(part_id):
    part = QR2Part.query.get_or_404(part_id)
    data = request.get_json()
    new_status = data.get("status", "").upper()

    if new_status not in ["ACTIVE", "INACTIVE"]:
        return jsonify({"status": "error", "error": "Invalid status"}), 400

    try:
        part.status = new_status
        part.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "success", "message": f"Status changed to {new_status}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/qr2_parts/<int:part_id>', methods=['GET'])
def get_qr2_part(part_id):
    part = QR2Part.query.get_or_404(part_id)
    return jsonify({
        "id": part.id,
        "crown_id": part.crown_id,
        "crown_ed_no": part.crown_ed_no,
        "pinion_id": part.pinion_id,
        "pinion_ed_no": part.pinion_ed_no,
        "status": part.status
    })


@app.route('/upload_qr2_excel', methods=['POST'])
@login_required
def upload_qr2_excel():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'status': 'error', 'error': 'No file selected'}), 400

    try:
        df = pd.read_excel(file)

        # ✅ Required columns now exclude 'status'
        required_cols = {'crown_id', 'crown_ed_no', 'pinion_id', 'pinion_ed_no'}
        if not required_cols.issubset(df.columns):
            return jsonify({'status': 'error', 'error': 'Missing required columns in Excel file'}), 400

        # Clean: trim whitespace, fill empty as '', convert to string uppercase
        df = df.fillna('').astype(str)
        df = df.applymap(lambda x: x.strip().upper())

        total = len(df)
        inserted = 0
        skipped = 0
        skipped_rows = []

        for _, row in df.iterrows():
            crown_id = row['crown_id']
            pinion_id = row['pinion_id']
            crown_ed_no = row['crown_ed_no']
            pinion_ed_no = row['pinion_ed_no']

            # ⛔️ Skip rows where required fields are empty
            if not crown_id or not pinion_id or not crown_ed_no or not pinion_ed_no:
                continue

            # Check for duplicates
            exists = QR2Part.query.filter_by(crown_id=crown_id, pinion_id=pinion_id).first()
            if exists:
                skipped += 1
                skipped_rows.append(f"{crown_id} / {pinion_id}")
                continue

            # Compute ED No.
            ed_no = crown_ed_no if crown_ed_no == pinion_ed_no else f"{crown_ed_no}/{pinion_ed_no}"

            part = QR2Part(
                crown_id=crown_id,
                crown_ed_no=crown_ed_no,
                pinion_id=pinion_id,
                pinion_ed_no=pinion_ed_no,
                ed_no=ed_no,
                status="ACTIVE", # ✅ Hardcoded to ACTIVE
                unit="1",         # ✅ default
                location="CWP-FQC",  # ✅ default
                username=current_user.username,
                employee_id=current_user.employee_id,
                user_type=current_user.user_type
            )

            db.session.add(part)
            inserted += 1

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'{total} rows processed. {inserted} inserted. {skipped} already existed.',
            'skipped_parts': skipped_rows
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/manage_admins')
@login_required
def manage_admins():
    if current_user.user_type != 'IT_ADMIN':
        return redirect(url_for('dashboard'))
    admins = User.query.filter(User.user_type.in_(['ADMIN', 'IT_ADMIN'])).all()
    return render_template('manage_admins.html', admins=admins)

@app.route('/admin/<employee_id>')
@login_required
def get_admin(employee_id):
    if current_user.user_type != 'IT_ADMIN':
        return jsonify({'error': 'Unauthorized'}), 403
    
    admin = User.query.get(employee_id)
    if not admin or admin.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Admin not found'}), 404
    
    return jsonify({
        'employee_id': admin.employee_id,
        'user_type': admin.user_type,
        'username': admin.username,
        'first_name': admin.first_name,
        'last_name': admin.last_name,
        'email': admin.email,
        'phone_number': admin.phone_number,
        'is_active': admin.is_active
    })

@app.route('/add_admin', methods=['POST'])
@login_required
def add_admin():
    if current_user.user_type != 'IT_ADMIN':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    try:
        if data.get('user_type') in ['ADMIN', 'IT_ADMIN'] and not data.get('employee_id'):
            return jsonify({'error': 'Employee ID is required for Admin/IT Admin'}), 400
        new_admin = User(
            employee_id=data['employee_id'],
            user_type=data['user_type'],  # 'ADMIN' or 'IT_ADMIN'
            username=data['username'],
            password=data['password'],  # Should be hashed in production
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone_number=data['phone_number'],
            created_by=current_user.employee_id,
            created_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            modified_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            is_active=True,
            is_deleted=False
        )
        
        if new_admin.user_type not in ['ADMIN', 'IT_ADMIN']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        db.session.add(new_admin)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'{new_admin.user_type} added successfully',
            'admin': {
                'employee_id': new_admin.employee_id,
                'user_type': new_admin.user_type,
                'username': new_admin.username,
                'full_name': f'{new_admin.first_name} {new_admin.last_name}',
                'email': new_admin.email,
                'phone_number': new_admin.phone_number,
                'is_active': new_admin.is_active
            }
        })
        
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@app.route('/update_admin/<employee_id>', methods=['PUT'])
@login_required
def update_admin(employee_id):
    if current_user.user_type != 'IT_ADMIN':
        return jsonify({'error': 'Unauthorized'}), 403
    
    admin = User.query.get(employee_id)
    if not admin or admin.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Admin not found'}), 404
    
    data = request.get_json()
    try:
        if 'user_type' in data and data['user_type'] not in ['ADMIN', 'IT_ADMIN']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        admin.user_type = data.get('user_type', admin.user_type)
        admin.username = data.get('username', admin.username)
        admin.first_name = data.get('first_name', admin.first_name)
        admin.last_name = data.get('last_name', admin.last_name)
        admin.email = data.get('email', admin.email)
        admin.phone_number = data.get('phone_number', admin.phone_number)
        if 'password' in data:
            admin.password = data['password']  # Should be hashed in production
        admin.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Admin updated successfully',
            'admin': {
                'employee_id': admin.employee_id,
                'user_type': admin.user_type,
                'username': admin.username,
                'full_name': f'{admin.first_name} {admin.last_name}',
                'email': admin.email,
                'phone_number': admin.phone_number,
                'is_active': admin.is_active
            }
        })
        
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': parse_integrity_error(err)}), 400    
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@app.route('/toggle_admin/<employee_id>', methods=['POST'])
@login_required
def toggle_admin(employee_id):
    if current_user.user_type != 'IT_ADMIN':
        return jsonify({'error': 'Unauthorized'}), 403
    
    admin = User.query.get(employee_id)
    if not admin or admin.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'error': 'Admin not found'}), 404
    
    # Prevent deactivating yourself
    if admin.employee_id == current_user.employee_id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    try:
        admin.is_active = not admin.is_active
        admin.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Admin {"activated" if admin.is_active else "deactivated"} successfully',
            'is_active': admin.is_active
        })
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@app.route('/upload_parts_excel', methods=['POST'])
@login_required
def upload_parts_excel():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return jsonify({'status': 'error', 'error': 'Unauthorized'}), 403

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'error': 'No file selected'}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'status': 'error', 'error': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'}), 400

    try:
        import pandas as pd
        df = pd.read_excel(file)

        df.columns = [col.strip().upper() for col in df.columns]
        required_columns = {'ID_NO', 'ED'}

        if not required_columns.issubset(set(df.columns)):
            return jsonify({'status': 'error', 'error': 'Missing required columns: ID_NO, ED'}), 400

        df = df.fillna('').astype(str)
        df['ID_NO'] = df['ID_NO'].str.strip().str.upper()
        df['ED'] = df['ED'].str.strip().str.upper()

        total = len(df)
        inserted = 0
        skipped = 0
        skipped_ids = []

        for _, row in df.iterrows():
            id_no = row['ID_NO']
            ed = row['ED']
            if id_no.strip() == '' or ed.strip() == '':
                continue


            

            existing_part = AddPart.query.filter_by(id_no=id_no).first()
            if existing_part:
                skipped += 1
                skipped_ids.append(id_no)
                continue

            new_part = AddPart(
                employee_id=current_user.employee_id,
                user_type=current_user.user_type,
                username=current_user.username,
                id_no=id_no,
                ed=ed,
                status='ACTIVE',
                created_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                modified_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(new_part)
            inserted += 1

        if inserted > 0:
            db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'{total} rows processed: {inserted} inserted, {skipped} skipped.',
            'inserted': inserted,
            'skipped': skipped,
            'skipped_ids': skipped_ids
        })

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': 'Failed to process Excel file',
            'details': str(e)
        }), 400

@app.route('/reports')
@login_required
def reports():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))
    return render_template('reports.html')

from flask import send_file, request, jsonify
from flask_login import login_required
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle
from reportlab.lib.pagesizes import landscape, A3
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from dateutil.relativedelta import relativedelta
@app.route('/download_report', methods=['POST'])
@login_required
def download_report():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.pagesizes import landscape, A3
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from io import BytesIO
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import os

    try:
        format_type = request.form.get('format', 'csv')
        machine = request.form.get('machine', 'qr1').lower()

        if machine == 'qr1':
            model = FQCPart
        elif machine == 'qr2':
            model = QR2ScanLog
        else:
            return jsonify({'error': 'Invalid machine type'}), 400

        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

        if start_date and end_date and end_date > start_date + relativedelta(months=3):
            return jsonify({'error': 'Date range cannot exceed 3 months'}), 400

        shift = request.form.get('shift')
        query = model.query

        if start_date:
            query = query.filter(model.timestamp >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(model.timestamp <= datetime.combine(end_date, datetime.max.time()))
        if shift:
            query = query.filter_by(shift=shift)

        data = query.order_by(model.timestamp.desc()).all()
        if not data:
            return jsonify({'error': 'No data found for the specified criteria'}), 404

        # ✅ PDF Generation
        if format_type == 'pdf':
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A3),
                                    leftMargin=10, rightMargin=10, topMargin=20, bottomMargin=20)

            styles = getSampleStyleSheet()
            elements = []

            from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.styles import ParagraphStyle

            # ---------- HEADER SECTION ----------
            logo_path = os.path.join(app.root_path, 'static', 'images', 'vecv.jpg')
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=2.2 * inch, height=0.75 * inch)
            else:
                logo_img = Paragraph('', styles['Normal'])

            # Title (centered)
            custom_title_style = ParagraphStyle('custom_title', fontSize=16, alignment=1, spaceAfter=10)
            title_para = Paragraph("<b>CWP-FQC VECV DEWAS</b>", custom_title_style)

            # Meta Info (left column)
            meta_style = ParagraphStyle('meta', fontSize=9, alignment=0, leading=12)
            meta_info = [
                logo_img,
                Spacer(1, 6),
                Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style),
                Paragraph(f"Date Range: {start_date_str or 'All'} to {end_date_str or 'All'}", meta_style),
                Paragraph(f"Shift: {shift or 'All'}", meta_style),
                Paragraph(f"Machine: {'FQC-DEWAS' if machine == 'qr1' else 'FQC-THANE'}", meta_style)
            ]

            # Header table: meta on left, heading on right
            header_table = RLTable([[meta_info, title_para]], colWidths=[270, 880])
            header_table.setStyle(RLTableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 16))

            # ---------- TABLE SECTION ----------
            if machine == 'qr1':
                headers = [
                    "Timestamp", "User Type", "Username", "Unit", "Location", "Shift",
                    "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
                    "Crown Set", "Pinion Set", "ED No", "Repeat No",
                    "Set Match", "Part Match", "Overall Status"
                ]
                table_data = [headers]
                for item in data:
                    table_data.append([
                        str(item.timestamp), item.user_type, item.username, item.unit, item.location, item.shift,
                        item.crown_scan, item.pinion_scan, item.crown_id_no, item.pinion_id_no,
                        item.crown_set_no, item.pinion_set_no, item.ed_no, item.repeat_no,
                        item.set_match, item.part_match, item.overall_status
                    ])
                col_widths = [90, 60, 70, 40, 60, 40, 110, 110, 80, 80, 60, 60, 60, 40, 60, 60, 70]

            else:  # QR2
                headers = [
                    "Timestamp", "User Type", "Username", "Unit", "Shift",
                    "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
                    "Crown Set", "Pinion Set", "ED No", "Repeat No",
                    "Set Match", "ED Match", "Overall Status"
                ]
                table_data = [headers]
                for item in data:
                    table_data.append([
                        str(item.timestamp), item.user_type, item.username, item.unit, item.shift,
                        item.crown_scan, item.pinion_scan, item.crown_id, item.pinion_id,
                        item.crown_set, item.pinion_set, item.ed_no, item.repeat_no,
                        item.set_match, item.ed_match, item.overall_status
                    ])
                col_widths = [90, 60, 70, 40, 40, 110, 110, 80, 80, 60, 60, 60, 40, 60, 60, 70]

            # PDF Table style
            table = Table(table_data, repeatRows=1, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))

            elements.append(table)
            doc.build(elements)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True,
                            download_name=f'download_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                            mimetype="application/pdf")
     
        # ------------------- CSV Export -------------------
        else:
            output = StringIO()
            writer = csv.writer(output)

            if machine == 'qr1':
                writer.writerow([
                    "Timestamp", "User Type", "Username", "Unit", "Location", "Shift",
                    "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
                    "Crown Set", "Pinion Set", "ED No", "Repeat No",
                    "Set Match", "Part Match", "Overall Status"
                ])
                for item in data:
                    writer.writerow([
                        item.timestamp, item.user_type, item.username, item.unit, item.location, item.shift,
                        item.crown_scan, item.pinion_scan, item.crown_id_no, item.pinion_id_no,
                        item.crown_set_no, item.pinion_set_no, item.ed_no, item.repeat_no,
                        item.set_match, item.part_match, item.overall_status
                    ])
            else:
                writer.writerow([
                    "Timestamp", "User Type", "Username", "Unit", "Shift",
                    "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
                    "Crown Set", "Pinion Set", "ED No", "Repeat No",
                    "Set Match", "ED Match", "Overall Status"
                ])
                for item in data:
                    writer.writerow([
                        item.timestamp.strftime('%Y-%m-%d %H:%M:%S'), item.user_type, item.username, item.unit, item.shift,
                        item.crown_scan, item.pinion_scan, item.crown_id, item.pinion_id,
                        item.crown_set, item.pinion_set, item.ed_no, item.repeat_no,
                        item.set_match, item.ed_match, item.overall_status
                    ])

            buffer = BytesIO(output.getvalue().encode('utf-8'))
            return send_file(buffer, as_attachment=True,
                             download_name=f'download_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                             mimetype='text/csv')

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/search_tabs', methods=['GET', 'POST'])
@login_required
def search_tabs():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))

    qr1_results = []
    qr2_results = []
    qr1_message = ""
    qr2_message = ""
    active_tab = 'qr1'  # Default

    if request.method == 'POST':
        search_type = request.form.get('search_type', 'qr1')
        active_tab = search_type

        if search_type == 'qr1':
            serial_no = request.form.get('serial_no', '').strip().upper().upper()
            set_no = request.form.get('set_no', '').strip().upper().upper()
            id_no = request.form.get('id_no', '').strip().upper().upper()

            query = FQCPart.query

            if not serial_no and not set_no and not id_no:
                # Fallback to today + current shift
                today = date.today()
                start_datetime = datetime.combine(today, datetime.min.time())
                end_datetime = start_datetime + timedelta(days=1)
                current_shift = get_current_shift()

                query = query.filter(
                    FQCPart.timestamp >= start_datetime,
                    FQCPart.timestamp < end_datetime,
                    FQCPart.shift == current_shift
                )
                qr1_results = query.order_by(FQCPart.timestamp.desc()).all()
                if not qr1_results:
                    qr1_message = "No part scanned in current shift."
            else:
                if serial_no:
                    query = query.filter((FQCPart.crown_scan == serial_no) | (FQCPart.pinion_scan == serial_no))
                if set_no:
                    query = query.filter((FQCPart.crown_set_no == set_no) | (FQCPart.pinion_set_no == set_no))
                if id_no:
                    query = query.filter((FQCPart.crown_id_no == id_no) | (FQCPart.pinion_id_no == id_no))

                qr1_results = query.order_by(FQCPart.timestamp.desc()).all()
                if not qr1_results:
                    qr1_message = "No results found. Please check your input."

        elif search_type == 'qr2':
            serial_no = request.form.get('serial_no', '').strip().upper()
            set_no = request.form.get('set_no', '').strip().upper()
            id_no = request.form.get('id_no', '').strip().upper()

            query = QR2ScanLog.query

            if not serial_no and not set_no and not id_no:
                today = date.today()
                start_datetime = datetime.combine(today, datetime.min.time())
                end_datetime = start_datetime + timedelta(days=1)
                current_shift = get_current_shift()

                query = query.filter(
                    QR2ScanLog.timestamp >= start_datetime,
                    QR2ScanLog.timestamp < end_datetime,
                    QR2ScanLog.shift == current_shift
                )
                qr2_results = query.order_by(QR2ScanLog.timestamp.desc()).all()
                if not qr2_results:
                    qr2_message = "No part scanned in current shift."
            else:
                if serial_no:
                    query = query.filter((QR2ScanLog.crown_scan == serial_no) | (QR2ScanLog.pinion_scan == serial_no))
                if set_no:
                    query = query.filter((QR2ScanLog.crown_set == set_no) | (QR2ScanLog.pinion_set == set_no))
                if id_no:
                    query = query.filter((QR2ScanLog.crown_id == id_no) | (QR2ScanLog.pinion_id == id_no))

                qr2_results = query.order_by(QR2ScanLog.timestamp.desc()).all()
                if not qr2_results:
                    qr2_message = "No results found. Please check your input."

    return render_template(
        "search_tabs.html",
        active_tab=active_tab,
        qr1_results=qr1_results,
        qr2_results=qr2_results,
        qr1_message=qr1_message,
        qr2_message=qr2_message
    )

 
from flask import request, render_template, redirect, url_for
from flask_login import login_required, current_user

from datetime import datetime, timedelta, date

# @app.route('/search', methods=['GET', 'POST'])
# @login_required
# def search():
#     if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
#         return redirect(url_for('dashboard'))

#     results = []
#     query = FQCPart.query

#     if request.method == 'POST':
#         serial_no = request.form.get('serial_no', '').strip()
#         set_no = request.form.get('set_no', '').strip()
#         id_no = request.form.get('id_no', '').strip()

#         if not serial_no and not set_no and not id_no:
#             # ✅ Use range filter instead of LIKE
#             today = date.today()
#             start_datetime = datetime.combine(today, datetime.min.time())
#             end_datetime = start_datetime + timedelta(days=1)

#             current_shift = get_current_shift()
#             query = query.filter(
#                 FQCPart.timestamp >= start_datetime,
#                 FQCPart.timestamp < end_datetime,
#                 FQCPart.shift == current_shift
#             )
#         else:
#             if serial_no:
#                 query = query.filter(
#                     (FQCPart.crown_scan == serial_no) |
#                     (FQCPart.pinion_scan == serial_no)
#                 )
#             if set_no:
#                 query = query.filter(
#                     (FQCPart.crown_set_no == set_no) |
#                     (FQCPart.pinion_set_no == set_no)
#                 )
#             if id_no:
#                 query = query.filter(
#                     (FQCPart.crown_id_no == id_no) |
#                     (FQCPart.pinion_id_no == id_no)
#                 )

#         results = query.order_by(FQCPart.timestamp.desc()).all()

#     return render_template('search_tabs.html', results=results)


@app.route('/download_search_pdf', methods=['POST'])
@login_required
def download_search_pdf():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import landscape, A3
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))

    serial_no = request.form.get('serial_no', '').strip().upper()
    set_no = request.form.get('set_no', '').strip().upper()
    id_no = request.form.get('id_no', '').strip().upper()

    query = FQCPart.query

    # ✅ Default fallback: current shift + today
    if not serial_no and not set_no and not id_no:
        today = date.today()
        start_datetime = datetime.combine(today, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        current_shift = get_current_shift()
        query = query.filter(
            FQCPart.timestamp >= start_datetime,
            FQCPart.timestamp < end_datetime,
            FQCPart.shift == current_shift
        )

        search_label = f"Current Shift: {current_shift}, Date: {today}"
    else:
        if serial_no:
            query = query.filter((FQCPart.crown_scan == serial_no) | (FQCPart.pinion_scan == serial_no))
        if set_no:
            query = query.filter((FQCPart.crown_set_no == set_no) | (FQCPart.pinion_set_no == set_no))
        if id_no:
            query = query.filter((FQCPart.crown_id_no == id_no) | (FQCPart.pinion_id_no == id_no))
        search_label = ""
        if serial_no: search_label += f"Serial No: {serial_no}  "
        if set_no: search_label += f"Set No: {set_no}  "
        if id_no: search_label += f"ID No: {id_no}"

    data = query.order_by(FQCPart.timestamp.desc()).all()
    if not data:
        return jsonify({'error': 'No data found'}), 404

    # PDF generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A3))
    styles = getSampleStyleSheet()
    elements = []
    # 🔗 Path to logo file
    logo_path = os.path.join(app.root_path, 'static', 'images', 'vecv.jpg')

    from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle
    from reportlab.lib.styles import ParagraphStyle

    # ✅ Load logo if exists
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=2.2 * inch, height=0.75 * inch)
    else:
        logo_img = Paragraph('', getSampleStyleSheet()['Normal'])

    # ✅ Create your original heading
    custom_title_style = ParagraphStyle('custom_title', fontSize=16, alignment=1, spaceAfter=10)
    title_para = Paragraph("<b> CWP FQC-DEWAS</b>", custom_title_style)

    # ✅ Combine into a header table (left: logo, center: title)
    header_table = RLTable([[logo_img, title_para]], colWidths=[250, 900])
    header_table.setStyle(RLTableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # ✅ Add to elements
    elements.append(header_table)
    elements.append(Spacer(1, 12))
        
        
    
        

    # elements.append(Spacer(1, 12))  # spacing below logo

    # elements.append(Paragraph("<b> CWP FQC-DEWAS</b>", styles['Title']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Report Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(search_label or "Search: All Results", styles['Normal']))
    elements.append(Spacer(1, 12))

    headers = [
        "Username", "User Type", "Timestamp", "Unit", "Location", "Shift",
        "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
        "Crown Set", "Pinion Set", "ED No", "Repeat No",
        "Set Match", "Part Match", "Overall Status"
    ]
    table_data = [headers]

    for row in data:
        table_data.append([
            row.username, row.user_type, str(row.timestamp), row.unit, row.location, row.shift,
            row.crown_scan, row.pinion_scan, row.crown_id_no, row.pinion_id_no,
            row.crown_set_no, row.pinion_set_no, row.ed_no, row.repeat_no,
            row.set_match, row.part_match, row.overall_status
        ])

    table = Table(table_data, repeatRows=1, colWidths=[
        60,   # Username
        60,   # User Type
        90,   # Timestamp
        50,   # Unit
        60,   # Location
        40,   # Shift
        120,  # Crown Scan
        120,  # Pinion Scan
        70,   # Crown ID
        70,   # Pinion ID
        60,   # Crown Set
        60,   # Pinion Set
        60,   # ED No
        50,   # Repeat No
        60,   # Set Match
        60,   # Part Match
        80    # Overall Status
    ])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f'search_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                     mimetype='application/pdf')


from flask import make_response
import csv

@app.route('/download_search_csv', methods=['POST'])
@login_required
def download_search_csv():
    import csv

    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))

    serial_no = request.form.get('serial_no', '').strip().upper()
    set_no = request.form.get('set_no', '').strip().upper()
    id_no = request.form.get('id_no', '').strip().upper()

    query = FQCPart.query

    if not serial_no and not set_no and not id_no:
        today = date.today()
        current_shift = get_current_shift()
        query = query.filter(
            db.func.date(FQCPart.timestamp) == today,
            FQCPart.shift == current_shift
        )
    else:
        if serial_no:
            query = query.filter((FQCPart.crown_scan == serial_no) | (FQCPart.pinion_scan == serial_no))
        if set_no:
            query = query.filter((FQCPart.crown_set_no == set_no) | (FQCPart.pinion_set_no == set_no))
        if id_no:
            query = query.filter((FQCPart.crown_id_no == id_no) | (FQCPart.pinion_id_no == id_no))

    data = query.order_by(FQCPart.timestamp.desc()).all()
    if not data:
        return jsonify({'error': 'No data found'}), 404

    # Use StringIO to write string data, then encode
    string_io = StringIO()
    writer = csv.writer(string_io)
    writer.writerow([
        "Username", "User Type", "Timestamp", "Unit", "Location", "Shift",
        "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
        "Crown Set", "Pinion Set", "ED No", "Repeat No",
        "Set Match", "Part Match", "Overall Status"
    ])
    for row in data:
        writer.writerow([
            row.username, row.user_type, row.timestamp, row.unit, row.location, row.shift,
            row.crown_scan, row.pinion_scan, row.crown_id_no, row.pinion_id_no,
            row.crown_set_no, row.pinion_set_no, row.ed_no, row.repeat_no,
            row.set_match, row.part_match, row.overall_status
        ])

    # Encode string data to bytes
    byte_stream = BytesIO()
    byte_stream.write(string_io.getvalue().encode('utf-8'))
    byte_stream.seek(0)

    return send_file(
        byte_stream,
        as_attachment=True,
        download_name=f'search_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mimetype='text/csv'
    )

# @app.route('/search_qr2', methods=['GET', 'POST'])
# @login_required
# def search_qr2():
#     if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
#         return redirect(url_for('dashboard'))

#     results = []
#     query = QR2ScanLog.query

#     if request.method == 'POST':
#         serial_no = request.form.get('serial_no', '').strip()
#         set_no = request.form.get('set_no', '').strip()
#         id_no = request.form.get('id_no', '').strip()

#         if not serial_no and not set_no and not id_no:
#             today = date.today()
#             current_shift = get_current_shift()
#             query = query.filter(
#                 db.func.date(QR2ScanLog.timestamp) == today,
#                 QR2ScanLog.shift == current_shift
#             )
#         else:
#             if serial_no:
#                 query = query.filter((QR2ScanLog.crown_scan == serial_no) | (QR2ScanLog.pinion_scan == serial_no))
#             if set_no:
#                 query = query.filter((QR2ScanLog.crown_set == set_no) | (QR2ScanLog.pinion_set == set_no))
#             if id_no:
#                 query = query.filter((QR2ScanLog.crown_id == id_no) | (QR2ScanLog.pinion_id == id_no))

#         results = query.order_by(QR2ScanLog.timestamp.desc()).all()

#     return render_template('search_qr2.html', results=results)


@app.route('/download_search_pdf_qr2', methods=['POST'])
@login_required
def download_search_pdf_qr2():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import landscape, A3
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))


    query = QR2ScanLog.query
    serial_no = request.form.get('serial_no', '').strip().upper()
    set_no = request.form.get('set_no', '').strip().upper()
    id_no = request.form.get('id_no', '').strip().upper()

    if serial_no:
        query = query.filter((QR2ScanLog.crown_scan == serial_no) | (QR2ScanLog.pinion_scan == serial_no))
    if set_no:
        query = query.filter((QR2ScanLog.crown_set == set_no) | (QR2ScanLog.pinion_set == set_no))
    if id_no:
        query = query.filter((QR2ScanLog.crown_id == id_no) | (QR2ScanLog.pinion_id == id_no))
    search_label = ""
    if serial_no: search_label += f"Serial No: {serial_no}  "
    if set_no: search_label += f"Set No: {set_no}  "
    if id_no: search_label += f"ID No: {id_no}"

    data = query.order_by(QR2ScanLog.timestamp.desc()).all()
    if not data:
        return jsonify({'error': 'No data found'}), 404

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A3))
    styles = getSampleStyleSheet()
    elements = []
    logo_path = os.path.join(app.root_path, 'static', 'images', 'vecv.jpg')
    from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle
    from reportlab.lib.styles import ParagraphStyle

    # ✅ Prepare image and title in left + center layout
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=2.2 * inch, height=0.75 * inch)
    else:
        logo_img = Paragraph('', styles['Normal'])

    custom_title_style = ParagraphStyle('custom_qr2_title', fontSize=16, alignment=1, spaceAfter=10)
    title_para = Paragraph("<b>CWP FQC-THANE Report</b>", custom_title_style)

    # ✅ Combine into header table
    header_table = RLTable([[logo_img, title_para]], colWidths=[250, 900])
    header_table.setStyle(RLTableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 12))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Report Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(search_label or "Search: All Results", styles['Normal']))
    elements.append(Spacer(1, 12))


    headers = [
        "Username", "User Type", "Timestamp", "Unit", "Shift",
        "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
        "Crown Set", "Pinion Set", "ED No", "Repeat No",
        "Set Match", "ED Match", "Overall Status"
    ]

    table_data = [headers]
    for row in data:
        table_data.append([
            row.username, row.user_type, row.timestamp.strftime('%Y-%m-%d %H:%M:%S'), row.unit, row.shift,
            row.crown_scan, row.pinion_scan, row.crown_id, row.pinion_id,
            row.crown_set, row.pinion_set, row.ed_no, row.repeat_no,
            row.set_match, row.ed_match, row.overall_status
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f'search_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                     mimetype='application/pdf')


@app.route('/download_search_csv_qr2', methods=['POST'])
@login_required
def download_search_csv_qr2():
    if current_user.user_type not in ['ADMIN', 'IT_ADMIN']:
        return redirect(url_for('dashboard'))

    serial_no = request.form.get('serial_no', '').strip().upper()
    set_no = request.form.get('set_no', '').strip().upper()
    id_no = request.form.get('id_no', '').strip().upper()

    query = QR2ScanLog.query
    if not serial_no and not set_no and not id_no:
        today = date.today()
        current_shift = get_current_shift()
        query = query.filter(
            db.func.date(FQCPart.timestamp) == today,
            FQCPart.shift == current_shift
        )
    else:
        if serial_no:
            query = query.filter((QR2ScanLog.crown_scan == serial_no) | (QR2ScanLog.pinion_scan == serial_no))
        if set_no:
            query = query.filter((QR2ScanLog.crown_set == set_no) | (QR2ScanLog.pinion_set == set_no))
        if id_no:
            query = query.filter((QR2ScanLog.crown_id == id_no) | (QR2ScanLog.pinion_id == id_no))

    data = query.order_by(QR2ScanLog.timestamp.desc()).all()
    if not data:
        return jsonify({'error': 'No data found'}), 404

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Username", "User Type", "Timestamp", "Unit", "Shift",
        "Crown Scan", "Pinion Scan", "Crown ID", "Pinion ID",
        "Crown Set", "Pinion Set", "ED No", "Repeat No",
        "Set Match", "ED Match", "Overall Status"
    ])

    for row in data:
        writer.writerow([
            row.username, row.user_type, row.timestamp.strftime('%Y-%m-%d %H:%M:%S'), row.unit, row.shift,
            row.crown_scan, row.pinion_scan, row.crown_id, row.pinion_id,
            row.crown_set, row.pinion_set, row.ed_no, row.repeat_no,
            row.set_match, row.ed_match, row.overall_status
        ])

    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    output.close()

    return send_file(mem, mimetype='text/csv',
                     download_name=f'search_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                     as_attachment=True)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = 'FQC Password Reset OTP'

        body = f"""
        <p>Dear user,</p>
        <p>Your OTP for password reset is: <strong>{otp}</strong></p>
        <p>Do not share it with anyone.</p>
        """
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())

        return True
    except Exception as e:
        print("Email send failed:", e)
        return False


@app.route('/forgot_password/<role>', methods=['GET', 'POST'])
def forgot_password(role):
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()

        # Role Check
        user = User.query.filter_by(email=email, user_type=role.upper(), is_active=True).first()
        if not user:
            flash(f"No Active {role.upper()} user found with this email.", "danger")
            return render_template("forgot_password.html", role=role)

        # OTP Generation
        otp = str(random.randint(100000, 999999))
        session['reset_otp'] = otp
        session['reset_user_id'] = user.employee_id

        if send_otp_email(email, otp):
            flash("OTP sent to your registered email.", "info")
            return redirect(url_for('verify_otp'))
        else:
            flash("Failed to send OTP. Please try again.", "danger")

    return render_template("forgot_password.html", role=role)


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp').strip()
        if entered_otp == session.get('reset_otp'):
            return redirect(url_for('reset_password', employee_id=session['reset_user_id']))
        else:
            flash("Invalid OTP. Please try again.", "danger")
    return render_template("verify_otp.html")



@app.route('/reset_password/<employee_id>', methods=['GET', 'POST'])
def reset_password(employee_id):
    user = User.query.get(employee_id)
    if not user:
        flash('Invalid user', 'danger')
        return redirect(url_for('forgot_password', role='operator'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', user=user)

        user.password = new_password  # ⚠️ Hash in production
        user.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

        flash('Password updated successfully!', 'success')
        session.pop('reset_otp', None)
        session.pop('reset_user_id', None)
        return redirect(url_for('index'))

    return render_template('reset_password.html', user=user)

import subprocess
import os

def start_node_report_service():
    node_script_path = os.path.join(os.path.dirname(__file__), 'report_sender.js')
    try:
        subprocess.Popen(['node', node_script_path])
        print("✅ Node report_sender.js service started.")
    except Exception as e:
        print("❌ Failed to start report_sender.js:", e)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    start_node_report_service()    
    app.run(debug=True)
    
