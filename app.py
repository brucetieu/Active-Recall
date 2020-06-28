import os
import matplotlib
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, Response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import numpy as np
import pandas as pd
import seaborn as sbn


from helpers import login_required

# Configure application
app = Flask(__name__)

# Initialize the graph folder
GRAPH_FOLDER = os.path.join('static')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = GRAPH_FOLDER

# Matplotlib relies on some backend to actually render the plots. The default backend is the agg backend.
# This backend only renders PNGs.
matplotlib.use('Agg')

# Add a time to session to expire
@app.before_request
def make_session_permanent():
    session.permanent = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = 'VEDK4d7NUfoCu-ADiFg-tA'
Session(app)

# Connect to the SQL db
# If check_same_thread=False, the returned connection may be shared across multiple threads.
conn = sqlite3.connect("recall.db", check_same_thread=False)

# Create a cursor object to execute SQL statements
db = conn.cursor()

@app.route("/")
def home():
    """ Display information about active recall """
    return render_template('home.html', title='Home')

# Get page of username password (GET) then log user in (POST)
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        db.execute("SELECT * FROM users WHERE username = (:username)", (request.form['username'],))
        rows = db.fetchall()
        # print(rows)

        if not rows:
            flash('That username does not exist. Try registering first before logging in!', 'danger')
            return render_template("login.html")

        # Ensure username exists and password is correct
        if rows[0][1] != request.form['username'] or not check_password_hash(rows[0][2], request.form['password']):
            # error = "invalid username and/or password."
            flash('Invalid username and/or password', 'danger')
            return render_template("login.html")

        # Remember which user has logged in
        # rows[0][1] represents the second element of the tuple
        session["user_id"] = rows[0][1]

        # VERY IMPORTANT, WE NEED TO KNOW WHO THE CURRENT USER IS
        session['username'] = request.form["username"]

        # Redirect user to home page, after the user has logged in
        session['logged_in'] = True
        flash('You were successfully logged in!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", title="Login")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('home'))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "GET":
        return render_template("register.html", title="Register")  # Display form that lets user register for an account

    # POST
    else:
        username = request.form.get("username")

        db.execute("SELECT username FROM users")
        handler = db.fetchall()

        # Check if the username entered matches a another user in the database. If it does, they have to pick a new username
        for user in handler:
            if username in user:
                flash("Username has been taken. Please choose a different one.", 'danger')
                return render_template("register.html")

        # Make sure the password has a number and a symbol
        req_chars = ['@', '#', '$', '%']
        req_nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

        pass_chars = []
        pass_nums = []

        password = request.form.get("password")

        for p in password:
            if p in req_chars:
                pass_chars.append(p)
            elif p in req_nums:
                pass_nums.append(p)

        if not pass_chars or not pass_nums:
            flash('Your password must contain at least one number (0-9) and at least one special symbol (@#$%)',
                  'warning')
            return render_template('register.html')

        confirmation = request.form.get("confirmPswrd")
        if not confirmation:
            flash('Please confirm your password.', 'danger')
            return render_template("register.html")

        # If passwords don't match
        if password != confirmation:
            flash('Passwords do not match!', 'danger')
            return render_template("register.html")

        # Hash password for security
        password_hash = generate_password_hash(password)

        # INSERT this information every time a new user registers
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()

        # Return to home page after successful registration
        flash("You have successfully registered!", 'success')
        return redirect(url_for('home'))

@app.route("/reset", methods=['GET', 'POST'])
def reset():
    """ Password reset for username """

    if request.method == 'GET':
        return render_template("reset.html")

    else:
        username = request.form.get('username')
        if not username:
            flash('Please provide a username', 'danger')
            return render_template('reset.html')

        user_list = []

        df = pd.read_sql_query("SELECT username FROM users", conn)
        for user in df['username']:
            user_list.append(user)

        if username not in user_list:
            flash("That username is not found", 'danger')
            return render_template('reset.html')

        req_chars = ['@', '#', '$', '%']
        req_nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

        pass_chars = []
        pass_nums = []

        newPswrd = request.form.get('newPswrd')
        if not newPswrd:
            flash('Please provide a new password', 'danger')
            return render_template('reset.html')

        for p in newPswrd:
            if p in req_chars:
                pass_chars.append(p)
            elif p in req_nums:
                pass_nums.append(p)

        if not pass_chars or not pass_nums:
            flash('Your password must contain at least one number (0-9) and at least one special symbol (@#$%)',
                  'warning')
            return render_template('register.html')

        confirmPswrd = request.form.get('confirmPswrd')
        if not confirmPswrd:
            flash('Please confirm your password', 'danger')
            return render_template('reset.html')

        if newPswrd != confirmPswrd:
            flash('Passwords do not match!', 'danger')
            return render_template('reset.html')

        # Hash password for security
        newPswrd_hash = generate_password_hash(newPswrd)

        # UPDATE this information every time a new user registers
        db.execute("UPDATE users SET hash = (?) WHERE username = (?)", (newPswrd_hash, username))
        conn.commit()

        flash('Password has been successfully reset!', 'success')
        return redirect(url_for('login'))

@app.route("/study", methods=['GET', 'POST'])
@login_required
def study():
    """ User fills out study form """
    if request.method == 'GET':
        return render_template("study.html", title="Study")

    else:
        course = request.form.get('class')
        if not course:
            error = 'Please do not leave the Class field blank.'
            return render_template('study.html', error=error)

        topic = request.form.get('topic')
        if not topic:
            error = 'Please do not leave the Topic field blank.'
            return render_template('study.html', error=error)

        duration = request.form.get('time')
        if not duration:
            error = 'Please do not leave the Length field blank.'
            return render_template('study.html', error=error)

        # Assign value of forms as session variables
        session['class'] = request.form["class"]
        session['topic'] = request.form["topic"]
        session['duration'] = request.form["time"]
        session['semester'] = request.form['semester']

        return redirect(url_for('timer'))


@app.route("/timer", methods=['GET', 'POST'])
@login_required
def timer():
    """ INSERT current session details into the database, direct to timer page """

    # Grab those session variables we assigned earlier
    course = session['class']
    topic = session['topic']
    duration = session['duration']
    user = session['username']
    semester = session['semester']

    today = datetime.now()
    today_string = today.strftime("%m/%d/%Y %H:%M")

    if request.method == 'GET':
        return render_template('timer.html', course=course, topic=topic, duration=duration, today=today_string, semester=semester, title="Study")

    else:
        # Get the confidence level of the user as a session variable
        session['confidence'] = request.form['confidence']
        confidence = session['confidence']

        # Insert that confidence information into the database
        db.execute("""INSERT INTO track (Username, Class, Topic, Duration, Session, Confidence, Semester)
                               VALUES(?,?,?,?,DATETIME('now','localtime'),?,?)""", (user, course, topic, duration, confidence, semester))
        conn.commit()

        # Redirect the user to the page where progress of each study session is tracked
        return redirect(url_for('track'))

@app.route("/track")
@login_required
def track():
    """ Create the page where the progress graph is displayed """

    # Try to render a graph in 'track.html'
    try:
        user = session['username']
        course = session['class']
        topic = session['topic']

        db.execute("""SELECT * FROM track WHERE Username = (?) and Class = (?) and Topic = (?)""",
                   (user, course, topic))
        query = db.fetchall()

        x = []
        y = []
        course = []
        topic = []

        for ele in query:
            x.append(ele[4])
            y.append(ele[5])
            course.append(ele[1])
            topic.append(ele[2])

        course_uni = np.array(course)
        topic_uni = np.array(topic)

        print(x)
        print(y)
        print(course)
        print(topic)

        return render_template('track.html', x=x, y=y, course_uni=np.unique(course_uni),
                               topic_uni=np.unique(topic_uni), user=user)
    # If no current session exists, then flash a message
    except:
        return render_template('flash.html', message="You are not currently studying. Click on the 'Study' tab above to start active recalling!")


@app.route("/plot", methods=['GET', 'POST'])
@login_required
def plot():
    """ Plot graphs of confidence levels for all classes and topics as well as total study times """

    user = session['username']

    # Query database for all results for the current user, put in Pandas dataframe
    df = pd.read_sql_query("SELECT * FROM track WHERE Username = (?)", conn, params={user})

    # If there are no results, then flash a message
    if df.empty:
        return render_template('flash.html',
                               message="It looks like you haven't actively recalled at least once, so there are no "
                                        "results! Click the 'Study' tab above to start actively recalling!")

    # If the dataframe is not empty, there are historical sessions
    elif not df.empty:

        # Once the "Overall Results" tab has been clicked, display the semester selector
        if request.method == "GET":
            return render_template("plot.html", df=df)

        # Once a semester is chosen, and the user clicks "Go", display the plots
        elif request.method == "POST":

            semester = request.form.get('semester')
            df_options = pd.read_sql_query("SELECT * FROM track WHERE Username = (?) and Semester = (?)", conn,
                                           params=[user, semester])

            newdf = df_options.drop(columns=['Username', 'Session', 'Duration'])

            # Create two graphs, one for the overall study results, another for total study duration
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
            # Add spacing between graphs
            plt.subplots_adjust(left=None, bottom=None, right=None, top=None,
                                wspace=None, hspace=None)
            sbn.swarmplot(x='Class', y='Confidence', hue='Topic', data=newdf, size=10, ax=ax1)

            # Anchor a 3 column legend outside of the plot
            ax1.legend(ncol=3, loc='center left', bbox_to_anchor=(1, 0.5))

            # Set the title and y limits for graph 1
            ax1.set_title('Confidence of each topic by class')
            ax1.set_ylim(0, 12)
            plt.xticks(size=10)

            # Graph two: group class and topic by sum of study minutes
            df_dur = df_options.drop(columns=['Username', 'Session'])
            df_dur = df_dur.groupby(['Class', 'Topic']).Duration.sum()
            df_dur = df_dur.reset_index()

            sbn.swarmplot(x='Class', y='Duration', hue='Topic', data=df_dur, size=10, ax=ax2)
            ax2.legend_.remove()
            plt.title('Total Study Duration in Hours of Each Topic by Class')
            ax2.set_ylim(0, df_dur['Duration'].max() + 5, auto=True)
            plt.ylabel("Duration (minutes)")

            # Save the figure to the following path as a png and make it fit on the page
            plt.savefig('static/image_output.png', format='png', bbox_inches='tight')

            # Grab the full directory of the photo
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'image_output.png')

            # Plot the dataframes and the saved plot into the plot.html template
            return render_template("plot.html", image=full_filename, df_options=df_options, df=df)


if __name__ == "__main__":
    app.run(debug=True)