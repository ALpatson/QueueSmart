# QueueSmart - Appointment & Queue Management System
QueueSmart is a role-based appointment booking and queue management system designed to manage clients, staff, and services with secure access control and real-time notifications.
##  Release
- **v1.0.0 – MVP**: Initial stable release with core booking, admin security, notifications, and password reset workflows.

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: venv\Scripts\activate
   - macOS/Linux: source venv/bin/activate
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

## Access Points

- **Client**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/login/
- **Staff**: http://localhost:8000/staff/login/

##  Features
- Client appointment booking
- Staff queue and service management
- Secure admin dashboard with restricted access
- Service creation and assignment to staff
- Email notifications for appointment updates and cancellations
- Secure password reset for clients
- Staff password reset using temporary credentials with mandatory change on first login
