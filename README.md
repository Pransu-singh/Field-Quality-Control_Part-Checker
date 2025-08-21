# FQC Part Checker System

A web-based Quality Control System for checking and validating crown and pinion parts, with user management and reporting capabilities.

## Features

- **User Authentication**
  - Multiple user roles (Operator, Admin, IT Admin)
  - Secure login system
  - Role-based access control

- **Part Scanning**
  - Real-time crown and pinion part scanning
  - Automatic validation and matching
  - Instant feedback on part compatibility
  - Auto-focus and submission

- **User Management**
  - Add/Edit/Deactivate operators
  - Manage admin accounts (IT Admin only)
  - Track user activities

- **Part Management**
  - Add individual parts
  - Bulk upload via Excel
  - Manage part IDs and ED numbers

- **Reporting**
  - Generate PDF/CSV reports
  - Filter by date range and shift
  - Custom part ID filtering

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome

## Setup Instructions

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure PostgreSQL**
   - Install PostgreSQL if not already installed
   - Create a new database named 'fqc_system'
   - Update the DATABASE_URL in .env file if needed

4. **Initialize Database**
   ```bash
   # Start Python shell
   python
   >>> from app import app, db
   >>> with app.app_context():
   ...     db.create_all()
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Application**
   - Open browser and navigate to: http://localhost:5000
   - Default IT Admin credentials:
     - Employee ID: 1234
     - Password: 12345678

## Project Structure

```
FQC_3/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── static/
│   └── css/
│       └── style.css  # Global styles
├── templates/
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── login.html     # Login page
│   ├── dashboard.html # User dashboard
│   ├── scan_parts.html# Part scanning page
│   └── reports.html   # Report generation
└── uploads/           # Excel file uploads
```

## Database Schema

### User Table
- employee_id (PK)
- user_type
- username
- password
- first_name
- last_name
- email
- phone_number
- created_by
- created_date
- modified_date
- is_active
- is_deleted

### FQC Part Table
- id (PK)
- employee_id (FK)
- user_type
- username
- unit
- location
- timestamp
- shift
- crown_scan
- pinion_scan
- crown_id_no
- pinion_id_no
- crown_set_no
- pinion_set_no
- ed_no
- repeat_no
- set_match
- part_match
- overall_status

### Add Part Table
- id (PK)
- employee_id (FK)
- user_type
- username
- id_no
- ed
- status
- created_date
- modified_date

### Login Table
- id (PK)
- employee_id (FK)
- user_type
- username
- last_login

## Security Considerations

1. Password hashing should be implemented in production
2. Use HTTPS in production
3. Implement rate limiting for login attempts
4. Regular security audits
5. Keep dependencies updated

## Maintenance

1. Regular database backups
2. Log rotation
3. Monitor system performance
4. Update security patches

## Support

For support and issues, please contact the IT department.