from MySQLdb import IntegrityError
from werkzeug.utils import secure_filename
import os

from flask import Flask, send_file 
from flask_mysqldb import MySQL
from flask import render_template, request, redirect, url_for, jsonify, make_response, abort, flash
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from models import UserProfile
import datetime
from collections import defaultdict
import math



app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'school'
app.config['JSON_SORT_KEYS'] = False
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
login_manager = LoginManager()
login_manager.init_app(app)
mysql = MySQL(app)

  
import sys
###
# Routing for your application.
###


def get_all(who):
    try:
        cur = mysql.connection.cursor()
        cur.execute("select * from {};".format(who))
        dataset =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Database error getting {} '.format(who), 400)
    return dataset


def updateUserRegister_ID(who, user_id, unique_id):
    try:
        cur = mysql.connection.cursor()
        if who == "Admin":
            statement = "UPDATE {} SET User_ID = %s WHERE AdminID = %s AND User_ID IS NULL".format(who)
        if who == "Lecturer":
            statement = "UPDATE {} SET User_ID = %s WHERE l_id = %s AND User_ID IS NULL".format(who)
        elif who == "Student":
            statement = "UPDATE {} SET User_ID = %s WHERE StudentID = %s AND User_ID IS NULL".format(who)
        cur.execute(statement, (user_id, unique_id))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("Error:", e)
        flash('Database update error', 'error')




def get_user_from_database(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT a.User_ID, a.Type, s.FirstName AS s_first, s.LastName AS s_last, \
                     adm.FirstName AS adm_first, adm.LastName AS adm_last, \
                     l.FirstName AS l_first, l.LastName AS l_last, \
                     a.Password \
                     FROM Account a \
                     LEFT JOIN Student s ON a.User_ID = s.User_ID \
                     LEFT JOIN Admin adm ON a.User_ID = adm.User_ID \
                     LEFT JOIN Lecturer l ON a.User_ID = l.User_ID \
                     WHERE a.User_ID = %s;", (user_id,))
        user_data = cur.fetchone()
        cur.close()
    except Exception as e:
        print(e)
        return None
    
    if user_data:
        user_type = user_data[1]
        if user_type == 'Student':
            firstname = user_data[2]
            lastname = user_data[3]
        elif user_type == 'Admin':
            firstname = user_data[4]
            lastname = user_data[5]
        elif user_type == 'Lecturer':
            firstname = user_data[6]
            lastname = user_data[7]
        else:
            return None
        
        # Return UserProfile object
        return UserProfile(user_data[0], firstname, lastname, user_type)
    else:
        return None



@login_manager.user_loader
def load_user(user_id):
    # Fetch user from the database based on user_id
    user_data = get_user_from_database(user_id)
    if user_data:
        # Create and return a User instance using the fetched user data
        return UserProfile(user_data.id, user_data.firstname, user_data.lastname, user_data.type)
    else:
        return None  # Return None if user not found



@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login'))  # Redirect unauthorized users to the login page



@app.route('/')
def home():
    if current_user.is_authenticated:
        # Access user information
        user_type = current_user.type
        # Redirect based on user type
        if user_type == "Admin":
            return redirect(url_for('admin_home'))
        elif user_type == "Lecturer":
            return redirect(url_for('lecturer_home'))
        elif user_type == "Student":
            return redirect(url_for('student_home'))
    return redirect(url_for('login'))




@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            userID = request.form.get('UserID')
            password = request.form.get('Password')
            if not userID or not password:
                return make_response("UserID and password needed.")
        except Exception:
            error = "Incorrect form data, please try again"
            flash(error, 'error')
            return redirect(url_for('login'))

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT User_ID, password, Type FROM account WHERE User_ID = %s;", (userID,))
            account = cur.fetchone()
            cur.close()
        except Exception as e:
            error = "Database error getting accounts"
            flash(error, 'error')
            return redirect(url_for('login'))

        if account is None:
            error = "Incorrect credentials, please try again"
            flash(error, 'error')
            return redirect(url_for('login'))

        user_id, stored_password, user_type = account

        # Perform a case-sensitive comparison for passwords
        if password != stored_password:
            error = "Incorrect credentials, please try again"
            flash(error, 'error')
            return redirect(url_for('login'))

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT FirstName, LastName FROM {} WHERE User_ID = %s;".format(user_type), (user_id,))
            user_details = cur.fetchone()
            cur.close()
        except Exception as e:
            error = "Database error retrieving user details"
            flash(error, 'error')
            return redirect(url_for('login'))

        if user_details is None:
            error = "User details not found, please try again"
            flash(error, 'error')
            return redirect(url_for('login'))

        User = UserProfile(user_id, user_details[0], user_details[1], user_type)
        login_user(User)
        return redirect(url_for('home'))
    return render_template('login.html')



@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()  # Clear the user's session
    return redirect(url_for('login'))


@app.route('/admin-home')
@login_required
def admin_home():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)  # Only admins can access the admin home page
        if current_user.type == "Admin":
            return render_template('admin-home.html', admin_name=current_user.firstname+" "+current_user.lastname, user_type=current_user.type)



def getLecID(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT l_id FROM Lecturer WHERE User_ID = %s;", (user_id,))
        lecids = cur.fetchall()
        cur.close()
        return lecids
    except Exception as e:
        print("Error retrieving lecturer ID:", e)
        return []
    


def fetch_lecturer_courses(lecturer_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT Course.CourseID, Course.Title
            FROM Course
            INNER JOIN assigned ON Course.CourseID = assigned.c_id
            WHERE assigned.l_id = %s;
        """, (lecturer_id,))
        courses = cur.fetchall()
        cur.close()
        return courses
    except Exception as e:
        print("Error fetching lecturer courses:", e)
        return []




@app.route('/lecturer-home')
@login_required
def lecturer_home():
    if current_user.is_authenticated:
        if current_user.type != "Lecturer":
            return abort(403)  # Only lecturers can access the lecturer home page
        
        if current_user.type == "Lecturer":
            # Fetch lecturer's ID
            lecids = getLecID(current_user.id)
            if not lecids:
                return make_response('Error retrieving lecturer ID', 400)
            
            # Fetch lecturer's courses using the lecturer's ID
            lecturer_id = lecids[0][0]
            courses = fetch_lecturer_courses(lecturer_id)
            
            # Format course data into a list of dictionaries
            formatted_courses = [{'CourseID': course[0], 'Title': course[1]} for course in courses]

            return render_template('lecturer-home.html', lecturer_name=current_user.firstname+" "+current_user.lastname, courses=formatted_courses, user_type=current_user.type)





def fetch_student_courses(user_id):
    try:
        cur = mysql.connection.cursor()
        # Fetch the student ID corresponding to the user ID
        cur.execute("""
            SELECT StudentID
            FROM Student
            WHERE User_ID = %s;
        """, (user_id,))
        student_id = cur.fetchone()[0]

        # Fetch the courses enrolled by the student
        cur.execute("""
            SELECT c.CourseID, c.Title
            FROM Course c
            INNER JOIN StudentCourseReg scr ON c.CourseID = scr.c_id
            WHERE scr.StudentID = %s;
        """, (student_id,))
        courses = cur.fetchall()
        cur.close()
        return courses
    except Exception as e:
        print("Error fetching student courses:", e)
        return []



@app.route('/student-home')
@login_required
def student_home():
    if current_user.is_authenticated:
        if current_user.type != "Student":
            return abort(403)  # Only students can access the student home page
        
            # Fetch student's courses from the database using the student's user ID
        if current_user.type == "Student":

            courses = fetch_student_courses(current_user.id)
            # Format course data into a list of dictionaries
            formatted_courses = [{'CourseID': course[0], 'Title': course[1]} for course in courses]

            return render_template('student-home.html', student_name=current_user.firstname+" "+current_user.lastname, courses=formatted_courses, user_type=current_user.type)


@app.route('/register', methods=['GET', 'POST'])
def Register():
    if request.method == 'POST':
        available = ["Student", "Lecturer", "Admin"]
        try:
            User_ID = request.form.get('User-ID')
            password = request.form.get('ConfirmPassword')
            type = request.form.get('TypeOfAccount')
            yourid = request.form.get('ID')
            if not User_ID or not password or not type or not yourid:
                return make_response("Please enter all the information required.")
        except Exception:
            flash("Incorrect form data", 'error')
            return redirect(url_for('Register'))
        
        if type not in available:
            flash("Invalid account type", 'error')
            return redirect(url_for('Register'))
        
        dataset = get_all(type)

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM account;")
            accounts = cur.fetchall()
            cur.close()
        except Exception as e:
            flash("Database error getting accounts", 'error')
            return redirect(url_for('Register'))
        
        try:
            cur = mysql.connection.cursor()
            if type == "Admin":
                cur.execute("SELECT User_ID FROM Admin WHERE AdminID = %s AND User_ID IS NOT NULL", (yourid,))
            elif type == "Lecturer":
                cur.execute("SELECT User_ID FROM Lecturer WHERE l_id = %s AND User_ID IS NOT NULL", (yourid,))
            elif type == "Student":
                cur.execute("SELECT User_ID FROM Student WHERE StudentID = %s AND User_ID IS NOT NULL", (yourid,))
            existing_user_id = cur.fetchone()
            cur.close()
        except Exception as e:
            flash("Database error getting existing User ID", 'error')
            return redirect(url_for('Register'))

        if existing_user_id:
            flash("Already registered", 'error')
            return redirect(url_for('Register'))



        # Check if the provided ID exists in the respective table
        if yourid not in [id for id, _, _, _, _ in dataset]:
            flash("Information not found, please recheck your {} ID".format(type), 'error')
            return redirect(url_for('Register'))

        for userid, _, _ in accounts:
            if userid == User_ID:
                flash("User ID already taken", 'error')
                return redirect(url_for('Register'))
            
        try:
            cur = mysql.connection.cursor()
            statement = "INSERT INTO account VALUES (%s, %s, %s)"
            cur.execute(statement, (User_ID, password, type))
            mysql.connection.commit()

            statement = "INSERT INTO Register VALUES (%s, %s, %s)"
            cur.execute(statement, (User_ID, yourid, datetime.datetime.today().strftime('%Y-%m-%d')))
            mysql.connection.commit()
            
            cur.close()
        except Exception as e:
            flash("Database error", 'error')
            return redirect(url_for('Register'))
        
        # Update User_ID in respective table
        updateUserRegister_ID(type, User_ID, yourid) 
        flash("Registered Successfully", 'success')
        return redirect(url_for('Register'))

    return render_template('register.html')



@app.route('/create-course', methods=['POST'])
@login_required
def createCourse():
    if current_user.is_authenticated:

        if current_user.type != "Admin":
            return abort(403)  # Only admins can access the admin home page

        if request.method == 'POST':
            try:
                code = request.form.get('course_code')
                title = request.form.get('title')
                credit = request.form.get('credits')
                if not code or not title or not credit:
                    return make_response("Please enter all the information required.")
            except Exception:
                flash('Incorrect form data', 'error')

            try:
                cur = mysql.connection.cursor()
                statement = "INSERT INTO course VALUES('{}','{}',{})".format(code, title, credit)
                cur.execute(statement)
                mysql.connection.commit()
                cur.close()
                flash('Course created successfully', 'create-course-success')  # Use a different category for create course success
            except IntegrityError:
                flash('Course already exists', 'create-course-error') 
            except Exception as e:
                flash('Database course creation error', 'create-course-error') 

            try:
                cur = mysql.connection.cursor()
                statement = "INSERT INTO Calendar(c_id) VALUES('{}')".format(code)
                cur.execute(statement)
                mysql.connection.commit()
                cur.close()
            except Exception as e:
                flash(str(e), 'create-course-error') 
            
            # Redirect to admin home page after handling the form submission
            return redirect(url_for('admin_home'))

        # If method is GET, render the create course form
        return render_template('admin-home.html')




@app.route('/all-courses', methods=['GET'])
@login_required
def get_all_courses():
    if current_user.is_authenticated:
        courses = getAllCourses()
        formatted_courses = [{'Course Code': course[0], 'Title': course[1], 'Credits': course[2]} for course in courses]
        num_courses = len(formatted_courses)
        return render_template('all-courses.html', courses=formatted_courses, num_courses=num_courses, user_type=current_user.type)


def getAllstudents(offset=0, limit=None):
    try:
        cur = mysql.connection.cursor()
        # Add LIMIT and OFFSET clauses to your SQL query
        cur.execute("SELECT * FROM Student, Account WHERE Student.User_ID = Account.User_ID LIMIT %s OFFSET %s;", (limit, offset))
        students = cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    return students



def getTotalStudentCount():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM Student, Account WHERE Student.User_ID = Account.User_ID")
        count = cur.fetchone()[0]
        cur.close()
    except Exception as e:
        return 0
    return count



@app.route('/all-students', methods=['GET'])
@login_required
def all_students():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)  # Only admins can access the admin home page
        
        page = request.args.get('page', 1, type=int)  # Get the page parameter, default to 1
        students_per_page = 5000  # Define the number of students to display per page
        
        offset = (page - 1) * students_per_page  # Calculate the offset for pagination
        
        # Fetch students for the current page
        students = getAllstudents(offset=offset, limit=students_per_page)
        
        # Get the total number of students
        total_students = getTotalStudentCount()
        
        # Calculate the total number of pages
        num_pages = math.ceil(total_students / students_per_page)
        
        # Pass necessary variables to the template
        num_stud = {"Total": total_students}
        formatted_students = [{'StudentID': student[0], 'FirstName': student[1], 'MiddleName': student[2], 'LastName': student[3]} for student in students]

        return render_template('all-students.html', students=formatted_students, num_stud=num_stud, num_pages=num_pages, current_page=page, user_type=current_user.type)




@app.route("/search", methods=['GET'])
def search_students():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)  # Only admins can access the admin home page
        
        search_query = request.args.get("query", "")
        
        # Split the search query into individual terms
        search_terms = search_query.split()

        # Initialize SQL query and parameters
        sql_query = """
        SELECT * FROM Student
        WHERE 1=1
        """
        params = []

        # Add conditions for searching by StudentID, FirstName, MiddleName, and LastName
        for term in search_terms:
            sql_query += " AND (StudentID LIKE %s OR FirstName = %s OR LastName = %s)"
            params.extend(["%" + term + "%", term, term])


        # Execute SQL query
        cur = mysql.connection.cursor()
        cur.execute(sql_query, params)
        students = cur.fetchall()
        cur.close()

        # Return search results as JSON
        return jsonify([{'StudentID': student[0], 'FirstName': student[1], 'MiddleName': student[2], 'LastName': student[3]} for student in students])


@app.route('/all-lecturers')
def all_lecturers():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)  # Only admins can access the admin home page
            
        lecturers = getAllLecturers()  # Call your function to lecturer student data
        formatted_lecturers = [{'LecturerID': lecturer[0], 'FirstName': lecturer[1], 'MiddleName': lecturer[2], 'LastName': lecturer[3]} for lecturer in lecturers]
        total_lecturers = len(formatted_lecturers)
        num_lec = {"Total": total_lecturers}
        return render_template('all-lecturers.html', lecturers=formatted_lecturers, num_lec=num_lec, user_type=current_user.type)




def getAllLecturers():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Lecturer, Account WHERE Lecturer.User_ID = Account.User_ID;")
        lecturers = cur.fetchall()
        cur.close()
    except Exception as e:
        # Handle the error appropriately, e.g., logging
        print('Error retrieving lecturers:', e)
        return None
    return lecturers


@app.route('/assignLecturer', methods=['POST'])
@login_required
def assignLecturer():
    if current_user.type != "Admin":
        return abort(403)  # Only admins can access the admin home page

    if request.method == 'POST':
        try:
            lecid = request.form.get('lecturer_id')
            cc = request.form.get('course_code')
            if not cc or not lecid:
                return make_response("Please enter a LecturerID and Course Code")
            # Check if the lecturer exists
            if not isLecturerExists(lecid):
                flash('Lecturer not found', 'assign-lecturer-error')
                return redirect(url_for('admin_home'))

            # Check if the course exists
            if not isCourseExists(cc):
                flash('Course not found', 'assign-lecturer-error')
                return redirect(url_for('admin_home'))

            # Check if the lecturer is already assigned to five courses
            if count_lecturer_courses(lecid) == 5:
                flash('Lecturer is already assigned to the maximum number of courses', 'assign-lecturer-error')
                return redirect(url_for('admin_home'))

            # Assign the lecturer to the course
            try:
                cur = mysql.connection.cursor()
                statement = "INSERT INTO assigned VALUES ('{}','{}')".format(cc, lecid)
                cur.execute(statement)
                mysql.connection.commit()
                cur.close()
                flash('Lecturer assigned to course successfully','assign-lecturer-success')
            except Exception as e:
                flash('A lecturer is already assigned to this course', 'assign-lecturer-error')
        except Exception as e:
            flash('An error occurred while assigning lecturer to course', 'assign-lecturer-error')

    return redirect(url_for('admin_home'))

def isLecturerExists(lecid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT l_id FROM Lecturer, Account WHERE Lecturer.User_ID = Account.User_ID AND Lecturer.l_id = %s", (lecid,))
        result = cur.fetchone()
        cur.close()
        return result is not None
    except Exception as e:
        return False


def isCourseExists(cc):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT CourseID FROM course WHERE CourseID = %s", (cc,))
        result = cur.fetchone()
        cur.close()
        return result is not None
    except Exception as e:
        return False

def isLecturerAssignedToCourse(cc, lecid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM assigned WHERE c_id = %s AND lecturer_id = %s", (cc, lecid))
        result = cur.fetchone()
        cur.close()
        return result is not None
    except Exception as e:
        return False


def count_lecturer_courses(lecturer_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM assigned WHERE l_id = %s", (lecturer_id,))
        count = cur.fetchone()[0]
        cur.close()
        return count
    except Exception as e:
        print("Error counting lecturer courses:", e)
        return 0



def get_forums(ccode):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT forum_id, title, description, datecreated FROM forum WHERE c_id = %s", (ccode,))
        forums = [{'forum_id': row[0], 'title': row[1], 'description': row[2], 'date_created': row[3]} for row in cur.fetchall()]
        return forums
    except Exception as e:
        print("Error fetching forum links:", e)
        return []



def get_course_details(ccode):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Course WHERE CourseID = %s", (ccode,))
        course_data = cur.fetchone()
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT FirstName, MiddleName, LastName FROM Lecturer, assigned
            WHERE c_id = %s AND Lecturer.l_id = assigned.l_id;
            """, (ccode,))
            lecs = cur.fetchall()
            cur.close()
            lecturers = [{"First Name": f, "Middle Name": m, "Last Name": l} for f, m, l in lecs]
        except Exception as e:
            return make_response('Error retrieving lecturers', 400)
        
        # Count the number of content items for the course
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) FROM contentitems WHERE cont_id IN (SELECT cont_id FROM content WHERE c_id = %s)", (ccode,))
            content_count = cur.fetchone()[0]
            cur.close()
        except Exception as e:
            return make_response('Error retrieving content count', 400)

        total_members = count_student_members(ccode) + len(lecturers)
        if course_data:
            course_details = {
                'Course Code': course_data[0],
                'Title': course_data[1],
                'Number of Forums': len(get_forums(ccode)),
                'Number of Events': len(get_events(ccode)),
                'Lecturer': get_lecturer_name(ccode),
                'Total Members': total_members,
                'Number of Content': content_count
            }
            return course_details
        else:
            return None
    except Exception as e:
        print("Error fetching course details:", e)
        return None



@app.route('/course_detail/<ccode>', methods=['GET'])
@login_required
def course_detail(ccode):
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403) 
        course = get_course_details(ccode)
        if course:
            return render_template('course-detail.html', course=course, user_type=current_user.type)
        else:
            return make_response("Course not found", 404)


def get_lecturer_name(ccode):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT FirstName, MiddleName, LastName 
            FROM Lecturer 
            JOIN assigned ON Lecturer.l_id = assigned.l_id
            WHERE assigned.c_id = %s
        """, (ccode,))
        lecturer_data = cur.fetchone()
        if lecturer_data:
            lecturer_name = " ".join(filter(None, lecturer_data))
            return lecturer_name
        else:
            return "N/A"
    except Exception as e:
        print("Error fetching lecturer name:", e)
        return "N/A"
    


def count_student_members(ccode):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM StudentCourseReg WHERE c_id = %s", (ccode,))
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        print("Error counting total members:", e)
        return 0



def get_events(ccode):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT EventName, DueDate 
            FROM calendarev 
            WHERE CalID IN (SELECT CalID FROM Calendar WHERE c_id = %s)
        """, (ccode,))
        events = cur.fetchall()
        event_list = [{"Name": event[0], "Due Date": event[1]} for event in events]
        return event_list
    except Exception as e:
        print("Error retrieving events:", e)
        return []
    



def get_student_name(sid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT FirstName, LastName FROM Student WHERE StudentID = %s", (sid,))
        student_info = cur.fetchone()
        cur.close()
        
        if student_info:
            first_name, last_name = student_info
            # Concatenate the first and last name
            full_name = ' '.join(part for part in [first_name, last_name] if part)
            return full_name
        else:
            return None
    except Exception as e:
        print("Error fetching student name:", e)
        return None


def get_student_courses(sid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT c.CourseID, c.Title, c.Credits
            FROM Course c
            JOIN StudentCourseReg scr ON c.CourseID = scr.c_id
            WHERE scr.StudentID = %s;
        """, (sid,))
        courses = cur.fetchall()
        cur.close()
        
        return courses
    except Exception as e:
        print("Error fetching student courses:", e)
        return []


@app.route('/student-detail/<sid>', methods=['GET'])
def student_detail(sid):
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)        
        student_name = get_student_name(sid)
        student_courses = get_student_courses(sid)
        num_courses = len(student_courses)
        total_credits = sum(course[2] for course in student_courses)
        return render_template('student-detail.html', 
                            student_name=student_name, 
                            num_courses=num_courses, 
                            courses=student_courses, 
                            total_credits=total_credits,
                            user_type=current_user.type)



def lec_name(lid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT FirstName, LastName FROM Lecturer WHERE l_id = %s", (lid,))
        lecturer_info = cur.fetchone()
        cur.close()
        
        if lecturer_info:
            first_name, last_name = lecturer_info
            # Concatenate the first, middle, and last name
            full_name = ' '.join(part for part in [first_name, last_name] if part)
            return full_name
        else:
            return None
    except Exception as e:
        print("Error fetching lecturer name:", e)
        return None


def get_lecturer_courses(lid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT c.CourseID, c.Title
            FROM Course c
            JOIN assigned a ON c.CourseID = a.c_id
            WHERE a.l_id = %s;
        """, (lid,))
        courses = cur.fetchall()
        cur.close()
        
        return courses
    except Exception as e:
        print("Error fetching lecturer courses:", e)
        return []



@app.route('/lecturer-detail/<lid>', methods=['GET'])
def lecturer_detail(lid):
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)

        lecturer_name = lec_name(lid)
        lecturer_courses = get_lecturer_courses(lid)
        num_courses = len(lecturer_courses)
        return render_template('lecturer-detail.html', lecturer_name=lecturer_name, num_courses=num_courses, courses=lecturer_courses, user_type=current_user.type)




@app.route('/register-student', methods=['GET', 'POST'])
@login_required
def register_student():
    if current_user.is_authenticated():
        if current_user.type == "Student":
            if request.method == 'POST':
                try:
                    course_code = request.form.get('course_code')
                    if not course_code:
                        error = "Please enter a course code."
                        flash(error, 'error')
                        return redirect(url_for('register_student'))
                    
                    courses = getAllCourses()
                    course_exists = any(course[0] == course_code for course in courses)
                    if not course_exists:
                        error = "Course does not exist."
                        flash(error, 'error')
                        return redirect(url_for('register_student'))

                    student_courses = fetch_student_courses(current_user.id)

                    max_courses = 6
                    if len(student_courses) == max_courses:
                        error = "You have already registered for the maximum number of courses."
                        flash(error, 'error')
                        return redirect(url_for('register_student'))

                    for code, _ in student_courses:
                        if code == course_code:
                            error = "You are already registered for this course."
                            flash(error, 'error')
                            return redirect(url_for('register_student'))

                    student_id = studentid_by_userid(current_user.id)

                    # Register student for the course
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        INSERT INTO StudentCourseReg(c_id, StudentID)
                        VALUES (%s, %s)
                    """, (course_code, student_id))
                    mysql.connection.commit()
                    cur.close()

                    flash("Successfully registered for the course.", 'success')
                    return redirect(url_for('register_student'))
                except Exception as e:
                    error = "An error occurred: " + str(e)
                    flash(error, 'error')
                    return redirect(url_for('register_student'))
            if request.method == 'GET':
                courses = getAllCourses()
                formatted_courses = [{'Course Code': course[0], 'Title': course[1], 'Credits': course[2]} for course in courses]
                num_courses = len(formatted_courses)
                return render_template('course-registration.html', courses=formatted_courses, num_courses=num_courses, user_type=current_user.type)
        else:
            return make_response("User must be a student", 401)



@app.route('/retrieve-members/<code>', methods=['GET'])
@login_required
def retrieve_members(code):
    if current_user.is_authenticated:
        authorized = None

        # Check authorization
        if current_user.type == "Admin":
            authorized = True
        elif current_user.type == "Student" or current_user.type == "Lecturer":
            authorized = check_course_authorization(code)

        if authorized:  # If authorized or admin
            lecturers = []
            students = []
            course_name = ""

            # Check if the course exists
            if not isCourseExists(code):
                return abort(404, "Course not found")

            try:
                # Retrieve course name
                cur = mysql.connection.cursor()
                cur.execute("SELECT Title FROM Course WHERE CourseID = %s", (code,))
                course_name = cur.fetchone()[0]
                cur.close()

                # Retrieve course members
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT Lecturer.FirstName, Lecturer.MiddleName, Lecturer.LastName
                    FROM Lecturer
                    JOIN assigned ON Lecturer.l_id = assigned.l_id
                    WHERE assigned.c_id = %s
                """, (code,))
                lecs = cur.fetchall()
                lecturers = [{"First Name": f, "Middle Name": m, "Last Name": l} for f, m, l in lecs]
                cur.close()

                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT Student.FirstName, Student.MiddleName, Student.LastName
                    FROM Student
                    JOIN StudentCourseReg ON Student.StudentID = StudentCourseReg.StudentID
                    WHERE StudentCourseReg.c_id = %s
                """, (code,))
                studs = cur.fetchall()
                students = [{"First Name": f, "Middle Name": m, "Last Name": l} for f, m, l in studs]
                cur.close()

                total_members = len(lecturers) + len(students)
                data = {"course_name": course_name, "lecturers": lecturers, "students": students, "total_members": total_members}
                return render_template('members.html', data=data, ccode=code, user_type=current_user.type)

            except Exception as e:
                print("Error:", e)  # Print the specific exception message
                return make_response('Error retrieving course members', 400)

        else:
            return make_response("User is not authorized to view this course", 401)





@app.route('/create-event/<cc>', methods=['POST'])
@login_required
def create_event(cc):
    if current_user.is_authenticated:
        if current_user.type == "Lecturer":
            try:
                title = request.form.get('title')
                due_date = request.form.get('due_date')
                # Split the date and handle date format errors
                if not title or not due_date:
                    return make_response("Title and due date are needed")
                try:
                    year, month, day = map(int, due_date.split('-'))  # Date format is yyyy-mm-dd
                    today = datetime.date(year, month, day)
                except ValueError:
                    flash("Please enter a valid date in yyyy-mm-dd format", 'error')
                    return redirect(url_for('course_container', ccode=cc))
            except Exception as e:
                flash("Event title and date needed", 'error')
                return redirect(url_for('course_container', ccode=cc))
            if check_course_authorization(cc):
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("select CalID FROM Calendar WHERE c_id = %s", (cc,))
                    callids =  cur.fetchall()
                    cur.close()
                except Exception as e:
                    flash("Error retrieving Calendar", 'error')
                    return redirect(url_for('course_container', ccode=cc))
                if len(callids) == 0:
                    flash("Incorrect Course Code", 'error')
                    return redirect(url_for('course_container', ccode=cc))
                
                # Check if event name already exists in the calendar
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("SELECT EventName FROM Calendarev WHERE CalID = %s", (callids[0][0],))
                    existing_events = cur.fetchall()
                    cur.close()
                    existing_event_names = [event[0] for event in existing_events]
                    if title in existing_event_names:
                        flash("There is already an event with this title", 'error')
                        return redirect(url_for('course_container', ccode=cc))
                except Exception as e:
                    flash("Error checking existing events", 'error')
                    return redirect(url_for('course_container', ccode=cc))
                
                # Add the event to the calendar
                try:
                    cur = mysql.connection.cursor()
                    statement = "INSERT INTO Calendarev VALUES (%s, %s, %s)"
                    cur.execute(statement, (callids[0][0], title, today.strftime("%A, %d %b %Y")))
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    flash("Error creating Calendarev", 'error')
                    return redirect(url_for('course_container', ccode=cc))

                flash("Event added to calendar successfully", 'success')
                return redirect(url_for('course_container', ccode=cc))
        flash("Must be a lecturer!", 'error')
        return redirect(url_for('course_container', ccode=cc))


def getAllStudentIDs():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT Student.StudentID FROM Student INNER JOIN Account ON Student.User_ID = Account.User_ID;")
        student_ids = [row[0] for row in cur.fetchall()]
        cur.close()
    except Exception as e:
        return make_response('Error retrieving student IDs', 400)
    return student_ids


def is_student_registered(student_id):
    all_student_ids = getAllStudentIDs()
    return student_id in all_student_ids



@app.route('/events/<ccode>', methods=['GET'])
@login_required
def events(ccode):
    if current_user.is_authenticated():
        if current_user.type == "Admin":
            # Admins have access, so no need to check further
            pass
        else:
            authorization_result = check_course_authorization(ccode)
            if not authorization_result:
                return make_response("User is not authorized to view this course", 401)
        events = get_events(ccode)
        try:
                # Retrieve course name
                cur = mysql.connection.cursor()
                cur.execute("SELECT Title FROM Course WHERE CourseID = %s", (ccode,))
                course_name = cur.fetchone()[0]
                cur.close()
        except Exception as e:
                print("Error:", e)  # Print the specific exception message
                return make_response('Error retrieving course members', 400)
        return render_template('events.html', events=events, course_name=course_name, user_type=current_user.type)



@app.route('/retrieve-sevent', methods=['POST'])
@login_required
def retrieve_sevent():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403) 
        
        format = []
        try:
            student_id = request.form.get('student_id')
            selected_date_str = request.form.get('selected_date')

            if not student_id or not selected_date_str:
                flash('Please provide both student ID and selected date.', 'search-student-event-error')
                return redirect(url_for('admin_home'))
            
            # Check if the student is registered
            if not is_student_registered(student_id):
                flash('Student is not registered.', 'search-student-event-error')
                return redirect(url_for('admin_home'))

            selected_date = parser.parse(selected_date_str).date()
        except Exception as e:
            return make_response(str(e), 400)

        try:
            # Query events
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT EventName, DueDate, CourseID, Title
                FROM calendarev,
                (SELECT * FROM calendar,
                (SELECT Course.CourseID, Title, Credits FROM Course,
                (SELECT c_id FROM student, StudentCourseReg
                WHERE student.StudentID = StudentCourseReg.StudentID AND student.StudentID = '{}') AS Students
                WHERE Course.CourseID = Students.c_id) AS courses
                                
                WHERE calendar.c_id = courses.CourseID) AS calendars
                WHERE calendarev.CalID = calendars.CalID AND DueDate = '{}';
            """.format(student_id, selected_date.strftime("%A, %d %b %Y")))
            events = cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving events', 400)

        if len(events) == 0:
            flash('No events found.', 'search-student-event-error')
            return redirect(url_for('admin_home'))

        format = [{"Event Title": name, "Due Date": due, "Course ID": course_id, "Course Title": title} for name, due, course_id, title in events]
        
        format.append({"Total Events": len(events)})

        student_name = get_student_name(student_id)
        
        return render_template('student-events.html', events=format, student_name=student_name, total_events=len(events), user_type=current_user.type)





def getLecIDs():
    try:
        cur = mysql.connection.cursor()
        cur.execute("Select l_id from Lecturer, Account where Lecturer.User_ID = Account.User_ID;")
        lecids =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    return lecids



@app.route('/course-container/<ccode>', methods=['GET'])
@login_required
def course_container(ccode):
    if current_user.is_authenticated:
        # Check course authorization
        if not check_course_authorization(ccode):
            return make_response("User is not authorized to view this course", 401)

        # Fetch course details based on the course code
        course_details = get_course_content(ccode)
        if course_details:
            return render_template('course-container.html', course_details=course_details, user_type=current_user.type)
        else:
            return make_response("Course not found", 404)




def get_course_content(ccode):
    try:
        cur = mysql.connection.cursor()

        # Fetching course code and name
        cur.execute("SELECT CourseID, Title FROM Course WHERE CourseID = %s", (ccode,))
        course_data = cur.fetchone()

        if course_data:
            course_code, course_name = course_data
            
            # Fetching content titles, content IDs, and item names
            cur.execute("""
                SELECT contentitems.item_id, content.cont_id, content.title, contentitems.link_filepath
                FROM content
                LEFT JOIN contentitems ON content.cont_id = contentitems.cont_id
                WHERE content.c_id = %s
            """, (ccode,))
            content_data = cur.fetchall()
            
            content_items = {}
            for item_id, cont_id, title, item_name in content_data:
                if title not in content_items:
                    content_items[title] = []
                content_items[title].append({"item_id": item_id, "cont_id": cont_id, "link_filepath": item_name})
            
            # Fetching calendar events with due dates
            cur.execute("""
                SELECT EventName, DueDate
                FROM calendarev
                WHERE CalID IN (SELECT CalID FROM Calendar WHERE c_id = %s)
            """, (ccode,))
            events_data = cur.fetchall()
            events = [{"Name": event[0], "Due Date": event[1]} for event in events_data]
            
            # Constructing the course details dictionary
            course_details = {
                'Course Code': course_code,
                'Course Name': course_name,
                'Content': content_items,
                'Calendar Events': events
            }
            
            cur.close()
            return course_details
        else:
            cur.close()
            return None
    except Exception as e:
        print("Error fetching course content:", e)
        return None


def valid(item_id):
    if current_user.is_authenticated:
        try:
            if current_user.type == "Student":
                # Fetch student ID
                student_id = studentid_by_userid(current_user.id)

                # Check if the student is enrolled in the course associated with the content item
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM StudentCourseReg 
                    WHERE StudentID = %s AND c_id = (
                        SELECT c_id FROM content 
                        JOIN contentitems ON content.cont_id = contentitems.cont_id
                        WHERE item_id = %s
                    )
                """, (student_id, item_id))
                result = cursor.fetchone()
                cursor.close()
            elif current_user.type == "Lecturer":
                # Fetch lecturer ID
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT l_id FROM Lecturer
                    JOIN Account ON Lecturer.User_ID = Account.User_ID
                    WHERE Account.User_ID = %s
                """, (current_user.id,))
                lecturer_id = cursor.fetchone()[0]
                cursor.close()

                # Check if the lecturer is assigned to the course associated with the content item
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM assigned 
                    WHERE l_id = %s AND c_id = (
                        SELECT c_id FROM content 
                        JOIN contentitems ON content.cont_id = contentitems.cont_id
                        WHERE item_id = %s
                    )
                """, (lecturer_id, item_id))
                result = cursor.fetchone()
                cursor.close()
            else:
                return make_response("Invalid user type", 403)
            
            if not result:
                return make_response("You are not apart of this course", 403)
            else:
                return None

        except mysql.connector.Error as err:
            return make_response(f"Database error: {err}", 500)
        
    return make_response("Unknown error", 500)



@app.route('/retrieveItem/<item_id>', methods=['GET'])
@login_required
def retrieve_item(item_id):
    if current_user.is_authenticated:
        if current_user.type == "Admin":
            pass
        else:
            valid_check = valid(item_id)
            if valid_check:
                return valid_check            
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT Course.CourseID, content.title, contentitems.link_filepath
                FROM contentitems
                JOIN content ON contentitems.cont_id = content.cont_id
                JOIN Course ON content.c_id = Course.CourseID
                WHERE contentitems.item_id = %s
            """, (item_id,))
            course_code, content_title, file_path = cur.fetchone()
            cur.close()

            # Get the current working directory
            current_directory = os.getcwd()
            # Construct the file path including the course code and content title folder
            folder_path = os.path.join(current_directory, f"{course_code} {content_title}")
            file_path = os.path.join(folder_path, os.path.basename(file_path))
            # Serve the file for download
            return send_file(file_path, as_attachment=True)
        except Exception as e:
                print("Error retrieving content item:", e)
                return make_response("Error retrieving content item", 400)



@app.route('/create-forum/<cc>', methods=['POST'])
@login_required
def create_forum(cc):
    if current_user.is_authenticated:
        if current_user.type == 'Lecturer':
            if request.method == 'POST':
                # Extract data from the form submission
                title = request.form.get('forumName')
                desc = request.form.get('description')

                if not title or not desc:
                    return make_response('Please provide both forum name and description.')
            
                foundCourse = False

                cur = mysql.connection.cursor()
                cur.execute("""
                SELECT l_id from Lecturer,account WHERE
                Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
                """.format(current_user.id))
                idd =  cur.fetchall()
                cur.close()
                l_id = idd[0][0]
                
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("""
                    SELECT Course.CourseID FROM Course, 
                    (SELECT c_id from Lecturer, assigned
                    where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
                    WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
                    """.format(l_id, cc))
                    courses =  cur.fetchall()
                    cur.close()
                except Exception as e:
                    return make_response('Error retrieving courses', 400)
                
                if courses and len(courses) >= 1:
                    foundCourse = True
                if foundCourse:
                    try:
                        cur = mysql.connection.cursor()
                        statement = "INSERT INTO forum(c_id, title, description, datecreated) VALUES ('{}','{}', '{}', '{}')".format(cc, title, desc, datetime.datetime.today().strftime('%Y-%m-%d'))
                        cur.execute(statement)
                        mysql.connection.commit()
                        cur.close()
                    except Exception as e:
                        return make_response('Database insert forum error ', 400)
                else:
                    return make_response('Course does not exist or you are not assigned to it', 400)
                return redirect(url_for('forums', ccode=cc))
        else:
            return abort(403)  # Only Lecturers can access this page



def check_course_authorization(ccode):
    if current_user.is_authenticated:
        try:
            if current_user.type == "Student":
                # Fetch student ID
                student_id = studentid_by_userid(current_user.id)
                # Check if the student is enrolled in the course associated with the forum
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM StudentCourseReg 
                    WHERE StudentID = %s AND c_id = %s
                """, (student_id, ccode))
                result = cursor.fetchone()
                cursor.close()

            elif current_user.type == "Lecturer":
                # Fetch lecturer ID
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT l_id FROM Lecturer, account 
                    WHERE Lecturer.User_ID = account.User_ID AND account.User_ID = %s
                """, (current_user.id,))
                lecturer_id = cursor.fetchone()[0]
                cursor.close()

                # Check if the lecturer is assigned to the course associated with the forum
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM assigned 
                    WHERE l_id = %s AND c_id = %s
                """, (lecturer_id, ccode))
                result = cursor.fetchone()
                cursor.close()

            else:
                return False

            return result is not None

        except Exception as e:
            return False

    else:
        return False




@app.route('/forums/<ccode>')
@login_required
def forums(ccode):
    if current_user.is_authenticated():
        if current_user.type == "Admin":
            # Admins have access, so no need to check further
            pass
        else:
            authorization_result = check_course_authorization(ccode)
            if not authorization_result:
                return make_response("User is not authorized to view this course", 401)

        try:
            # Query to get forum ID, names, description, and count of discussion threads
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT forum.c_id, forum.forum_id, forum.title, forum.description, COUNT(discussion_thread.disc_id) AS thread_count, forum.datecreated 
                FROM forum 
                LEFT JOIN discussion_thread ON forum.forum_id = discussion_thread.forum_id 
                WHERE forum.c_id = %s 
                GROUP BY forum.forum_id, forum.title, forum.description
            """, (ccode,))
            forums_data = cur.fetchall()
            cur.close()

            if not forums_data:
                # Fetch course code and title separately if no forums found
                cur = mysql.connection.cursor()
                cur.execute("SELECT CourseID, Title FROM Course WHERE CourseID = %s", (ccode,))
                course_data = cur.fetchone()
                cur.close()
                if not course_data:
                    return make_response("Course not found", 404)
                # Return course code and title along with no forums message
                return render_template('forums.html', forums=[], course=course_data, no_forums=True, user_type=current_user.type)
        except Exception as e:
            return make_response('Error retrieving forums', 400)
        
        # Render the template with forums data
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT CourseID, Title FROM Course WHERE CourseID = %s", (ccode,))
            course_data = cur.fetchone()
            cur.close()
        except Exception as e:
            return make_response('Error retreving course title', 400)
        return render_template('forums.html', forums=forums_data, course=course_data, user_type=current_user.type)    



@app.route('/create_thread/<fi>', methods=['POST'])
@login_required
def create_thread(fi):
    if current_user.is_authenticated:
        if request.method == 'POST':
            try:
                title = request.form.get('title')
                message = request.form.get('message')
                if not title or not message:
                    raise ValueError("Title and message are required")
            except ValueError as e:
                return make_response(f"Error: {str(e)}", 400)

            # Check authorization
            authorization_result = check_authorization(fi)
            if authorization_result:
                return authorization_result
            
            try:
                # Insert the new thread into the database
                cursor = mysql.connection.cursor()
                cursor.execute("INSERT INTO discussion_thread (forum_id, title, datecreated, message, owner) VALUES (%s, %s, %s, %s, %s)", (fi, title, datetime.datetime.today().strftime('%Y-%m-%d'), message, current_user.firstname + " " + current_user.lastname))
                mysql.connection.commit()
                cursor.close()
            except Exception as e:
                return make_response(f"Error inserting thread: {e}", 500)

            # Redirect to the threads page after creating the thread
            return redirect(url_for('retrieve_thread', fi=fi, user_type=current_user.type))



def check_authorization(fi):
    if current_user.is_authenticated:
        if current_user.type == "Student":
            # Fetch student ID
            try:
                student_id = studentid_by_userid(current_user.id)
            except mysql.connector.Error as err:
                return make_response(f"Error fetching student ID: {err}", 500)

            # Check if the student is enrolled in the course associated with the forum
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM StudentCourseReg 
                    WHERE StudentID = %s AND c_id = (
                        SELECT c_id FROM forum WHERE forum_id = %s
                    )
                """, (student_id, fi))
                result = cursor.fetchone()
                cursor.close()
            except mysql.connector.Error as err:
                return make_response(f"Error checking course enrollment: {err}", 500)

        elif current_user.type == "Lecturer":
            # Fetch lecturer ID
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT l_id FROM Lecturer, account 
                    WHERE Lecturer.User_ID = account.User_ID AND account.User_ID = %s
                """, (current_user.id,))
                lecturer_id = cursor.fetchone()[0]
                cursor.close()
            except mysql.connector.Error as err:
                return make_response(f"Error fetching lecturer ID: {err}", 500)

            # Check if the lecturer is assigned to the course associated with the forum
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM assigned 
                    WHERE l_id = %s AND c_id = (
                        SELECT c_id FROM forum WHERE forum_id = %s
                    )
                """, (lecturer_id, fi))
                result = cursor.fetchone()
                cursor.close()
            except mysql.connector.Error as err:
                return make_response(f"Error checking course assignment: {err}", 500)
        else:
            return make_response("Invalid user type", 403)

        if not result:
            return make_response("User is not authorized", 403)
        else:
            return None



@app.route('/reply/<disc_id>', methods=['POST'])
@login_required
def reply_to_thread(disc_id):
    if current_user.is_authenticated:
        if request.method == 'POST':
            try:
                message = request.form.get('message')
                if not message:
                    return make_response("Message is required",)
            except Exception as e:
                return make_response("Error: Incomplete form data", 400)

            # Check if the user is a student or a lecturer
            if current_user.type == "Student":
                # Fetch student ID
                try:
                    cursor = mysql.connection.cursor()
                    cursor.execute("""
                        SELECT StudentID FROM student, account 
                        WHERE student.User_ID = account.User_ID AND account.User_ID = %s
                    """, (current_user.id,))
                    student_id = cursor.fetchone()[0]
                    cursor.close()
                except mysql.connector.Error as err:
                    return make_response(f"Error fetching student ID: {err}", 500)

                # Check if the student is enrolled in the course associated with the thread
                try:
                    cursor = mysql.connection.cursor()
                    cursor.execute("""
                        SELECT * FROM StudentCourseReg 
                        WHERE StudentID = %s AND c_id = (
                            SELECT c_id FROM forum WHERE forum_id = (
                                SELECT forum_id FROM discussion_thread WHERE disc_id = %s
                            )
                        )
                    """, (student_id, disc_id))
                    result = cursor.fetchone()
                    cursor.close()
                except mysql.connector.Error as err:
                    return make_response(f"Error checking course enrollment: {err}", 500)

            elif current_user.type == "Lecturer":
                # Fetch lecturer ID
                try:
                    cursor = mysql.connection.cursor()
                    cursor.execute("""
                        SELECT l_id FROM Lecturer, account 
                        WHERE Lecturer.User_ID = account.User_ID AND account.User_ID = %s
                    """, (current_user.id,))
                    lecturer_id = cursor.fetchone()[0]
                    cursor.close()
                except mysql.connector.Error as err:
                    return make_response(f"Error fetching lecturer ID: {err}", 500)

                # Check if the lecturer is assigned to the course associated with the thread
                try:
                    cursor = mysql.connection.cursor()
                    cursor.execute("""
                        SELECT * FROM assigned 
                        WHERE l_id = %s AND c_id = (
                            SELECT c_id FROM forum WHERE forum_id = (
                                SELECT forum_id FROM discussion_thread WHERE disc_id = %s
                            )
                        )
                    """, (lecturer_id, disc_id))
                    result = cursor.fetchone()
                    cursor.close()
                except mysql.connector.Error as err:
                    return make_response(f"Error checking course assignment: {err}", 500)

            else:
                return make_response("Invalid user type", 403)

            if not result:
                return make_response("User is not authorized to reply to this thread", 403)

            try:
                # Fetch forum_id, title, and course_id of the thread
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT forum_id, title FROM discussion_thread WHERE disc_id = %s", (disc_id,))
                thread_info = cursor.fetchone()
                forum_id = thread_info[0]
                thread_title = thread_info[1]

            except Exception as e:
                print('Error retrieving thread information:', e)
            # Insert the reply into the database
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("INSERT INTO discussion_thread (forum_id, title, datecreated, message, owner, reply_id) VALUES (%s, %s, %s, %s, %s, %s)", (forum_id, thread_title, datetime.datetime.today().strftime('%Y-%m-%d'), message, current_user.firstname +" "+current_user.lastname, disc_id))
                mysql.connection.commit()
                cursor.close()
            except Exception as e:
                print('Error inserting reply:', e)
            return redirect(url_for('retrieve_thread', fi=forum_id, user_type=current_user.type))  # Redirect to the thread view page


@app.route('/retrieve-thread/<fi>', methods=['GET'])
@login_required
def retrieve_thread(fi):
    if current_user.is_authenticated:
        # Check if the user is an admin
        if current_user.type == "Admin":
            # Admins have access, so no need to check further
            pass
        else:
            # Check authorization
            authorization_result = check_authorization(fi)
            if authorization_result:
                return authorization_result
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT f.title AS forum_title, dt.title AS thread_title, dt.message, dt.datecreated, dt.owner, dt.disc_id, dt.reply_id   
                FROM discussion_thread dt
                JOIN forum f ON dt.forum_id = f.forum_id
                WHERE dt.forum_id = '{}';
            """.format(fi))            
            threads = cur.fetchall()
            cur.close()
            if threads:
                formatted_threads = [{'Forum ID': fi, 
                                      'Forum Title': thread[0], 
                                      'Thread Title': thread[1], 
                                      'Message': thread[2], 
                                      'Date Created': thread[3], 
                                      'Owner': thread[4],
                                      'Discussion ID': thread[5], 
                                      'Reply ID': thread[6]} 
                                      for thread in threads]
            else:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT title
                    FROM forum
                    WHERE forum_id = '{}';
                """.format(fi)) 
                forum_title = cur.fetchone()[0]  # Extract just the title
                cur.close()
                formatted_threads = [{'Forum ID': fi, 'Forum Title': forum_title}]
        except Exception as e:
            print('Error retrieving threads:', e)
            # Handle the error appropriately

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT Course.CourseID, Course.Title
                FROM forum
                JOIN Course ON forum.c_id = Course.CourseID
                WHERE forum.forum_id = '{}';
            """.format(fi)) 
            course= cur.fetchone()
            return render_template('threads.html', threads=formatted_threads, course=course, user_type=current_user.type)
        except Exception as e:
            print('Error retrieving threads:', e)



@app.route('/createContent/<cc>', methods=['POST'])
@login_required
def createContent(cc):
    if current_user.is_authenticated:
        if current_user.type == "Lecturer":
            try:
                # Get the content title from the form
                title = request.form.get('contentTitle')
                if not title:
                    return make_response("Title is required",)
            except Exception:
                return make_response("Incorrect form data", 400)
            
            # Query the database to get the lecturer's ID
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT l_id FROM Lecturer
                JOIN account ON Lecturer.User_ID = account.User_ID
                WHERE account.User_ID = '{}'
            """.format(current_user.id))
            lecturer_id = cur.fetchone()[0]
            cur.close()
            
            # Query the database to check if the lecturer is assigned to the course
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT c_id FROM assigned
                    WHERE l_id = '{}' AND c_id = '{}'
                """.format(lecturer_id, cc))
                course = cur.fetchone()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving courses', 400)
            
            # If the lecturer is assigned to the course, create the content
            if course:
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        INSERT INTO content (c_id, title)
                        VALUES ('{}', '{}')
                    """.format(course[0], title))
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    return make_response('Error creating content', 400)
                
                # Redirect to the URL for the course container
                return redirect(url_for('course_container', ccode=cc))
            else:
                return make_response("Lecturer not assigned to course", 400)
        else:
            return make_response("Unauthorized", 401)




@app.route('/content/<ccode>', methods=['GET'])
@login_required
def retrieve_content(ccode):
    if current_user.is_authenticated():
        if current_user.type == "Admin":
            # Admins have access, so no need to check further
            pass
        else:
            authorization_result = check_course_authorization(ccode)
            if not authorization_result:
                return make_response("User is not authorized to view this course contents", 401)
        course_details = get_course_content(ccode)
        if course_details:
            return render_template('content.html', course_details=course_details, user_type=current_user.type)
        else:
            return make_response("Course not found", 404)




@app.route('/createItem/<cc>/<cid>', methods=['POST'])
@login_required
def createItem(cc, cid):
    if current_user.is_authenticated():
        if current_user.type == "Lecturer":
            titlefound = False
            sectit = ""
            try:
                file = request.files['file']
                link = request.form.get('link')
                if not file:
                    return make_response("A file is needed", 400)
            except Exception:
                return make_response("Incorrect form data", 400)

            # Fetch lecturer ID
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT l_id from Lecturer, account 
                WHERE Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
            """.format(current_user.id))
            l_id = cur.fetchone()[0]
            cur.close()

            # Check if lecturer is assigned to the course
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT Course.CourseID 
                    FROM Course 
                    INNER JOIN (SELECT c_id from Lecturer, assigned
                                WHERE Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
                    ON Course.CourseID = Lecturers.c_id 
                    WHERE Course.CourseID = '{}'
                """.format(l_id, cc))
                courses = cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving courses', 400)

            if len(courses) < 1:
                return make_response("Lecturer not assigned to course", 400)

            # Fetch content titles for the course
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT content.cont_id, content.title 
                    FROM content 
                    INNER JOIN course ON content.c_id = course.CourseID 
                    WHERE course.CourseID = '{}';
                """.format(cc))
                contents = cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving content titles', 400)

            if len(contents) == 0:
                return make_response("Incorrect course code", 400)

            for cont_id, realtit in contents:
                if int(cont_id) == int(cid):
                    titlefound = True
                    sectit = realtit
                    break

            if titlefound:
                filename = secure_filename(file.filename)
                try:
                    cur = mysql.connection.cursor()
                    if filename == "":
                        statement = "INSERT INTO contentitems(cont_id, title, link_filepath) VALUES ('{}','{}', '{}')".format(cid, sectit, link)
                    else:
                        statement = "INSERT INTO contentitems(cont_id, title, link_filepath) VALUES ('{}','{}', '{}')".format(cid, sectit, filename)
                    cur.execute(statement)
                    mysql.connection.commit()
                    cur.close()

                    if filename != "":
                        try:
                            os.makedirs(cc + " " + sectit)
                        except FileExistsError:
                            pass
                        file.save(os.path.join(cc + " " + sectit, filename))

                    return redirect(url_for('course_container', ccode=cc))
                except Exception as e:
                    return make_response('Error creating content item', 400)
            else:
                return make_response("Incorrect content ID", 400)
        else:
            return make_response("Unauthorized", 401)



def getAllCourses():
    try:
        cur = mysql.connection.cursor()
        cur.execute("select * from course;")
        courses =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    return courses



@app.route('/submit/<cc>', methods=['GET', 'POST'])
@login_required
def submitAssignment(cc):
    if current_user.is_authenticated():
        if current_user.type == "Student":
            if request.method == 'POST':
                try:
                    file = request.files['file']
                    if file.filename == '':
                        return make_response("No file selected", 400)
                except Exception:
                    return make_response("Insert a file!!!", 400)
                
                # Retrieve student ID
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        SELECT StudentID
                        FROM Student
                        WHERE User_ID = '{}';
                    """.format(current_user.id))
                    student_id = cur.fetchone()[0]
                    cur.close()
                except Exception as e:
                    return make_response('Error retrieving student ID', 400)
                
                # Check if the student is enrolled in the course
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        SELECT *
                        FROM StudentCourseReg
                        WHERE c_id = '{}' AND StudentID = '{}';
                    """.format(cc, student_id))
                    enrolled = cur.fetchone()
                    cur.close()
                    if not enrolled:
                        return make_response("You are not enrolled in this course", 403)
                except Exception as e:
                    return make_response('Error checking course enrollment', 400)

                # Insert submission into the database
                try:
                    filename = secure_filename(file.filename)
                    cur = mysql.connection.cursor()
                    statement = "INSERT INTO Assignment(stud_id, files, dateSubmitted, CourseID) VALUES ('{}', '{}', '{}', '{}')".format(student_id, filename, datetime.datetime.today().strftime('%Y-%m-%d'), cc)
                    cur.execute(statement)
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    print(e)
                    return make_response('Error submitting assignment', 400)
                
                # Save the uploaded file
                try:
                    studentid = studentid_by_userid(current_user.id)
                    directory = os.path.join(cc + " Assignment " + studentid)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    file.save(os.path.join(directory, filename))
                except Exception as e:
                    return make_response('Error saving file', 400)
                
                
                return redirect(url_for("getGrade", cc=cc))
            if request.method == 'GET':
                return render_template('submit.html', course_code=cc, user_type=current_user.type)
        else:
            return make_response("Unauthorized", 401)

def studentid_by_userid(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT StudentID FROM Student WHERE User_ID = %s", (user_id,))
        student_id = cur.fetchone()
        cur.close()
        if student_id:
            return student_id[0]  # Return the first element of the tuple (student ID)
        else:
            return None  # Return None if no student ID is found
    except Exception as e:
        print("Error:", e)
        return None



@app.route('/give-grade/<cc>/<assid>', methods=['POST'])
@login_required
def submitGrade(cc, assid):
    if current_user.is_authenticated:
        if current_user.type == "Lecturer":
            try:
                grade = request.form.get('Grade')  # Access form data using request.form
                if not grade:
                    return make_response("Grade is needed")
            except Exception:
                return make_response("Incorrect form data", 400)
        
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT l_id from Lecturer,account WHERE
            Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
            """.format(current_user.id))
            idd =  cur.fetchall()
            cur.close()
            l_id = idd[0][0]
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                SELECT Course.CourseID FROM Course, 
                (SELECT c_id from Lecturer, assigned
                where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
                WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
                """.format(l_id, cc))
                courses =  cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving courses', 400)
            if(len(courses) <1):
                return make_response("lecturer not assigned to course")
            
            try:
                cur = mysql.connection.cursor()
                statement = "update assignment set grade = {} where ass_id = {} and CourseID = '{}'".format(grade, assid, cc)
                cur.execute(statement)
                mysql.connection.commit()
                cur.close()
            except Exception as e:
                return make_response('update error ', 400)
            
            return redirect(url_for('getGrade', cc=cc))

    

def valid_assignment(assid):
    if current_user.is_authenticated:
        try:
            if current_user.type == "Student":
                # Fetch student ID
                student_id=studentid_by_userid(current_user.id)
                
                # Check if the assignment belongs to the student
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM assignment 
                    WHERE ass_id = %s AND stud_id = %s
                """, (assid, student_id))
                result = cursor.fetchone()
                cursor.close()
            elif current_user.type == "Lecturer":
                # Fetch lecturer ID
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT l_id FROM Lecturer
                    JOIN Account ON Lecturer.User_ID = Account.User_ID
                    WHERE Account.User_ID = %s
                """, (current_user.id,))
                lecturer_id = cursor.fetchone()[0]
                cursor.close()

                # Create a new cursor for the second query
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT * FROM assigned 
                    WHERE l_id = %s AND c_id = (
                        SELECT Course.CourseID FROM Course 
                        JOIN assignment ON Course.CourseID = assignment.CourseID
                        WHERE ass_id = %s
                    )
                """, (lecturer_id, assid))
                result = cursor.fetchone()
                cursor.close()
            else:
                return make_response("Invalid user type", 403)
            
            if not result:
                return make_response("You are not allowed to view this assignment", 403)
            else:
                return None

        except Exception as e:
            return make_response(f"Assignment retrieval error: {e}", 500)
        
    return make_response("Unknown error", 500)


@app.route('/retrieveAssignment/<assid>', methods=['GET'])
@login_required
def retrieve_assignment(assid):
    if current_user.is_authenticated:
        valid_check = valid_assignment(assid)
        if valid_check:
            return valid_check            
        try:
            # Fetch student ID associated with the assignment (if applicable)
            student_id = None
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT stud_id, Course.CourseID, assignment.files
                FROM assignment
                JOIN Course ON assignment.CourseID = Course.CourseID
                WHERE assignment.ass_id = %s
            """, (assid,))
            student_id, course_code, file_path = cursor.fetchone()
            cursor.close()

            # Fetch assignment details
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT Course.CourseID, assignment.files
                FROM assignment
                JOIN Course ON assignment.CourseID = Course.CourseID
                WHERE assignment.ass_id = %s
            """, (assid,))
            course_code, file_path = cursor.fetchone()
            cursor.close()

            # Construct the file path
            if student_id:
                folder_path = os.path.join(os.getcwd(), f"{course_code} Assignment {student_id}")

            file_path = os.path.join(folder_path, os.path.basename(file_path))
            
            # Serve the file
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            print("Error retrieving assignment:", e)
            return make_response("Error retrieving assignment", 400)



    
@app.route('/grade/<cc>', methods=['GET'])
@login_required
def getGrade(cc):
    if current_user.is_authenticated:
        if current_user.type == "Student":
            # Retrieve student ID
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT StudentID
                    FROM Student
                    WHERE User_ID = '{}';
                """.format(current_user.id))
                student_id = cur.fetchone()[0]
                cur.close()
            except Exception as e:
                return make_response('Error retrieving student ID', 400)
            
            # Check if the student is enrolled in the course
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT *
                    FROM StudentCourseReg
                    WHERE c_id = '{}' AND StudentID = '{}';
                """.format(cc, student_id))
                enrolled = cur.fetchone()
                cur.close()
                if not enrolled:
                    return make_response("You are not enrolled in this course", 403)
            except Exception as e:
                return make_response('Error checking course enrollment', 400)
            
            # Retrieve assignments and grades for the logged-in student in the specified course
            format = []
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT assignment.ass_id, assignment.files, assignment.grade
                    FROM assignment
                    WHERE stud_id = '{}' AND assignment.CourseID = '{}';
                """.format(student_id, cc))
                assignments = cur.fetchall()
                cur.close()

                for assid, files, grade in assignments:
                    format.append({"Assignment ID": assid, "File": files, "Grade": grade})
                
                # Calculate average grade
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        SELECT AVG(grade) 
                        FROM assignment 
                        WHERE stud_id = '{}' AND CourseID = '{}';
                    """.format(student_id, cc))
                    average_grade = cur.fetchone()[0]
                    cur.close()
                except Exception as e:
                    return make_response('Error calculating average grade: {}'.format(str(e)), 400)
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("SELECT Title FROM Course WHERE CourseID = %s", (cc,))
                    title = cur.fetchone()
                    cur.close()
                except Exception as e:
                    return make_response('Error retreiving course title', 400)
                return render_template('grades.html', assignments=format, average_grade=average_grade, course_code=cc, title=title, user_type=current_user.type)
            except Exception as e:
                return make_response('Error retrieving assignments: {}'.format(str(e)), 400)
        elif current_user.type == "Lecturer":
            # Retrieve lecturer ID
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT l_id
                    FROM Lecturer
                    WHERE User_ID = '{}';
                """.format(current_user.id))
                lecturer_id = cur.fetchone()[0]
                cur.close()
            except Exception as e:
                return make_response('Error retrieving lecturer ID', 400)
            
            # Check if the lecturer is assigned to the course
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT *
                    FROM assigned
                    WHERE c_id = '{}' AND l_id = '{}';
                """.format(cc, lecturer_id))
                assigned = cur.fetchone()
                cur.close()
                if not assigned:
                    return make_response("You are not assigned to teach this course", 403)
            except Exception as e:
                return make_response('Error checking course assignment', 400)
            
            # Retrieve assignments and grades for all students enrolled in the specified course
            format = []
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT student.StudentID, student.FirstName, student.MiddleName, student.LastName, 
                           assignment.ass_id, assignment.files, assignment.grade
                    FROM assignment
                    INNER JOIN student ON assignment.stud_id = student.StudentID
                    WHERE assignment.CourseID = '{}';
                """.format(cc))
                assignments = cur.fetchall()
                cur.close()

                assignments_by_student = defaultdict(list)
                for studid, first, mid, last, assid, files, grade in assignments:
                    assignments_by_student[studid].append({
                        "First Name": first,
                        "Middle Name": mid,
                        "Last Name": last,
                        "Assignment ID": assid,
                        "File": files,
                        "Grade": grade
                    })
                
                # Calculate average grade for each student
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("""
                        SELECT stud_id, AVG(grade) AS average_grade
                        FROM assignment
                        WHERE CourseID = '{}'
                        GROUP BY stud_id;
                    """.format(cc))
                    avg_grades = cur.fetchall()
                    average_grades = {stud_id: avg_grade for stud_id, avg_grade in avg_grades}
                    cur.close()
                except Exception as e:
                    return make_response('Error calculating average grades', 400)
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("SELECT Title FROM Course WHERE CourseID = %s", (cc,))
                    title = cur.fetchone()
                    cur.close()
                except Exception as e:
                    return make_response('Error retreiving course title', 400)
                return render_template('grades.html', assignments_by_student=assignments_by_student, title=title, average_grades=average_grades, course_code=cc, user_type=current_user.type)
            except Exception as e:
                return make_response('Error retrieving assignments', 400)
        else:
            return make_response("Unauthorized user")


@app.route('/report1', methods=['GET'])
def report1():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)     
        report_data = []
        try:
            cur = mysql.connection.cursor()

            # Create or replace the view
            cur.execute("""
            CREATE OR REPLACE VIEW 50Students AS
            SELECT CourseID, Title, COUNT(studentcoursereg.StudentID) AS numStudents
            FROM course, studentcoursereg
            WHERE course.CourseID = studentcoursereg.c_id
            GROUP BY CourseID
            HAVING COUNT(studentcoursereg.StudentID) >= 50;
            """)

            # Fetch data using the view
            cur.execute("""
            SELECT CourseID, Title, numStudents
            FROM 50Students;
            """)
            stud = cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error getting data for report 1', 400)

        # Process fetched data
        for code, title, num in stud:
            report_data.append({"Course Code": code, "Title": title, "Number of Students": num})

        total_courses = len(stud)

        return render_template('report1.html', report_data=report_data, total_courses=total_courses, user_type=current_user.type)


@app.route('/report2', methods=['GET'])
def report2():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)
    
        try:
            cur = mysql.connection.cursor()

            # Retrieve students with five or more courses and count total students
            cur.execute("""
            CREATE OR REPLACE VIEW 5Courses AS 
            SELECT student.StudentID, student.FirstName, student.MiddleName, student.LastName, COUNT(studentcoursereg.c_id) AS numCourses
            FROM student
            INNER JOIN studentcoursereg ON student.StudentID = studentcoursereg.StudentID
            GROUP BY student.StudentID
            HAVING COUNT(studentcoursereg.c_id) >= 5;
            """)
            cur.execute("""
            SELECT * FROM 5Courses;
            """)
            students = cur.fetchall()
            total_students = len(students)
            cur.close()
        except Exception as e:
            return make_response('Error getting data for report 2', 400)
        
        # Format report data
        report_data = [{"Student ID": id, "First Name": first, "Middle Name": middle, "Last Name": last, "Number of Courses": num} for id, first, middle, last, num in students]

        return render_template('report2.html', report_data=report_data, total_students=total_students, user_type=current_user.type)


@app.route('/report3', methods=['GET'])
def report3():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)
        format = []
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            CREATE OR REPLACE VIEW 3AssignedCourses AS 
            SELECT lecturer.l_id, lecturer.FirstName, lecturer.MiddleName, lecturer.LastName, COUNT(assigned.c_id) AS numCourses
            FROM lecturer
            INNER JOIN assigned ON lecturer.l_id = assigned.l_id
            GROUP BY lecturer.l_id
            HAVING numCourses >= 3;
            """)
            cur.execute("""
            SELECT * FROM 3AssignedCourses;
            """)
            lecturers = cur.fetchall()
            cur.close()
        except Exception as e:
            print(e)
            return make_response('Error creating or fetching data for Report3', 400)

        for lecturer in lecturers:
            lecturer_info = {
                "Lecturer ID": lecturer[0],
                "First Name": lecturer[1],
                "Middle Name": lecturer[2],
                "Last Name": lecturer[3],
                "Number of Courses": lecturer[4]
            }
            format.append(lecturer_info)

        total_lecturers = len(lecturers)

        return render_template('report3.html', lecturers=format, total_lecturers=total_lecturers, user_type=current_user.type)

@app.route('/report4', methods=['GET'])
def report4():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)
        format = []
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            CREATE OR REPLACE VIEW 10MostEnrolled AS 
            SELECT course.CourseID, course.Title, COUNT(studentcoursereg.StudentID) AS numStudents
            FROM course
            INNER JOIN studentcoursereg ON course.CourseID = studentcoursereg.c_id
            GROUP BY course.CourseID
            ORDER BY numStudents DESC
            LIMIT 10;
            """)
            cur.execute("""
            SELECT * FROM 10MostEnrolled;
            """)
            courses = cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error creating or fetching data for Report4', 400)

        for course in courses:
            course_info = {
                "Course Code": course[0],
                "Title": course[1],
                "Number of Students": course[2]
            }
            format.append(course_info)

        return render_template('report4.html', report_data=format, user_type=current_user.type)


@app.route('/report5', methods=['GET'])
def report5():
    if current_user.is_authenticated:
        if current_user.type != "Admin":
            return abort(403)
        format = []
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            CREATE OR REPLACE VIEW 10HighestAverage AS 
            SELECT  s.StudentID, s.FirstName, s.MiddleName, s.LastName, AVG(a.grade) AS Average
            FROM Student s
            INNER JOIN assignment a ON s.StudentID = a.stud_id
            GROUP BY s.StudentID
            ORDER BY Average DESC
            LIMIT 10;
            """)
            cur.execute("""
            SELECT * FROM 10HighestAverage;
            """)
            students = cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error creating or fetching data for Report5', 400)

        for student in students:
            student_info = {
                "Student ID": student[0],
                "First Name": student[1],
                "Middle Name": student[2],
                "Last Name": student[3],
                "Average": student[4]
            }
            format.append(student_info)

        return render_template('report5.html', report_data=format, user_type=current_user.type)
