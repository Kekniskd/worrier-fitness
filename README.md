# Gym Management System

## Overview
The Gym Management System is designed to help gym administrators manage members, track attendance, and handle payments efficiently. It includes features for sending announcements via WhatsApp and managing staff.

## Features
- User registration and login
- Membership management
- Attendance tracking
- Payment recording
- WhatsApp announcements
- Membership expiry reminders

## Architecture Diagram
```mermaid
graph TD;
    A[User] -->|Registers| B[Web Application]
    B --> C[Database]
    B --> D[WhatsApp API]
    C --> E[User Table]
    C --> F[Membership Table]
    C --> G[Plan Table]
    C --> H[Attendance Table]
    C --> I[Staff Table]
```

## Database Schema
```mermaid
erDiagram
    User {
        int id PK
        string username
        string email
        string phone
        string address
        boolean is_admin
        string member_id
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
    Attendance {
        int id PK
        int user_id FK
        date date
    }
    Staff {
        int id PK
        string name
        string email
        string phone
        string position
        float salary
        string address
    }
```

## Flow Diagrams
### User Registration Flow
```mermaid
flowchart TD;
    A[Start] --> B[Enter User Details]
    B --> C{Is Username Unique?}
    C -->|Yes| D[Create User]
    C -->|No| E[Show Error]
    D --> F[Redirect to Dashboard]
    E --> B
```

### Sending WhatsApp Announcements
```mermaid
flowchart TD;
    A[Start] --> B[Select Recipient Type]
    B --> C[Compose Message]
    C --> D[Send Message]
    D --> E{Success?}
    E -->|Yes| F[Show Success Message]
    E -->|No| G[Show Error Message]
```

## Usage Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gym-management-system.git
   cd gym-management-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```
   WHATSAPP_TOKEN=your_whatsapp_token_here
   PHONE_NUMBER_ID=your_phone_number_id_here
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at `http://localhost:5000`.

## Conclusion
The Gym Management System provides a comprehensive solution for managing gym operations efficiently. With features like WhatsApp notifications and membership tracking, it enhances the user experience for both administrators and members.