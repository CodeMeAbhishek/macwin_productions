# Unisphere Project Documentation 📚

## 1. Technology Stack 🛠️

### Frontend
- HTML5 & CSS3
- JavaScript
- Django Templates
- Bootstrap (for responsive design)

### Backend
- Django 5.0.2
- Python 3.x
- Django Channels 4.0.0 (for WebSocket support)
- Redis 5.0.1 (for real-time communication)

### Database
- SQLite3 (Development)
- Django ORM

### DevOps & Deployment
- Daphne 4.0.0 (ASGI server)
- Redis (for WebSocket support)

## 2. Implemented Features and Pages 🚀

### Chat Application
- Real-time messaging using WebSockets
- User authentication and authorization
- Message history and persistence
- Online/offline status indicators
- Message read receipts
- File sharing capabilities

### User Profiles
- User profile management
- Profile picture upload and management
- User information editing
- Profile visibility settings

### Core Features
- User authentication system
- Session management
- URL routing and view handling
- Static file serving
- Media file handling

## 3. Project Architecture and Flow 🔄

### High-Level Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Django    │────▶│  Database   │
│  (Browser)  │◀────│  Backend    │◀────│  (SQLite)   │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                    ▲
       │                    │
       ▼                    ▼
┌─────────────┐     ┌─────────────┐
│  WebSocket  │     │    Redis    │
│  Connection │     │   Server    │
└─────────────┘     └─────────────┘
```

### Data Flow
1. User Authentication Flow:
   - User submits credentials
   - Django authenticates and creates session
   - User receives authentication token

2. Chat Message Flow:
   - User sends message
   - Message processed by Django Channels
   - Message stored in database
   - Real-time delivery via WebSocket
   - Recipient receives message instantly

3. Profile Management Flow:
   - User updates profile information
   - Changes saved to database
   - Profile page updated with new information

## 4. Dependencies and Their Purpose 📦

### Core Dependencies
- `Django==5.0.2`: Main web framework
- `asgiref==3.7.2`: ASGI specification implementation
- `sqlparse==0.4.4`: SQL parsing and formatting
- `tzdata==2024.1`: Timezone database

### Real-time Communication
- `channels==4.0.0`: WebSocket support for Django
- `channels-redis==4.1.0`: Redis backend for Channels
- `daphne==4.0.0`: ASGI server for Django Channels
- `redis==5.0.1`: Redis client for Python

### Media Handling
- `Pillow==10.2.0`: Image processing library

## 5. Directory Structure 📁

```
unisphere/
├── core/                 # Core application settings and configuration
├── chat/                 # Chat application
│   ├── static/          # Static files (CSS, JS, images)
│   ├── templates/       # HTML templates
│   ├── models.py        # Database models
│   ├── views.py         # View logic
│   ├── consumers.py     # WebSocket consumers
│   └── routing.py       # WebSocket routing
├── profiles/            # User profiles application
├── media/               # User-uploaded media files
├── requirements.txt     # Project dependencies
└── manage.py           # Django management script
```

## 6. Security Features 🔒

- User authentication and authorization
- CSRF protection
- Secure password handling
- Session management
- File upload security
- WebSocket connection security

## 7. Future Enhancements 🚀

- Group chat functionality
- Message encryption
- Video/audio calling
- Push notifications
- Advanced search functionality
- User activity analytics
- Multi-language support 