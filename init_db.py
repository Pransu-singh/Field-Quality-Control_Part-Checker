from app import app, db, User, AddPart, LoginLog, FQCPart
from datetime import datetime

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if IT Admin exists
        if not User.query.filter_by(employee_id='1234').first():
            # Create IT Admin
            it_admin = User(
                employee_id='1234',
                user_type='IT_ADMIN',
                username='VVERMAG',
                password='12345678',
                first_name='VISHAL',
                last_name='VERMA',
                email='VVERMAG@VECV.IN',
                phone_number='8851857434',
                created_by='EMPID',
                created_date='20:34.7',
                modified_date='39:12.7',
                is_active=True,
                is_deleted=False
            )
            db.session.add(it_admin)

        # Create Admin
        if not User.query.filter_by(employee_id='567').first():
            admin = User(
                employee_id='567',
                user_type='ADMIN',
                username='RAVI',
                password='12345',
                first_name='RAVI',
                last_name='CHAWADA',
                email='ZZRCHAWADA@VECV.IN',
                phone_number='123457890',
                created_by='EMPID',
                created_date='46:27.3',
                modified_date='45:48.6',
                is_active=True,
                is_deleted=False
            )
            db.session.add(admin)

        # Create Operator
        if not User.query.filter_by(employee_id='2345').first():
            operator = User(
                employee_id='2345',
                user_type='OPERATOR',
                username='ABC',
                password='123',
                first_name='HANS',
                last_name='RAJ',
                email='amitravat@vecv.in',
                phone_number='+91 9328971172',
                created_by='EMPID',
                created_date='22:43.1',
                modified_date='26:06.7',
                is_active=True,
                is_deleted=False
            )
            db.session.add(operator)

        # Add sample parts
        sample_parts = [
            {'id_no': 'D10190240', 'ed': '6148/51', 'status': 'ACTIVE'},
            {'id_no': '006504487B91', 'ed': '6338/6361', 'status': 'NOT_ACTIVE'},
            {'id_no': '1310A01101', 'ed': '6750/51', 'status': 'ACTIVE'}
        ]

        for part in sample_parts:
            if not AddPart.query.filter_by(id_no=part['id_no']).first():
                new_part = AddPart(
                    employee_id='1234',  # Added by IT Admin
                    user_type='IT_ADMIN',
                    username='VVERMAG',
                    id_no=part['id_no'],
                    ed=part['ed'],
                    status=part['status'],
                    created_date=datetime.now().strftime('%d-%b'),
                    modified_date=datetime.now().strftime('%d-%b')
                )
                db.session.add(new_part)

        # Add sample FQC part check
        if not FQCPart.query.filter_by(crown_scan='PID313626A#TFD-87#').first():
            fqc_part = FQCPart(
                employee_id='2345',
                user_type='OPERATOR',
                username='ABC',
                unit='UNIT-1',
                location='CWPFQC',
                timestamp='26-06-2025 06:28',
                shift='C',
                crown_scan='PID313626A#TFD-87#',
                pinion_scan='PID313626A#TFD-87#',
                crown_id_no='ID313626',
                pinion_id_no='ID313626',
                crown_set_no='FD-87',
                pinion_set_no='FD-87',
                ed_no='5680/81',
                set_match='YES',
                part_match='YES',
                overall_status='OK'
            )
            db.session.add(fqc_part)

        # Add sample login log
        if not LoginLog.query.filter_by(employee_id='2345').first():
            login_log = LoginLog(
                employee_id='2345',
                user_type='OPERATOR',
                username='ABC',
                last_login='27-Jun'
            )
            db.session.add(login_log)

        # Commit all changes
        db.session.commit()

if __name__ == '__main__':
    init_database()
    print('Database initialized successfully!')