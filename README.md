# Social Media Content Planner

A Django-based SaaS platform for scheduling and automating social media posts across multiple platforms.

## Features

- User authentication and profile management
- Social media account integration (Twitter, Instagram, LinkedIn)
- Post scheduling and automation
- Content calendar view
- Analytics tracking
- Freemium subscription model

## Tech Stack

- Backend: Django
- Database: SQLite (development)
- Task Queue: Celery with Redis
- Authentication: Django OAuth Toolkit
- Frontend: HTML, CSS, JavaScript (Bootstrap)

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the database:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Install and start Redis (required for Celery):
```bash
# On macOS with Homebrew:
brew install redis
brew services start redis

# On Ubuntu:
sudo apt-get install redis-server
sudo service redis-server start
```

6. Start Celery worker:
```bash
celery -A social_planner worker -l info
```

7. Start Celery beat for scheduled tasks:
```bash
celery -A social_planner beat -l info
```

8. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

- `accounts/`: User authentication and profile management
- `social_accounts/`: Social media platform integration
- `posts/`: Post creation, scheduling, and management
- `analytics/`: Analytics tracking and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License. 