# QueueSmart - Appointment & Queue Management System

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

## Access Points

- **Client**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/login/
- **Staff**: http://localhost:8000/staff/login/

## Features

✅ Client appointment booking
✅ Staff queue management
✅ Admin dashboard
✅ Email notifications
✅ Real-time queue tracking