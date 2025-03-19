NewsHub - Real-time News Aggregator

NewsHub is a comprehensive news aggregation platform that fetches news from multiple sources and displays them in a user-friendly interface. The application uses the News API to gather the latest headlines and articles from various news providers, categorizes them, and presents them in an organized manner.

Features

- Real-time News Collection: Fetches current news articles from multiple sources including CNN, NDTV, and other Indian news outlets
- User Authentication: Secure login system with role-based access control (admin/user)
- News Categories: Browse news by categories such as Business, Technology, Sports, etc.
- Search Functionality: Search for specific news articles across all sources
- Admin Dashboard: Comprehensive admin interface for managing news sources and viewing statistics
- User Dashboard: Personalized user experience with recommended and popular news articles
- Responsive Design: Fully responsive interface that works on desktops, tablets, and mobile devices

 Technology Stack

- Backend: Python Flask framework
- Database: MySQL
- Frontend: HTML, CSS, JavaScript, Bootstrap
- APIs: News API integration
- Authentication: Session-based authentication
- Logging: Built-in logging system for error tracking and debugging

Installation

Prerequisites

- Python 3.6+
- MySQL
- News API key (sign up at [newsapi.org](https://newsapi.org))

Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/newshub.git
   cd newshub
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the MySQL database:
   ```
   mysql -u root -p
   CREATE DATABASE newsinfo;
   USE newsinfo;
   ```

5. Import the database schema (SQL file in the repository):
   ```
   mysql -u root -p newsinfo < database_schema.sql
   ```

6. Update the API keys in the application:
   - Open the main Python file
   - Replace the placeholder API keys with your actual News API keys

7. Run the application:
   ```
   python app.py
   ```

8. Access the application at [http://localhost:5000](http://localhost:5000)

Database Schema

The application uses the following main tables:

- `register`: Stores user registration information
- `newsdetails`: Stores manually uploaded news articles
- `api_news`: Stores news articles fetched from external APIs

Usage

Admin User

1. Log in as admin (username: Admin, password: Admin)
2. Access the admin dashboard to:
   - View news statistics
   - Fetch news from external sources
   - Upload manual news articles
   - Manage categories

Regular User

1. Register a new account
2. Log in with your credentials
3. Browse news by categories
4. Search for specific news articles
5. Read detailed news articles

API Integration

The application integrates with News API to fetch articles from various sources. The API keys are used in the following routes:

- `/fetch_cnn_news`: Fetches news from CNN
- `/fetch_ndtv_news`: Fetches news from NDTV and other Indian sources

Customization

You can customize the application by:

1. Adding more news sources
2. Modifying the category extraction logic
3. Updating the UI theme
4. Adding more features like user comments or ratings

Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Acknowledgements

- [News API](https://newsapi.org) for providing the news data
- Flask and its extensions for the web framework
- Bootstrap for the responsive design
