from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import re
import MySQLdb.cursors
from ebaysdk.finding import Connection
from ebaysdk.trading import Connection as Trading
from ebaysdk.merchandising import Connection as Merchandising
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'COMP0022'
# Enter your database connection details below
app.config['MYSQL_HOST'] = 'comp002205.mysql.database.azure.com'
app.config['MYSQL_USER'] = 'comp002205@comp002205'
app.config['MYSQL_PASSWORD'] = 'Comp0022'
app.config['MYSQL_DB'] = 'comp0022'

# Intialize MySQL
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'loggedin' in session:
        return redirect(url_for('profile'))
    else:
        # User is not loggedin redirect to login page
        api = Merchandising(config_file='ebay.yaml', siteid="EBAY-GB")
        response = api.execute('getMostWatchedItems')
        return render_template('index.html', response=response)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', [username])
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account and check_password_hash(account['password'], password):
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('profile'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        city = request.form['city']
        postcode = request.form['postcode']
        country = request.form['country']
        interest = request.form['interest']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', [username])
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not re.match(r'[ A-Za-z]+', city):
            msg = 'Address must contain only characters and numbers!'
        elif not re.match(r'[A-Za-z0-9]+', postcode):
            msg = 'Postcode must contain only characters and numbers!'
        elif not re.match(r'[ A-Za-z]+', country):
            msg = 'Country must contain only characters and numbers!'
        elif not re.match(r'[0-9]+', phone):
            msg = 'Phone number must contain only numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT IGNORE INTO address VALUES (%s, %s, %s)', [postcode, city, country])
            mysql.connection.commit()
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, %s, %s)',
                           [username, generate_password_hash(password), email, phone, postcode, interest])
            mysql.connection.commit()
            return redirect(url_for('profile'))
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT EXISTS (SELECT 1 FROM category)')
    if sum(cursor.fetchone().values()) is 0:
        api = Trading(config_file="ebay.yaml", domain="api.sandbox.ebay.com", debug=True)
        callData = {
            'DetailLevel': 'ReturnAll',
            'CategorySiteID': 0,
            'LevelLimit': 1
        }
        response = api.execute('GetCategories', callData)
        for i in response.reply.CategoryArray.Category:
            cursor.execute('INSERT INTO category VALUES (%s, %s)', [i.CategoryID, i.CategoryName])
        mysql.connection.commit()
        cursor.execute('SELECT categoryName FROM category ORDER BY category.categoryName ASC')
        category = cursor.fetchall()
        return render_template('register.html', msg=msg, response=category)
    else:
        cursor.execute('SELECT categoryName FROM category ORDER BY category.categoryName ASC')
        category = cursor.fetchall()
        return render_template('register.html', msg=msg, response=category)


@app.route('/modify', methods=['GET', 'POST'])
def modify():
    msg = ''
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM address WHERE postcode = %s', [account['postcode']])
        address = cursor.fetchone()
        if request.method == 'POST' and 'password' in request.form and 'email' in request.form and 'phone' in request.form:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            id = session['id']
            email = request.form['email']
            phone = request.form['phone']
            password = request.form['password']
            interest = request.form['interest']
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[0-9]+', phone):
                msg = 'Phone number must contain only numbers!'
            else:
                cursor.execute('UPDATE accounts SET password = %s, email = %s, interest=%s WHERE id = %s',
                               [generate_password_hash(password), email, interest, id])
                mysql.connection.commit()
                return redirect(url_for('profile'))
        if request.method == 'POST' and 'city' in request.form and 'postcode' in request.form and 'country' in request.form:
            postcode = request.form['postcode']
            city = request.form['city']
            country = request.form['country']
            if not re.match(r'[ A-Za-z0-9]+', city):
                msg = 'Address must contain only characters and numbers!'
            elif not re.match(r'[A-Za-z0-9]+', postcode):
                msg = 'Postcode must contain only characters and numbers!'
            elif not re.match(r'[ A-Za-z]+', country):
                msg = 'Country must contain only characters and numbers!'
            else:
                cursor.execute('UPDATE address SET postcode = %s, city = %s, country=%s WHERE postcode = %s',
                               [postcode, city, country, account['postcode']])
                mysql.connection.commit()
                return redirect(url_for('profile'))
        # Show the profile page with account info
        cursor.execute('SELECT categoryName FROM category ORDER BY category.categoryName ASC')
        category = cursor.fetchall()
        return render_template('modify.html', account=account, msg=msg, response=category, address=address)
    else:
        redirect(url_for('login'))


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to main page
    return redirect(url_for('index'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    msg = ''
    if request.method == 'POST' and 'search' in request.form:
        search = request.form['search']
        api = Connection(config_file='ebay.yaml', siteid="EBAY-GB")
        requests = {
            'keywords': search,
            'itemFilter': [
                {'name': 'condition', 'value': 'new'}
            ],
            'paginationInput': {
                'entriesPerPage': 10,
                'pageNumber': 1
            },
            'sortOrder': 'BestMatch'
        }
        response = api.execute('findItemsByKeywords', requests)
        return render_template('search.html', response=response)
    else:
        return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT categoryID FROM category WHERE categoryName = (SELECT interest FROM accounts WHERE id = %s)',
            [session['id']])
        interestID = cursor.fetchone()
        if interestID is None:
            session.pop('loggedin', None)
            session.pop('id', None)
            session.pop('username', None)
            # Redirect to main page
            return redirect(url_for('index'))
        api = Connection(config_file='ebay.yaml', siteid="EBAY-GB")
        requests = {
            'categoryId': interestID['categoryID'],
            'paginationInput': {
                'entriesPerPage': 20,
                'pageNumber': 1
            },
            'sortOrder': 'BestMatch',
            'itemFilter': [
                {'name': 'HideDuplicateItems', 'value': 'true'},
                {'name': 'ListingType', 'value': 'Auction'}
            ],
            'outputSelector': 'SellerInfo'
        }
        response = api.execute('findItemsAdvanced', requests)
        print(response.reply.searchResult.item)
        for i in response.reply.searchResult.item:
            cursor.execute('INSERT IGNORE INTO items VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                           [i.itemId, i.title, 'New', i.sellingStatus.currentPrice.value,
                            i.sellingStatus.currentPrice._currencyId, i.sellingStatus.sellingState,
                            i.listingInfo.endTime, i.galleryURL, i.viewItemURL])
            mysql.connection.commit()
            cursor.execute('INSERT IGNORE INTO item_category_junction VALUES (%s, %s)',
                           [i.itemId, interestID['categoryID']])
            mysql.connection.commit()
            cursor.execute('INSERT IGNORE INTO seller VALUES (%s, %s, %s)',
                           [i.sellerInfo.sellerUserName, i.sellerInfo.feedbackScore,
                            i.sellerInfo.positiveFeedbackPercent])
            mysql.connection.commit()
            cursor.execute('INSERT IGNORE INTO item_seller VALUES (%s, %s)', [i.itemId, i.sellerInfo.sellerUserName])
            mysql.connection.commit()
        if request.method == 'POST' and 'itemID' in request.form:
            itemID = request.form['itemID']
            if not re.match(r'[0-9]+', itemID):
                print("wrong")
                return render_template('profile.html', response=response)
            else:
                cursor.execute('INSERT IGNORE INTO favourite VALUES (%s, %s)', [session['id'], itemID])
                mysql.connection.commit()
                return redirect(url_for('save'))
        # Show the profile page with account info
        return render_template('profile.html', response=response)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/save', methods=['GET', 'POST'])
def save():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM items INNER JOIN favourite ON items.itemID = favourite.itemID')
        product = cursor.fetchall()
        if request.method == 'POST' and 'itemID' in request.form:
            itemID = request.form['itemID']
            if not re.match(r'[0-9]+', itemID):
                return render_template('saved.html', product=product)
            else:
                cursor.execute('DELETE FROM favourite WHERE userID = %s AND itemID = %s', [session['id'], itemID])
                mysql.connection.commit()
                return redirect(url_for('save'))
        return render_template('saved.html', product=product)
    return redirect(url_for('login'))


@app.route('/search_logged', methods=['GET', 'POST'])
def search_logged():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST' and 'search' in request.form:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            print('flag')
            search = request.form['search']
            api = Connection(config_file='ebay.yaml', siteid="EBAY-GB")
            requests = {
                'keywords': search,
                'itemFilter': [
                    {'name': 'condition', 'value': 'new'}
                ],
                'paginationInput': {
                    'entriesPerPage': 10,
                    'pageNumber': 1
                },
                'sortOrder': 'BestMatch',
                'outputSelector': 'SellerInfo'
            }
            response = api.execute('findItemsByKeywords', requests)
            print(response.reply.ack)
            if response.reply.ack == 'Failure':
                msg = 'Please type again'
                return redirect(url_for('profile'))
            priceRange = []
            for i in response.reply.searchResult.item:
                cursor.execute('INSERT IGNORE INTO items VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                               [i.itemId, i.title, 'New', i.sellingStatus.currentPrice.value,
                                i.sellingStatus.currentPrice._currencyId, i.sellingStatus.sellingState,
                                i.listingInfo.endTime, i.galleryURL, i.viewItemURL])
                priceRange.append(i.sellingStatus.currentPrice.value)
                mysql.connection.commit()
                cursor.execute('INSERT IGNORE INTO seller VALUES (%s, %s, %s)',
                               [i.sellerInfo.sellerUserName, i.sellerInfo.feedbackScore,
                                i.sellerInfo.positiveFeedbackPercent])
                mysql.connection.commit()
                cursor.execute('INSERT IGNORE INTO item_seller VALUES (%s, %s)',
                               [i.itemId, i.sellerInfo.sellerUserName])
                mysql.connection.commit()
            priceRange.sort()
            priceRange = [float(i) for i in priceRange]
            return render_template('search_logged.html', response=response, search=search, priceRange=priceRange)
        if request.method == 'POST' and 'itemID' in request.form:
            itemID = request.form['itemID']
            if not re.match(r'[0-9]+', itemID):
                return redirect(url_for('profile'))
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT IGNORE INTO favourite VALUES (%s, %s)', [session['id'], itemID])
                mysql.connection.commit()
                return redirect(url_for('save'))
        return redirect(url_for('login'))
    return redirect(url_for('login'))


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'loggedin' in session:
        if 'itemID1' in request.form:
            itemID = request.form['itemID1']
            print(type(itemID))
            print(itemID)
            msg = ''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'SELECT * FROM seller WHERE sellerName = (SELECT sellerID FROM item_seller WHERE itemID = %s)',
                [itemID])
            feedback = cursor.fetchone()
            cursor.execute('SELECT AVG(`sellerFeedbackScore`) FROM `seller`')
            average = cursor.fetchone()
            print(average['AVG(`sellerFeedbackScore`)'])
            cursor.execute('SELECT * FROM items WHERE itemID = %s', [itemID])
            item = cursor.fetchone()
            return render_template('feedback.html', feedback=feedback, item=item,
                                   average=float(average['AVG(`sellerFeedbackScore`)']))
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
