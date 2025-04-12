# Gym Management System

A comprehensive gym management system built with Flask for managing members, staff, memberships, attendance, and payments.

## System Architecture

```mermaid
graph TD
    A[Web Interface] --> B[Flask Application]
    B --> C[(SQLite Database)]
    B --> D[WhatsApp API]
    
    subgraph Backend Services
        B --> E[Member Management]
        B --> F[Staff Management]
        B --> G[Attendance System]
        B --> H[Payment Processing]
        B --> I[Notification System]
    end
    
    subgraph Database Tables
        C --> J[Users]
        C --> K[Staff]
        C --> L[Memberships]
        C --> M[Attendance]
        C --> N[Plans]
        C --> O[Payments]
    end
```

## User Roles and Access Flow

```mermaid
flowchart TD
    A[User Types] --> B[Admin]
    A --> C[Moderator]
    A --> D[Member]
    
    B --> E[Full System Access]
    B --> F[Staff Management]
    B --> G[Financial Controls]
    
    C --> H[Limited Access]
    C --> I[Staff Attendance]
    C --> J[Member Management]
    
    D --> K[Self Service]
    D --> L[Attendance Marking]
    D --> M[View Profile]
```

## Membership Management Flow

```mermaid
stateDiagram-v2
    [*] --> NewMember
    NewMember --> ActiveMembership: Register & Pay
    ActiveMembership --> ExpiringMembership: 7 Days Before
    ExpiringMembership --> ExpiredMembership: Not Renewed
    ExpiringMembership --> ActiveMembership: Renew
    ExpiredMembership --> ActiveMembership: Late Renewal
    ActiveMembership --> [*]: Terminate
```

## Attendance Tracking System

```mermaid
sequenceDiagram
    participant M as Member/Staff
    participant S as System
    participant D as Database
    participant N as Notification
    
    M->>S: Mark Attendance
    S->>D: Check Previous Entry
    alt No Previous Entry
        D->>S: Confirm No Entry
        S->>D: Record Attendance
        S->>N: Confirm Success
    else Already Marked
        D->>S: Entry Exists
        S->>N: Show Warning
    end
    N->>M: Display Result
```

## Staff Management Flow

```mermaid
flowchart LR
    A[Add Staff] --> B[Active Staff]
    B --> C{Daily Tasks}
    C --> D[Mark Attendance]
    C --> E[Record Payment]
    B --> F[Deactivate]
    F --> G[Inactive Staff]
    G --> B[Reactivate]
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gym-management.git
cd gym-management
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
uv add -r requirements.txt
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Create an admin moderator:
```bash
python create_moderator.py
```

6. Run the application:
```bash
flask run
```

## Features

### Member Management
- Add/Edit/View members
- Generate unique member IDs
- Track membership status
- Handle membership renewals
- View attendance history

### Staff Management
- Add/Edit/View staff
- Track staff attendance
- Manage staff payments
- Staff activity status control

### Membership Plans
- Create/Edit membership plans
- Set duration and pricing
- Track active/expired memberships

### Attendance System
- Mark member attendance
- Mark staff attendance
- View attendance reports
- Track check-in times

### Payment Processing
- Record membership payments
- Process staff salaries
- Track payment history
- Multiple payment methods

### Notification System
- WhatsApp integration
- Membership expiry reminders
- Announcements to members
- Customizable messages

### Access Control
- Role-based access control
- Admin and moderator roles
- Secure authentication
- Activity logging

## Database Schema

```mermaid
erDiagram
    User ||--o{ Membership : has
    User ||--o{ Attendance : marks
    User ||--o{ Payment : makes
    Plan ||--o{ Membership : includes
    Staff ||--o{ StaffAttendance : marks
    Staff ||--o{ StaffPayment : receives

    User {
        int id PK
        string member_id
        string username
        string email
        string phone
        string address
        datetime join_date
    }

    Membership {
        int id PK
        int user_id FK
        int plan_id FK
        date start_date
        date end_date
        boolean active
    }

    Plan {
        int id PK
        string name
        int duration
        float price
        string description
    }

    Staff {
        int id PK
        string name
        string email
        string phone
        string position
        float salary
        boolean is_active
    }

    StaffAttendance {
        int id PK
        int staff_id FK
        datetime check_in
        string status
    }

    StaffPayment {
        int id PK
        int staff_id FK
        float amount
        date payment_date
        string payment_method
    }
```

## API Endpoints

### Member Routes
- `GET /members` - List all members
- `POST /members/add` - Add new member
- `GET /members/<id>` - View member details
- `POST /members/<id>/renew` - Renew membership

### Staff Routes
- `GET /staff` - List all staff
- `POST /staff/add` - Add new staff
- `GET /staff/<id>` - View staff details
- `POST /staff/attendance` - Mark staff attendance

### Plan Routes
- `GET /plans` - List all plans
- `POST /plans/add` - Add new plan
- `DELETE /plans/<id>` - Delete plan

### Attendance Routes
- `POST /attendance/mark` - Mark attendance
- `GET /attendance/today` - View today's attendance

### Payment Routes
- `POST /payments/record` - Record payment
- `GET /payments/history` - View payment history

## Security Considerations

1. Authentication
- Secure password hashing
- Session management
- Role-based access control

2. Data Protection
- Input validation
- SQL injection prevention
- XSS protection

3. API Security
- Rate limiting
- Request validation
- Error handling

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.