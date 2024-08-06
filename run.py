from flask import Flask, request, jsonify
import bcrypt
import psycopg2
from flask_cors import CORS
import json

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


app = Flask(__name__)
#PostgreSQL connection and details
con = psycopg2.connect(database="aegis_beta", user="postgres", password="t3tr1s", port="5432")


# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "youhavetoguess"  # Change this!
jwt = JWTManager(app)

#CORS was needed to resolve cross-origin issues
CORS(app)

#API for registering a user
@app.post("/api/add_user")
def add_user():
    # Get data from request
    data = request.json
    student_id = data.get("student_id")
    fname = data.get("fname")
    lname = data.get("lname")
    email = data.get("email")
    password = data.get("password")
    
    INSERT_USER = "INSERT INTO users (student_id, fname, lname, email, password_hash) VALUES (%s, %s, %s, %s, %s);"

    # Validate input
    if not (student_id and fname and lname and email and password):
        return jsonify({"error": "Missing required fields"}), 400

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_USER, (student_id, fname,lname, email, password_hash))
        con.commit()
    return jsonify(message="User added successfully."), 200


#API for logging in a user
@app.post("/api/login")
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    FIND_USER = "SELECT student_id, email, fname, lname, password_hash FROM users WHERE email = %s;"

    # Validate input
    if not (email and password):
        return jsonify({"error": "Missing required fields"}), 400

    # Get user from database
    with con:
        with con.cursor() as cursor:
            cursor.execute(FIND_USER, (email,))
            user = cursor.fetchone()

    # Check if user exists and password is correct
    if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
        # Return all user data in token
        access_token = create_access_token(identity=email)
        return jsonify({
            "message": "Login successful.",
            "access_token": access_token,
            "student_id": user[0],
            "email": user[1],
            "fname": user[2],
            "lname": user[3]}), 200

    else:
        return jsonify(message="Invalid credentials."), 404



#API for getting a user by student_id
@app.get("/api/get_user/<student_id>")
def get_user(student_id):
    GET_USER = "SELECT student_id, fname, lname, email FROM users WHERE student_id = %s;"
    
    try:
        with con:
            with con.cursor() as cursor:
                cursor.execute(GET_USER, (student_id,))  # Ensure student_id is passed as a tuple
                user = cursor.fetchone()  # Fetches the first row of a query result or None if no result
                
                if user:
                    # Map the database row to a dictionary
                    user_dict = {
                        "student_id": user[0],
                        "fname": user[1],
                        "lname": user[2],
                        "email": user[3]
                    }
                    return jsonify(user_dict), 200  # Return the user as a JSON response with status code 200
                else:
                    return jsonify({"error": "User not found"}), 404  # Return an error message if no user is found
    except Exception as e:
        return jsonify({"error": str(e)}), 500








#API for getting all courses and storing in an array
@app.get("/api/get_courses")
def get_courses():
    GET_COURSES = "SELECT course_id, title, description FROM courses;"
    
    # List of dictionaries to store courses
    courses = []

    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_COURSES)
            list_course  = cursor.fetchall()
            for course in list_course:
                course_dict = {
                    "course_id": course[0],
                    "title": course[1],
                    "description": course[2]
                }
                courses.append(course_dict)
            
    return jsonify(courses), 200


#API for getting lessons in a course
@app.get("/api/get_lessons/<course_id>")
def get_lessons(course_id):
    GET_LESSONS = "SELECT lesson_id, course_id, title, content, type FROM lessons WHERE course_id = %s;"
    
    # List of dictionaries to store lessons
    lessons = []

    try:
        with con.cursor() as cursor:
            cursor.execute(GET_LESSONS, (course_id,))  # Ensure course_id is passed as a tuple
            list_lesson = cursor.fetchall()
            for lesson in list_lesson:
                lesson_dict = {
                    "lesson_id": lesson[0],
                    "course_id": lesson[1],
                    "title": lesson[2],
                    "content": lesson[3],
                    "type": lesson[4]
                }
                lessons.append(lesson_dict)
        con.commit()
    except Exception as e:
        con.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(lessons), 200


#API for getting a single lesson by lesson_id
@app.get("/api/get_lesson/<lesson_id>")
def get_lesson(lesson_id):
    GET_LESSON = "SELECT lesson_id, course_id, title, content, type FROM lessons WHERE lesson_id = %s;"
    
    try:
        with con:
            with con.cursor() as cursor:
                cursor.execute(GET_LESSON, (lesson_id,))  # Ensure lesson_id is passed as a tuple
                lesson = cursor.fetchone()  # Fetches the first row of a query result or None if no result
                
                if lesson:
                    # Map the database row to a dictionary
                    lesson_dict = {
                        "lesson_id": lesson[0],
                        "course_id": lesson[1],
                        "title": lesson[2],
                        "content": lesson[3],
                        "type": lesson[4]
                    }
                    return jsonify(lesson_dict), 200  # Return the lesson as a JSON response with status code 200
                else:
                    return jsonify({"error": "Lesson not found"}), 404  # Return an error message if no lesson is found
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return an error message if there is a database or execution error


#API for completing a lesson
@app.post("/api/complete_lesson")
def complete_lesson():
    data = request.json
    student_id = data.get("student_id")
    lesson_id = data.get("lesson_id")
    status = "Completed"

    INSERT_COMPLETED_LESSON = "INSERT INTO user_progress (student_id, lesson_id, status) VALUES (%s, %s, %s);"

    # Validate input
    if not (student_id and lesson_id):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_COMPLETED_LESSON, (student_id, lesson_id, status))
        con.commit()
    return jsonify(message="Lesson completed successfully."), 200

#API for removing a lesson as completed
@app.post("/api/remove_completed_lesson")
def remove_completed_lesson():
    data = request.json
    student_id = data.get("student_id")
    lesson_id = data.get("lesson_id")

    DELETE_COMPLETED_LESSON = "DELETE FROM user_progress WHERE student_id = %s AND lesson_id = %s;"

    # Validate input
    if not (student_id and lesson_id):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(DELETE_COMPLETED_LESSON, (student_id, lesson_id))
        con.commit()
    return jsonify(message="Lesson removed successfully."), 200



#API for getting all completed lessons by student_id
@app.get("/api/get_completed_lessons/<student_id>")
def get_completed_lessons(student_id):
    GET_COMPLETED_LESSONS = "SELECT lesson_id, FROM user_progress WHERE student_id = %s;"
    
    # List of dictionaries to store courses
    lessons = []

    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_COMPLETED_LESSONS)
            list_course  = cursor.fetchall()
            for course in list_course:
                course_dict = {
                    "course_id": course[0],
                    "title": course[1],
                    "description": course[2]
                }
                lessons.append(course_dict)
            
    return jsonify(lessons), 200


# API for getting user progress grouped by courses
@app.get("/api/user_progress/<student_id>")
def user_progress(student_id):
    GET_COMPLETED_LESSONS = """
    SELECT l.course_id, c.title, COUNT(l.lesson_id) as total_lessons,
           COUNT(up.lesson_id) as completed_lessons
    FROM Lessons l
    LEFT JOIN User_Progress up ON l.lesson_id = up.lesson_id AND up.student_id = %s AND up.status = 'Completed'
    JOIN Courses c ON l.course_id = c.course_id
    GROUP BY l.course_id, c.title;
    """

    try:
        with con:
            with con.cursor() as cursor:
                cursor.execute(GET_COMPLETED_LESSONS, (student_id,))
                progress = cursor.fetchall()

        # Check if progress data is fetched properly
        if not progress:
            return jsonify([]), 200  # Return an empty list if no progress data is found

        # Process the data into a suitable format
        result = []
        for row in progress:
            total = row[2]
            completed = row[3]
            percentage = (completed / total) * 100 if total > 0 else 0
            result.append({
                "course_id": row[0],
                "title": row[1],
                "total_lessons": total,
                "completed_lessons": completed,
                "percentage": percentage
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error for debugging
        return jsonify({"error": str(e)}), 500








### ADMIN SPECIFIC APIS ###

#API for adding an admin
@app.post("/api/add_admin")
def add_admin():
    # Get data from request
    data = request.json
    admin_id = data.get("admin_id")
    fname = data.get("fname")
    lname = data.get("lname")
    email = data.get("email")
    password = data.get("password")
    
    INSERT_ADMIN = "INSERT INTO admins (admin_id, fname, lname, email, password_hash) VALUES (%s, %s, %s, %s, %s);"

    # Validate input
    if not (admin_id and fname and lname and email and password):
        return jsonify({"error": "Missing required fields"}), 400

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_ADMIN, (admin_id, fname,lname, email, password_hash))
        con.commit()
    return jsonify(message="Admin registered successfully."), 200


#API for logging in an admin using admin id and password
@app.post("/api/login_admin")
def login_admin():
    data = request.json
    email = data.get("admin_id")
    password = data.get("password")

    FIND_ADMIN = "SELECT admin_id, email, fname, lname, password_hash FROM admins WHERE admin_id = %s;"

    # Validate input
    if not (email and password):
        return jsonify({"error": "Missing required fields"}), 400

    # Get admin from database
    with con:
        with con.cursor() as cursor:
            cursor.execute(FIND_ADMIN, (email,))
            admin = cursor.fetchone()

    # Check if admin exists and password is correct
    if admin and bcrypt.checkpw(password.encode('utf-8'), admin[4].encode('utf-8')):
        # Return all admin data in token
        access_token = create_access_token(identity=email)
        return jsonify({
            "message": "Login successful.",
            "access_token": access_token,
            "admin_id": admin[0],
            "email": admin[1],
            "fname": admin[2],
            "lname": admin[3]}), 200

    else:
        return jsonify(message="Invalid credentials."), 404

#API for getting all users
@app.get("/api/get_users")
def get_users():
    GET_USERS = "SELECT student_id, fname, lname, email FROM users;"
    
    # List of dictionaries to store users
    users = []

    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_USERS)
            list_user  = cursor.fetchall()
            for user in list_user:
                user_dict = {
                    "student_id": user[0],
                    "fname": user[1],
                    "lname": user[2],
                    "email": user[3]
                }
                users.append(user_dict)
            
    return jsonify(users), 200


#API for editing a user
@app.post("/api/edit_user")
def edit_user():
    data = request.json
    student_id = data.get("student_id")
    fname = data.get("fname")
    lname = data.get("lname")
    email = data.get("email")

    EDIT_USER = "UPDATE users SET fname = %s, lname = %s, email = %s WHERE student_id = %s;"

    # Validate input
    if not (student_id and fname and lname and email):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(EDIT_USER, (fname, lname, email, student_id))
        con.commit()
    return jsonify(message="User edited successfully."), 200

#API for deleting a user
@app.post("/api/delete_user")
def delete_user():
    data = request.json
    student_id = data.get("student_id")

    DELETE_USER = "DELETE FROM users WHERE student_id = %s;"

    # Validate input
    if not student_id:
        return jsonify({"error": "Missing required fields"}), 400

    # Use the database connection
    with con:
        with con.cursor() as cursor:
            cursor.execute(DELETE_USER, (student_id,))
        con.commit()
    return jsonify(message="User deleted successfully."), 200



#API for adding a course
@app.post("/api/add_course")
def add_course():
    data = request.json
    title = data.get("title")
    description = data.get("description")

    INSERT_COURSE = "INSERT INTO courses (title, description) VALUES (%s, %s);"

    # Validate input
    if not (title and description):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_COURSE, (title, description))
        con.commit()
    return jsonify(message="Course added successfully."), 200



#API for deleting a course along with its lessons
@app.post("/api/delete_course")
def delete_course():
    data = request.json
    course_id = data.get("course_id")

    DELETE_COURSE = "DELETE FROM courses WHERE course_id = %s;"
    DELETE_LESSONS = "DELETE FROM lessons WHERE course_id = %s;"

    # Validate input
    if not course_id:
        return jsonify({"error": "Missing required fields"}), 400

    # Use the database connection
    with con:
        with con.cursor() as cursor:
            cursor.execute(DELETE_COURSE, (course_id,))  # Corrected to (course_id,)
            cursor.execute(DELETE_LESSONS, (course_id,))  # Corrected to (course_id,)
        con.commit()
    return jsonify(message="Course deleted successfully."), 200



#API for editing a course
@app.post("/api/edit_course")
def edit_course():
    data = request.json
    course_id = data.get("course_id")
    title = data.get("title")
    description = data.get("description")

    EDIT_COURSE = "UPDATE courses SET title = %s, description = %s WHERE course_id = %s;"

    # Validate input
    if not (course_id and title and description):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(EDIT_COURSE, (title, description, course_id))
        con.commit()
    return jsonify(message="Course edited successfully."), 200


#API for adding a lesson
@app.post("/api/add_lesson")
def add_lesson():
    data = request.json
    course_id = data.get("course_id")
    title = data.get("title")
    content = data.get("content")
    type_str = data.get("type")

    INSERT_LESSON = "INSERT INTO lessons (course_id, title, content, type) VALUES (%s, %s, %s, %s);"

    # Validate input
    if not (course_id and title and content and type_str):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert user into the database
    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_LESSON, (course_id, title, content, type_str))
        con.commit()
    return jsonify(message="Lesson added successfully."), 200

#API for deleting a lesson
@app.post("/api/delete_lesson")
def delete_lesson():
    data = request.json
    lesson_id = data.get("lesson_id")

    DELETE_LESSON = "DELETE FROM lessons WHERE lesson_id = %s;"

    # Validate input
    if not lesson_id:
        return jsonify({"error": "Missing required fields"}), 400

    # Use the database connection
    with con:
        with con.cursor() as cursor:
            cursor.execute(DELETE_LESSON, (lesson_id,))
        con.commit()
    return jsonify(message="Lesson deleted successfully."), 200


#API for editing a lesson
@app.post("/api/edit_lesson")
def edit_lesson():
    data = request.json
    lesson_id = data.get("lesson_id")
    course_id = data.get("course_id")
    title = data.get("title")
    content = data.get("content")
    type_str = data.get("type")

    EDIT_LESSON = "UPDATE lessons SET course_id = %s, title = %s, content = %s, type = %s WHERE lesson_id = %s;"

    # Validate input
    if not (lesson_id and course_id and title and content and type_str):
        return jsonify({"error": "Missing required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(EDIT_LESSON, (course_id, title, content, type_str, lesson_id))
        con.commit()
    return jsonify(message="Lesson edited successfully."), 200



#Get a specific course by course_id
@app.get("/api/get_course/<course_id>")
def get_course(course_id):
    GET_COURSE = "SELECT course_id, title, description FROM courses WHERE course_id = %s;"
    
    try:
        with con:
            with con.cursor() as cursor:
                cursor.execute(GET_COURSE, (course_id,))  # Ensure course_id is passed as a tuple
                course = cursor.fetchone()  # Fetches the first row of a query result or None if no result
                
                if course:
                    # Map the database row to a dictionary
                    course_dict = {
                        "course_id": course[0],
                        "title": course[1],
                        "description": course[2]
                    }
                    return jsonify(course_dict), 200  # Return the course as a JSON response with status code 200
                else:
                    return jsonify({"error": "Course not found"}), 404  # Return an error message if no course is found
    except Exception as e:
        return jsonify({"error": str(e)}), 500



### Quizzes
#Create quizzes
@app.post("/api/create_quiz")
def add_quiz():
    data = request.json
    course_id = data.get("course_id")
    title = data.get("title")
    description = data.get("description")

    INSERT_QUIZ = "INSERT INTO quizzes (course_id, title, description) VALUES (%s, %s, %s);"

    if not (course_id and title and description):
        return jsonify({"error": "Missing required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_QUIZ, (course_id, title, description))
        con.commit()
    return jsonify(message="Quiz added successfully."), 200

#Get a specific quiz by quiz_id
@app.get("/api/get_quiz_details/<quiz_id>")
def get_quiz(quiz_id):
    GET_QUIZ = "SELECT quiz_id, title, description FROM quizzes WHERE quiz_id = %s;"
    
    try:
        with con:
            with con.cursor() as cursor:
                cursor.execute(GET_QUIZ, (quiz_id,))  # Ensure quiz_id is passed as a tuple
                quiz = cursor.fetchone()  # Fetches the first row of a query result or None if no result
                
                if quiz:
                    # Map the database row to a dictionary
                    quiz_dict = {
                        "quiz_id": quiz[0],
                        "title": quiz[1],
                        "description": quiz[2]
                    }
                    return jsonify(quiz_dict), 200  # Return the quiz as a JSON response with status code 200
                else:
                    return jsonify({"error": "Quiz not found"}), 404  # Return an error message if no quiz is found
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Editing a quiz
@app.post("/api/edit_quiz")
def edit_quiz():
    data = request.json
    quiz_id = data.get("quiz_id")
    title = data.get("title")
    description = data.get("description")

    EDIT_QUIZ = "UPDATE quizzes SET title = %s, description = %s WHERE quiz_id = %s;"

    if not (quiz_id and title and description):
        return jsonify({"error": "Missing required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(EDIT_QUIZ, (title, description, quiz_id))
        con.commit()
    return jsonify(message="Quiz edited successfully."), 200


#Deleting a quiz
@app.post("/api/delete_quiz")
def delete_quiz():
    data = request.json
    quiz_id = data.get("quiz_id")

    DELETE_QUIZ = "DELETE FROM quizzes WHERE quiz_id = %s;"

    if not quiz_id:
        return jsonify({"error": "Missing required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(DELETE_QUIZ, (quiz_id,))
        con.commit()
    return jsonify(message="Quiz deleted successfully."), 200



#Create questions
@app.post("/api/add_question")
def add_question():
    data = request.json
    quiz_id = data.get("quiz_id")
    question_text = data.get("question_text")
    options = data.get("options")  # Array of options
    correct_answer = data.get("correct_answer")  # Index of the correct option

    INSERT_QUESTION = "INSERT INTO questions (quiz_id, question_text, options, correct_answer) VALUES (%s, %s, %s, %s);"

    if not (quiz_id and question_text and options and isinstance(correct_answer, int)):
        return jsonify({"error": "Missing or invalid required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(INSERT_QUESTION, (quiz_id, question_text, options, correct_answer))
        con.commit()
    return jsonify(message="Question added successfully."), 200

#Editing a question
@app.post("/api/edit_question")
def edit_question():
    data = request.json
    question_id = data.get("question_id")
    question_text = data.get("question_text")
    options = data.get("options")  # Array of options
    correct_answer = data.get("correct_answer")  # Index of the correct option

    EDIT_QUESTION = "UPDATE questions SET question_text = %s, options = %s, correct_answer = %s WHERE question_id = %s;"

    if not (question_id and question_text and options and isinstance(correct_answer, int)):
        return jsonify({"error": "Missing or invalid required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(EDIT_QUESTION, (question_text, options, correct_answer, question_id))
        con.commit()
    return jsonify(message="Question edited successfully."), 200

#Deleting a question
@app.post("/api/delete_question")
def delete_question():
    data = request.json
    question_id = data.get("question_id")

    DELETE_QUESTION = "DELETE FROM questions WHERE question_id = %s;"

    if not question_id:
        return jsonify({"error": "Missing required fields"}), 400

    with con:
        with con.cursor() as cursor:
            cursor.execute(DELETE_QUESTION, (question_id,))
        con.commit()
    return jsonify(message="Question deleted successfully."), 200


#Get Quizzes for a course and store in a list
@app.get("/api/get_quizzes/<course_id>")
def get_quizzes(course_id):
    GET_QUIZZES = "SELECT quiz_id, title, description FROM quizzes WHERE course_id = %s;"
    
    quizzes = []

    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_QUIZZES, (course_id,))
            list_quiz  = cursor.fetchall()
            for quiz in list_quiz:
                quiz_dict = {
                    "quiz_id": quiz[0],
                    "title": quiz[1],
                    "description": quiz[2]
                }
                quizzes.append(quiz_dict)
            
    return jsonify(quizzes), 200

#Get Questions for a quiz and store in a list
@app.get("/api/get_questions/<quiz_id>")
def get_questions(quiz_id):
    GET_QUESTIONS = """
    SELECT question_id, question_text, options, correct_answer 
    FROM questions 
    WHERE quiz_id = %s;
    """
    
    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_QUESTIONS, (quiz_id,))
            questions = cursor.fetchall()
            
            question_list = [
                {
                    "question_id": q[0],
                    "question_text": q[1],
                    "options": q[2],
                    "correct_answer": q[3]
                } 
                for q in questions
            ]
            
    return jsonify(question_list), 200

#API for submitting answers
@app.post("/api/submit_answers")
def submit_answers():
    data = request.json
    quiz_id = data['quiz_id']
    student_id = data['student_id']
    answers = data['answers']

    GET_CORRECT_ANSWERS = """
    SELECT question_id, correct_answer 
    FROM questions 
    WHERE quiz_id = %s;
    """

    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_CORRECT_ANSWERS, (quiz_id,))
            correct_answers = cursor.fetchall()
            
            score = 0
            for question_id, correct_answer in correct_answers:
                if answers.get(str(question_id)) == correct_answer:
                    score += 1
            
            # Save the score to the database
            SAVE_SCORE = """
            INSERT INTO quiz_scores (student_id, quiz_id, score) 
            VALUES (%s, %s, %s);
            """
            cursor.execute(SAVE_SCORE, (student_id, quiz_id, score))
    
    return jsonify({"score": score}), 200

#Get question answers from a quiz and store in a list
@app.get("/api/get_quiz_answers/<quiz_id>")
def get_quiz_answers(quiz_id):
    GET_QUESTIONS = """
    SELECT question_id, question_text, options, correct_answer 
    FROM questions 
    WHERE quiz_id = %s;
    """
    
    with con:
        with con.cursor() as cursor:
            cursor.execute(GET_QUESTIONS, (quiz_id,))
            questions = cursor.fetchall()
            
            question_list = [
                {
                    "question_id": q[0],
                    "question_text": q[1],
                    "options": q[2],
                    "correct_answer": q[3]
                } 
                for q in questions
            ]
            
    return jsonify(question_list), 200




# Get the highest quiz scores for a student
@app.get("/api/get_quiz_scores/<student_id>")
def get_quiz_scores(student_id):
    GET_HIGHEST_SCORES = """
        SELECT q.quiz_id, q.title, MAX(qs.score) as highest_score
        FROM quiz_scores qs
        JOIN Quizzes q ON qs.quiz_id = q.quiz_id
        WHERE qs.student_id = %s
        GROUP BY q.quiz_id, q.title
    """
    
    scores = []
    try:
        with con:
            with con.cursor() as cursor:
                cursor.execute(GET_HIGHEST_SCORES, (student_id,))
                list_score = cursor.fetchall()
                for score in list_score:
                    score_dict = {
                        "quiz_id": score[0],
                        "quiz_title": score[1],
                        "score": score[2]
                    }
                    scores.append(score_dict)
        return jsonify(scores), 200
    except psycopg2.Error as e:
        con.rollback()
        print(f"Database error occurred: {e}")
        return jsonify({"error": "An error occurred while fetching quiz scores"}), 500


@app.get("/api/user_details/<student_id>")
def user_details(student_id):
    try:
        # Fetch user details
        GET_USER = "SELECT student_id, fname, lname, email FROM users WHERE student_id = %s;"
        with con.cursor() as cursor:
            cursor.execute(GET_USER, (student_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found"}), 404
            user_dict = {
                "student_id": user[0],
                "fname": user[1],
                "lname": user[2],
                "email": user[3]
            }

        # Fetch course progress
        GET_COMPLETED_LESSONS = """
        SELECT l.course_id, c.title, COUNT(l.lesson_id) as total_lessons,
        COUNT(up.lesson_id) as completed_lessons
        FROM Lessons l
        LEFT JOIN User_Progress up ON l.lesson_id = up.lesson_id AND up.student_id = %s AND up.status = 'Completed'
        JOIN Courses c ON l.course_id = c.course_id
        GROUP BY l.course_id, c.title;
        """
        with con.cursor() as cursor:
            cursor.execute(GET_COMPLETED_LESSONS, (student_id,))
            progress = cursor.fetchall()

        progress_result = [{
            "course_id": row[0],
            "title": row[1],
            "total_lessons": row[2],
            "completed_lessons": row[3],
            "percentage": (row[3] / row[2]) * 100 if row[2] > 0 else 0
        } for row in progress]

        # Fetch quiz scores
        GET_HIGHEST_SCORES = """
        SELECT q.quiz_id, q.title, MAX(qs.score) as highest_score
        FROM quiz_scores qs
        JOIN Quizzes q ON qs.quiz_id = q.quiz_id
        WHERE qs.student_id = %s
        GROUP BY q.quiz_id, q.title
        """
        with con.cursor() as cursor:
            cursor.execute(GET_HIGHEST_SCORES, (student_id,))
            scores = cursor.fetchall()
        
        scores_result = [{
            "quiz_id": row[0],
            "quiz_title": row[1],
            "score": row[2]
        } for row in scores]

        return jsonify({
            "user": user_dict,
            "progress": progress_result,
            "scores": scores_result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)