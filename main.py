import os
import mysql.connector
import mysql.connector as mysql
from flask import Flask, render_template, request, flash, redirect, url_for, session
from mysql.connector import connection, cursor
import requests
import json
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# News API keys - You'll need to sign up for these
CNN_API_KEY = "9ef757c06ccc41b383d96ce2853627c0"  # Replace with your actual API key
NDTV_API_KEY = "9ef757c06ccc41b383d96ce2853627c0"  # Replace with your actual API key


# Database connection function
def get_db_connection():
    try:
        conn = mysql.connect(user='root', password='root', host='127.0.0.1',
                             charset='utf8', database='newsinfo')
        return conn
    except mysql.Error as err:
        logger.error(f"Database connection error: {err}")
        return None


@app.route('/')
def home():
    return render_template('Homepage.html')


@app.route('/about')
def about():
    return render_template('Aboutus.html')


@app.route('/contact')
def contact():
    return render_template('Contactus.html')


@app.route('/adminhome')
def adminhome():
    # Get news statistics for admin dashboard
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get total news count
    cursor.execute("SELECT COUNT(*) FROM api_news")
    news_count = cursor.fetchone()[0]

    # Get last fetched time
    cursor.execute("SELECT MAX(fetched_at) FROM api_news")
    last_fetched_result = cursor.fetchone()[0]
    last_fetched = last_fetched_result.strftime("%Y-%m-%d %H:%M:%S") if last_fetched_result else "Never"

    # Get 5 most recent news items
    cursor.execute("SELECT * FROM api_news ORDER BY fetched_at DESC LIMIT 5")
    recent_news = cursor.fetchall()

    # Get category statistics
    cursor.execute("SELECT category, COUNT(*) as count FROM api_news GROUP BY category ORDER BY count DESC")
    category_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('Adminhome.html', news_count=news_count,
                           last_fetched=last_fetched, recent_news=recent_news,
                           category_stats=category_stats)


@app.route('/userhome')
def userhome():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please login to access the user home page", "error")
        return redirect(url_for('login'))

    # Get latest news for the user dashboard
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get 5 most recent news items from all sources
    cursor.execute("SELECT * FROM api_news ORDER BY published_at DESC LIMIT 6")
    latest_news = cursor.fetchall()

    # Get top news categories
    cursor.execute("SELECT category, COUNT(*) as count FROM api_news GROUP BY category ORDER BY count DESC LIMIT 5")
    top_categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('Userhome.html', latest_news=latest_news,
                           top_categories=top_categories, username=session.get('username'))


@app.route('/categorynews')
def categorynews():
    # Get all available categories
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM newsdetails")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('Categorynews.html', categories=categories)


@app.route('/uploadnews')
def uploadnews():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    cursor.execute("select MAX(Newsid) from newsdetails")
    data = cursor.fetchone()
    rid = data[0]
    if rid == None:
        rid = "1"
        print(rid)
    else:
        rid = rid + 1

    # Get all available categories for dropdown
    cursor.execute("SELECT DISTINCT category FROM api_news")
    categories = cursor.fetchall()

    cursor.close()
    db_connection.close()
    return render_template('uploadnews.html', Newsid=rid, categories=categories)


@app.route('/Register')
def Register():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    cursor.execute("select MAX(Regid) from Register")
    data = cursor.fetchone()
    rid = data[0]
    if rid == None:
        rid = "1"
        print(rid)
    else:
        rid = rid + 1
    cursor.close()
    db_connection.close()
    return render_template('Register.html', Regid=rid)


@app.route('/insert', methods=['POST'])
def insert():
    if request.method == "POST":
        try:
            Regid = request.form['Regid']
            rname = request.form['rname']
            contact = request.form['contact']
            email = request.form['email']
            Address = request.form['Address']
            city = request.form['city']
            role = request.form['role']
            uname = request.form['uname']
            password = request.form['password']

            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Check if username already exists
            cursor.execute("SELECT * FROM register WHERE uname = %s", (uname,))
            if cursor.fetchone():
                flash("Username already exists. Please choose another username.", "error")
                return redirect(url_for('Register'))

            cursor.execute(
                "INSERT INTO register (rname, contact, email, Address, city, role, uname, password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                (rname, contact, email, Address, city, role, uname, password))

            db_connection.commit()
            cursor.close()
            db_connection.close()

            flash("Registration Successfully! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash("Error during registration. Please try again.", "error")
            return render_template('Register.html')


@app.route('/insertnews', methods=['POST'])
def insertnews():
    if request.method == "POST":
        try:
            Newsid = request.form['Newsid']
            newshead = request.form['newshead']
            upload = request.form['dateinfo']
            category = request.form['category']
            Description = request.form['Description']

            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            cursor.execute(
                "INSERT INTO newsdetails (Newsid, newshead, upload, category, Description) VALUES(%s, %s, %s, %s, %s)",
                (Newsid, newshead, upload, category, Description))

            db_connection.commit()
            cursor.close()
            db_connection.close()

            flash("News Detail Upload Successfully!", "success")
            return redirect(url_for('adminhome'))
        except Exception as e:
            logger.error(f"News upload error: {e}")
            flash("Error uploading news. Please try again.", "error")
            return redirect(url_for('uploadnews'))


@app.route('/fetch_cnn_news', methods=['POST'])
def fetch_cnn_news():
    try:
        # Add debug logging
        logger.info("Starting CNN news fetch")

        # Real API call to fetch CNN news
        url = f"https://newsapi.org/v2/top-headlines?sources=cnn&apiKey={CNN_API_KEY}"
        logger.info(f"Requesting news from URL: {url.replace(CNN_API_KEY, 'API_KEY_HIDDEN')}")

        response = requests.get(url)
        logger.info(f"API Response status code: {response.status_code}")

        if response.status_code != 200:
            error_message = f"API request failed with status code {response.status_code}: {response.text}"
            logger.error(error_message)
            raise Exception(error_message)

        # Log response info
        data = response.json()
        logger.info(f"API Response status: {data.get('status')}")
        logger.info(f"Articles received: {len(data.get('articles', []))}")

        if data.get('status') != 'ok':
            error_message = f"API returned non-OK status: {data.get('status')} - {data.get('message', 'No message')}"
            logger.error(error_message)
            raise Exception(error_message)

        articles = data.get('articles', [])
        if not articles:
            logger.warning("No articles returned from API")

        # Store articles in database
        db_connection = get_db_connection()
        if not db_connection:
            raise Exception("Failed to establish database connection")

        cursor = db_connection.cursor()

        stored_count = 0
        for article in articles:
            try:
                # Safety checks for required fields
                if not article.get('title') or not article.get('source', {}).get('name'):
                    logger.warning(f"Skipping article due to missing title or source: {article}")
                    continue

                # Check if article already exists to avoid duplicates
                cursor.execute("SELECT id FROM api_news WHERE title = %s AND source = %s",
                               (article['title'], article['source']['name']))

                if cursor.fetchone() is None:
                    # Format the date properly - handle different date formats
                    try:
                        published_at = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        try:
                            published_at = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            published_at = datetime.now()  # Fallback to current time

                    # Extract category from the URL or set a default
                    category = "General"
                    if article.get('url'):
                        if '/business/' in article['url']:
                            category = "Business"
                        elif '/politics/' in article['url']:
                            category = "Politics"
                        elif '/tech/' in article['url'] or '/technology/' in article['url']:
                            category = "Technology"
                        elif '/health/' in article['url']:
                            category = "Health"
                        elif '/entertainment/' in article['url']:
                            category = "Entertainment"
                        elif '/sports/' in article['url'] or '/sport/' in article['url']:
                            category = "Sports"

                    # Ensure description isn't None
                    description = article.get('description', '')
                    if description is None:
                        description = ''

                    cursor.execute(
                        "INSERT INTO api_news (source, title, description, url, image_url, published_at, category, fetched_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
                        (article['source']['name'], article['title'], description,
                         article.get('url', ''), article.get('urlToImage', ''), published_at, category)
                    )
                    stored_count += 1
            except Exception as article_error:
                logger.error(f"Error processing article: {article_error}")
                # Continue with next article

        db_connection.commit()
        cursor.close()
        db_connection.close()

        logger.info(f"Stored {stored_count} CNN news articles")
        flash(f"Successfully fetched {stored_count} CNN news articles!", "success")
    except Exception as e:
        logger.error(f"CNN news fetch error: {str(e)}")
        flash(f"Error fetching CNN news: {str(e)}", "error")

    return redirect(url_for('adminhome'))


@app.route('/fetch_ndtv_news', methods=['POST'])
def fetch_ndtv_news():
    try:
        # Add debug logging
        logger.info("Starting NDTV news fetch")

        # Try multiple approaches to get Indian news
        sources_to_try = [
            {"url": f"https://newsapi.org/v2/top-headlines?sources=ndtv&apiKey={NDTV_API_KEY}",
             "description": "NDTV source"},
            {"url": f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NDTV_API_KEY}",
             "description": "Indian news"},
            {"url": f"https://newsapi.org/v2/everything?domains=ndtv.com&apiKey={NDTV_API_KEY}",
             "description": "NDTV domain"}
        ]

        response = None
        data = None
        for source in sources_to_try:
            try:
                logger.info(
                    f"Trying to fetch {source['description']} from URL: {source['url'].replace(NDTV_API_KEY, 'API_KEY_HIDDEN')}")
                response = requests.get(source['url'])
                logger.info(f"API Response status code: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok' and len(data.get('articles', [])) > 0:
                        logger.info(
                            f"Successfully got {len(data.get('articles', []))} articles from {source['description']}")
                        break
            except Exception as source_error:
                logger.warning(f"Error trying {source['description']}: {str(source_error)}")

        if not data or data.get('status') != 'ok':
            if response:
                error_message = f"All API requests failed. Last status: {data.get('status')} - {data.get('message', 'No message')}"
            else:
                error_message = "All API requests failed. No valid response received."
            logger.error(error_message)
            raise Exception(error_message)

        articles = data.get('articles', [])
        if not articles:
            logger.warning("No articles returned from any API endpoint")
            flash("No articles found from NDTV or Indian news sources", "warning")
            return redirect(url_for('adminhome'))

        # Store articles in database
        db_connection = get_db_connection()
        if not db_connection:
            raise Exception("Failed to establish database connection")

        cursor = db_connection.cursor()

        stored_count = 0
        for article in articles:
            try:
                # Safety checks for required fields
                if not article.get('title') or not article.get('source', {}).get('name'):
                    logger.warning(f"Skipping article due to missing title or source: {article}")
                    continue

                # Check if article already exists to avoid duplicates
                cursor.execute("SELECT id FROM api_news WHERE title = %s AND source = %s",
                               (article['title'], article['source']['name']))

                if cursor.fetchone() is None:
                    # Format the date properly - handle different date formats
                    try:
                        published_at = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        try:
                            published_at = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            published_at = datetime.now()  # Fallback to current time

                    # Extract category from the URL or set a default
                    category = "General"
                    if article.get('url'):
                        if '/business/' in article['url']:
                            category = "Business"
                        elif '/politics/' in article['url']:
                            category = "Politics"
                        elif '/tech/' in article['url'] or '/technology/' in article['url']:
                            category = "Technology"
                        elif '/health/' in article['url']:
                            category = "Health"
                        elif '/entertainment/' in article['url']:
                            category = "Entertainment"
                        elif '/sports/' in article['url'] or '/sport/' in article['url']:
                            category = "Sports"
                        elif '/india/' in article['url']:
                            category = "India"
                        elif '/world/' in article['url']:
                            category = "World"

                    # Ensure description isn't None
                    description = article.get('description', '')
                    if description is None:
                        description = ''

                    cursor.execute(
                        "INSERT INTO api_news (source, title, description, url, image_url, published_at, category, fetched_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
                        (article['source']['name'], article['title'], description,
                         article.get('url', ''), article.get('urlToImage', ''), published_at, category)
                    )
                    stored_count += 1
            except Exception as article_error:
                logger.error(f"Error processing article: {article_error}")
                # Continue with next article

        db_connection.commit()
        cursor.close()
        db_connection.close()

        logger.info(f"Stored {stored_count} NDTV/Indian news articles")
        flash(f"Successfully fetched {stored_count} NDTV/Indian news articles!", "success")
    except Exception as e:
        logger.error(f"NDTV news fetch error: {str(e)}")
        flash(f"Error fetching NDTV news: {str(e)}", "error")

    return redirect(url_for('adminhome'))


@app.route('/checklogin', methods=['POST'])
def checklogin():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        utype = request.form['utype']

        if username == 'Admin' and password == 'Admin' and utype == 'Admin':
            session['admin_logged_in'] = True
            return redirect(url_for('adminhome'))

        if utype == "User":
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            cursor.execute(
                "SELECT Regid, rname FROM register WHERE uname = %s AND password = %s",
                (username, password))
            account = cursor.fetchone()
            cursor.close()
            db_connection.close()

            if account:
                # Set session variables
                session['user_logged_in'] = True
                session['user_id'] = account[0]
                session['username'] = account[1]
                flash(f"Welcome back, {account[1]}!", "success")
                return redirect(url_for('userhome'))
            else:
                flash("Invalid username or password!", "error")
                return render_template('login.html')

        flash("Invalid user type or credentials", "error")
        return render_template('login.html')

    return render_template('login.html')


@app.route('/viewnews')
def viewnews():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM newsdetails ORDER BY upload DESC")
    result = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return render_template('viewnews.html', postlist=result)


@app.route('/viewnewsuser')
def viewnewsuser():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please login to view news", "error")
        return redirect(url_for('login'))

    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    # Get all news from both sources
    cursor.execute("""
        SELECT * FROM (
            SELECT 'internal' as source_type, Newsid as id, newshead as title, 
                   Description as description, upload as published_at, category, NULL as url, NULL as image_url 
            FROM newsdetails
            UNION ALL
            SELECT 'api' as source_type, id, title, description, published_at, 
                   category, url, image_url 
            FROM api_news
        ) AS combined_news
        ORDER BY published_at DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return render_template('viewnewsuser.html', postlist=result, username=session.get('username'))


@app.route('/view_api_news')
def view_api_news():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM api_news ORDER BY published_at DESC")
    result = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return render_template('view_api_news.html', news_list=result)


@app.route('/getcategory', methods=['POST', 'GET'])
def getcategory():
    if request.method == 'POST':
        category = request.form['category']
    else:
        category = request.args.get('category')

    if not category:
        flash("No category selected", "error")
        return redirect(url_for('categorynews'))

    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    # Get news from both sources for selected category
    cursor.execute("""
        SELECT * FROM (
            SELECT 'internal' as source_type, Newsid as id, newshead as title, 
                   Description as description, upload as published_at, category, NULL as url, NULL as image_url 
            FROM newsdetails WHERE category = %s
            UNION ALL
            SELECT 'api' as source_type, id, title, description, published_at, 
                   category, url, image_url 
            FROM api_news WHERE category = %s
        ) AS combined_news
        ORDER BY published_at DESC
    """, (category, category))

    data = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return render_template('viewnews1.html', postlist=data, selected_category=category)


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
    else:
        search_query = request.args.get('search_query')

    if not search_query:
        flash("Please enter a search term", "error")
        return redirect(url_for('userhome'))

    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    # Search in both sources
    cursor.execute("""
        SELECT * FROM (
            SELECT 'internal' as source_type, Newsid as id, newshead as title, 
                   Description as description, upload as published_at, category, NULL as url, NULL as image_url 
            FROM newsdetails 
            WHERE newshead LIKE %s OR Description LIKE %s
            UNION ALL
            SELECT 'api' as source_type, id, title, description, published_at, 
                   category, url, image_url 
            FROM api_news 
            WHERE title LIKE %s OR description LIKE %s
        ) AS combined_news
        ORDER BY published_at DESC
    """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))

    results = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return render_template('search_results.html', postlist=results, search_query=search_query)


@app.route('/login')
def login():
    # Clear any existing session
    session.clear()
    return render_template('Login.html')


@app.route('/Logout')
def Logout():
    # Clear the session
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for('login'))


@app.route('/news_detail/<source_type>/<int:news_id>')
def news_detail(source_type, news_id):
    db_connection = get_db_connection()
    cursor = db_connection.cursor(dictionary=True)  # Use dictionary cursor for easier access

    if source_type == 'internal':
        cursor.execute("SELECT * FROM newsdetails WHERE Newsid = %s", (news_id,))
        news = cursor.fetchone()
        if news:
            result = {
                'id': news['Newsid'],
                'title': news['newshead'],
                'date': news['upload'],
                'category': news['category'],
                'content': news['Description'],
                'source_type': 'internal',
                'image_url': 'static/assets/images/news-placeholder.jpg'  # Default image for internal news
            }
    else:  # API news
        cursor.execute("SELECT * FROM api_news WHERE id = %s", (news_id,))
        news = cursor.fetchone()
        if news:
            # Check if image URL is a placeholder or null
            image_url = news['image_url']
            if not image_url or 'example.com' in image_url:
                image_url = 'static/assets/images/news-placeholder.jpg'

            result = {
                'id': news['id'],
                'source': news['source'],
                'title': news['title'],
                'content': news['description'],
                'url': news['url'],
                'image_url': image_url,
                'date': news['published_at'],
                'category': news['category'],
                'source_type': 'api'
            }

    cursor.close()
    db_connection.close()

    if not news:
        flash("News article not found", "error")
        return redirect(url_for('userhome'))

    return render_template('news_detail.html', news=result)


if __name__ == "__main__":
    app.run(debug=True)