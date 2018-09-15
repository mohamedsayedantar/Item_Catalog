from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_create import Categories, Base, Items, User
from flask import session as login_session
from flask import session
import random
import string
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from sqlalchemy.inspection import inspect
import simplejson
from functools import wraps

app = Flask(__name__)

# get the client secret from the json file
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Categories"

#connect to the database
engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/login')
def login():
    login_session.clear()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("""Current user is
        already connected."""),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/logedin/catalog')

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ " style = "width: 300px; height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> """
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = """https://accounts.google.com/o/oauth2/r
    evoke?token=%s""" % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect('/')
    else:
        # clear the session when error happen to DISCONNECT the user
        login_session.clear()
        return redirect('/')


@app.route('/')
@app.route('/catalog')
def homepage():
    # the home page contain all categories and items
    items = session.query(Items).all()
    categories = session.query(Categories).all()
    return render_template('home.html', categories=categories, items=items)


@app.route('/logedin/catalog')
@login_required
def homepage_userin():
    # the home page when the user is logged in

    if getUserID(login_session['email']) is None:
        createUser(login_session)
        userId = getUserID(login_session['email'])
    else:
        userId = getUserID(login_session['email'])

    items = session.query(Items).all()
    categories = session.query(Categories).all()
    return render_template(
        'home_userin.html', categories=categories, items=items)


@app.route('/catalog/<string:category_name>')
def categoriesfunc(category_name):
    # when specific category is choosed to find all items in it
    categories = session.query(Categories).all()
    id = session.query(Categories.id).filter_by(name=category_name).all()
    items = session.query(Items).filter_by(categories_id=id[0][0]).all()
    count = session.query(Items).filter_by(categories_id=id[0][0]).count()
    return render_template('categories.html', categories=categories,
                           items=items, category=category_name, count=count)


@app.route('/logedin/catalog/<string:category_name>')
@login_required
def categoriesfunc_logedin(category_name):
    # the same categoriesfunc but when the user is logged in
    categories = session.query(Categories).all()
    id = session.query(Categories.id).filter_by(name=category_name).all()
    items = session.query(Items).filter_by(categories_id=id[0][0]).all()
    count = session.query(Items).filter_by(categories_id=id[0][0]).count()
    return render_template('categories_userin.html', categories=categories,
                           items=items, category=category_name, count=count)


@app.route('/catalog/<string:category_name>/<string:item_name>')
def item_description(category_name, item_name):
    # to show each item discribtion
    description = session.query(Items.description).filter_by(name=item_name
                                                             ).first()
    return render_template('description.html',
                           description=description[0], item_name=item_name)


@app.route('/catalog/<string:category_name>/<string:item_name>/otherUser')
def item_description2(category_name, item_name):
    # to show each item discribtion for some one's item to another user
    description = session.query(Items.description).filter_by(name=item_name
                                                             ).first()
    return render_template('descriptionOtherUser.html',
                           description=description[0], item_name=item_name)


@app.route('/logedin/catalog/<string:category_name>/<string:item_name>')
@login_required
def item_description_logedin(category_name, item_name):
    # to show the item discribtion whith eddit or delete property for the owner

    if getUserID(login_session['email']) is None:
        createUser(login_session)
        userId = getUserID(login_session['email'])
    else:
        userId = getUserID(login_session['email'])

    print (userId)
    print (session.query(Items.user_id).filter_by(name=item_name).first()[0])

    if userId != session.query(Items.user_id).filter_by(name=item_name
                                                        ).first()[0]:
        description = session.query(Items.description).filter_by(name=item_name
                                                                 ).first()
        return render_template('descriptionOtherUser.html',
                               description=description[0], item_name=item_name)

    description = session.query(Items.description).filter_by(name=item_name
                                                             ).first()
    return render_template('description_userin.html',
                           description=description[0], item_name=item_name,
                           category=category_name)


@app.route('/additem')
@login_required
def addItem():
    # to add items, any user can use

    categories = session.query(Categories).all()
    return render_template('addItem.html', categories=categories)


@app.route('/handle_data1', methods=['POST'])
@login_required
def handle_data1():
    # handling the data from add temlpate

    if getUserID(login_session['email']) is None:
        createUser(login_session)
        userId = getUserID(login_session['email'])
    else:
        userId = getUserID(login_session['email'])

    category_name = request.form['select']
    if request.form['Item1'] == '':
        return """sorry you did not enter any name to your item,
        please go back and choose one"""

    newName = request.form['Item1']
    try:
        if newName == session.query(Items.name).filter_by(name=newName
                                                          ).first()[0]:
            return """sorry this name is existed! please go back
            and choose another one"""
    except:
        id = session.query(Categories.id).filter_by(name=category_name).all()
        item1 = Items(name=request.form['Item1'],
                      description=request.form['Dis1'],
                      categories_id=id[0][0], user_id=userId)
        session.add(item1)
        session.commit()
        return redirect('/logedin/catalog')


@app.route('/logedin/catalog/<string:category_name>/<string:item_name>/eddit')
@login_required
def EdditItem(category_name, item_name):
    # eddit item for the item owner only
    userId = getUserID(login_session['email'])
    if userId != session.query(Items.user_id).filter_by(name=item_name
                                                        ).first()[0]:
        return "sorry this item is not belong to you"
    return render_template('editItem.html',
                           category_name=category_name, item_name=item_name)


@app.route('/handle_data2', methods=['POST'])
@login_required
def handle_data2():
    # handling the data from eddit template
    if request.form['Item1'] == '':
        return """sorry you did not enter any name to your item,
        please go back and choose one"""

    oldName = request.form['item_name']
    newName = request.form['Item1']
    newDis = request.form['Dis1']
    try:
        if newName == session.query(Items.name).filter_by(name=newName
                                                          ).first()[0]:
            return """sorry this name is existed! please go back
            and choose another one"""
    except:
        item = session.query(Items).filter_by(name=oldName).first()
        item.name = newName
        item.description = newDis
        session.commit()
        return redirect('/logedin/catalog')


@app.route('/logedin/catalog/<string:category_name>/<string:item_name>/remove')
@login_required
def RemoveItem(category_name, item_name):
    # if the item owner wants to delete this item
    userId = getUserID(login_session['email'])
    if userId != session.query(Items.user_id).filter_by(name=item_name
                                                        ).first()[0]:
        return "sorry this item is not belong to you"
    return render_template('removeItem.html', category=category_name,
                           item_name=item_name)


@app.route('/handle_data3', methods=['POST'])
@login_required
def handle_data3():
    # handling the data from remove template
    Name = request.form['item_name']
    session.query(Items).filter_by(name=Name).delete()
    session.commit()
    return redirect('/logedin/catalog')


@app.route('/catalog.json')
def Json():
    # the json end point file generator
    items = session.query(Items).all()
    categories = session.query(Categories).all()
    cat = []
    its = []

    for category in categories:
        for item in items:
            if item.categories_id == category.id:
                it = {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "categories_id": item.categories_id
                }
                its.append(it)

        as_dict = {
            "id": category.id,
            "name": category.name,
            "items": its
            }
        its = []
        cat.append(as_dict)

    theCategory = {
                   "category": cat
    }
    return simplejson.dumps(theCategory)


@app.route('/<string:item_name>/json')
def Json2(item_name):

    # the json end point file generator for any item
    items = session.query(Items).all()
    its = []
    for item in items:
        if item.name == item_name:
            it = {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "categories_id": item.categories_id
            }
            its.append(it)

    theItem = {
                   item_name+" item": its
    }
    return simplejson.dumps(theItem)


@app.route('/Bat.json')
def Json3():

    # the json end point file generator for any item
    items = session.query(Items).all()
    its = []
    for item in items:
        if item.name == "Bat":
            it = {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "categories_id": item.categories_id
            }
            its.append(it)

    theItem = {
                   "Bat": its
    }
    return simplejson.dumps(theItem)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
