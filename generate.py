import random
import datetime
from faker import Faker
import re


fake = Faker()

file = open("insertquery.sql", "w")

# Define the number of students, courses, and lecturers
num_students = 100000
num_courses = 250
num_lecturers = 100

numcourses = {}

# Define the maximum and minimum number of courses per student
max_courses_per_student = 6
min_courses_per_student = 3

# Define the minimum number of students per course
min_students_per_course = 10

# Define the maximum and minimum number of courses per lecturer
max_courses_per_lecturer = 5
min_courses_per_lecturer = 1

# Open a file for writing the account data
file.write("INSERT INTO account VALUES\n")
for user_id in range(1, num_students + num_lecturers + 1):
    if user_id <= num_students:
        role = "Student"
    else:
        role = "Lecturer"

    if user_id == num_students + num_lecturers:
        file.write("('{}', '{}', '{}');\n".format(f'UserID{user_id}', f'Password{user_id}', role))
    else:
        file.write("('{}', '{}', '{}'),\n".format(f'UserID{user_id}', f'Password{user_id}', role))

# Open a file for writing the student data
file.write("\nINSERT INTO Student(StudentID, FirstName, MiddleName, LastName, User_ID) VALUES\n")
for student_id in range(1, num_students + 1):
    numcourses[student_id] = random.randint(min_courses_per_student, max_courses_per_student)
    if student_id == num_students:
        first_name = fake.first_name()
        middle_name = fake.first_name()
        last_name = fake.last_name()
        file.write("('{}', '{}', '{}', '{}', '{}');\n".format(f'StudentID{student_id}', first_name, middle_name, last_name, f'UserID{student_id}'))
    else:
        first_name = fake.first_name()
        middle_name = fake.first_name()
        last_name = fake.last_name()
        file.write("('{}', '{}', '{}', '{}', '{}'),\n".format(f'StudentID{student_id}', first_name, middle_name, last_name, f'UserID{student_id}'))

# Open a file for writing the register data
file.write("\nINSERT INTO Register VALUES\n")
for user_id in range(1, num_students + num_lecturers + 1):
    if user_id <= num_students:
        role = "Student"
    else:
        role = "Lecturer"

    if user_id == num_students + num_lecturers:
        file.write("('{}', '{}', '{}');\n".format(f'UserID{user_id}', f'MemberID{user_id}', datetime.datetime.today().strftime('%Y-%m-%d')))
    else:
        file.write("('{}', '{}', '{}'),\n".format(f'UserID{user_id}', f'MemberID{user_id}', datetime.datetime.today().strftime('%Y-%m-%d')))


# Define a list of words to exclude from capitalization
exclude_words = ["in", "and", "of", "at", "to"]  # Add more words if needed

# Function to capitalize the first letter of each word except excluded words
def capitalize_course_title(title):
    words = title.split()
    capitalized_words = [word.capitalize() if word.lower() not in exclude_words else word for word in words]
    return ' '.join(capitalized_words)

# Generate fake course titles
fake_course_titles = [capitalize_course_title(fake.catch_phrase()) for _ in range(num_courses)]

# Function to clean course code by removing non-letter characters and returning the first four characters
def clean_course_code(title):
    # Remove non-letter characters and convert to uppercase
    cleaned_title = re.sub(r'[^a-zA-Z]', '', title).upper()
    # Take the first four characters
    return cleaned_title[:4]

# Generate fake course codes based on cleaned course titles
fake_course_codes = [clean_course_code(title)[:4] + str(i) for i, title in enumerate(fake_course_titles, start=1)]

# Open a file for writing the course data
file.write("\nINSERT INTO course VALUES\n")
for i in range(num_courses):
    course_code = fake_course_codes[i]
    course_title = fake_course_titles[i]
    credit_hours = random.randint(1, 3)
    if i == num_courses - 1:
        file.write(f"('{course_code}', '{course_title}', {credit_hours});\n")
    else:
        file.write(f"('{course_code}', '{course_title}', {credit_hours}),\n")


# Open a file for writing the calendar data
file.write("\nINSERT INTO Calendar(c_id) VALUES\n")
for coursecode in range(1, num_courses + 1):
    fake_course_code = fake_course_codes[coursecode - 1]  # Subtract 1 to match the 0-based index of the list
    if coursecode == num_courses:
        file.write("('{}');\n".format(fake_course_code))
    else:
        file.write("('{}'),\n".format(fake_course_code))


# Open a file for writing the student course registration data
file.write("\nINSERT INTO StudentCourseReg(c_id, StudentID) VALUES\n")
used = set()  # Using a set to ensure uniqueness
for studid in numcourses:
    for i in range(numcourses[studid]):
        course_code = random.choice(fake_course_codes)
        while (course_code, studid) in used:  # Check if the pair already exists
            course_code = random.choice(fake_course_codes)
        used.add((course_code, studid))
        if studid == num_students and numcourses[studid] - 1 == i:
            file.write("('{}', '{}');\n".format(course_code, f'StudentID{studid}'))
        else:
            file.write("('{}', '{}'),\n".format(course_code, f'StudentID{studid}'))

# Open a file for writing the lecturer data
file.write("\nINSERT INTO Lecturer VALUES\n")
lecturers_assigned_courses = {}  # Track the number of courses assigned to each lecturer
for lecturer_id in range(1, num_lecturers + 1):
    if lecturer_id == num_lecturers:
        first_name = fake.first_name()
        middle_name = fake.first_name()
        last_name = fake.last_name()
        file.write("('{}', '{}', '{}', '{}', '{}');\n".format(f'LecturerID{lecturer_id}', first_name, middle_name, last_name, f'UserID{lecturer_id+num_students}'))
    else:
        first_name = fake.first_name()
        middle_name = fake.first_name()
        last_name = fake.last_name()
        file.write("('{}', '{}', '{}', '{}', '{}'),\n".format(f'LecturerID{lecturer_id}', first_name, middle_name, last_name, f'UserID{lecturer_id+num_students}'))

# Generate insert statements for assigned courses
file.write("\n-- Insert statements for assigned courses\n")

# Track assigned lecturers to avoid exceeding maximum courses per lecturer
assigned_lecturers = {lecturer_id: 0 for lecturer_id in range(1, num_lecturers + 1)}

# Assign one course to each lecturer before randomly assigning the rest
for lecturer_id in range(1, num_lecturers + 1):
    course_code = fake_course_codes[lecturer_id - 1]  # Assign the course at the current index
    file.write("INSERT INTO assigned(c_id, l_id) VALUES ('{}', 'LecturerID{}');\n".format(course_code, lecturer_id))
    assigned_lecturers[lecturer_id] += 1

# Continue assigning the remaining courses
for course_code in fake_course_codes[num_lecturers:]:
    # Select a random lecturer who hasn't reached the maximum courses
    available_lecturers = [lecturer_id for lecturer_id, assigned_count in assigned_lecturers.items() 
                           if assigned_count < max_courses_per_lecturer]
    
    if not available_lecturers:
        # All lecturers have reached their maximum courses, reset the counts and assign from the beginning
        assigned_lecturers = {lecturer_id: 0 for lecturer_id in range(1, num_lecturers + 1)}
        available_lecturers = list(assigned_lecturers.keys())

    lecturer_id = random.choice(available_lecturers)
    assigned_lecturers[lecturer_id] += 1

    file.write("INSERT INTO assigned(c_id, l_id) VALUES ('{}', 'LecturerID{}');\n".format(course_code, lecturer_id))
    
file.close()
