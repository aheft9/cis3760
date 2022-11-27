import os
import psycopg2
import psycopg2.extras

from datetime import time

from flask import Flask, jsonify, json, request

# api config
ENV = os.environ.get('FLASK_ENV', 'production')
PORT = int(os.environ.get('PORT', 3001))
API_PREFIX = '/api' if ENV == 'development' else ''

# db config
DB_HOST = 'db' if ENV == 'development' else 'postgres'
DB_USER = 'postgres'
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_DATABASE = 'scheduler'
DB_PORT = 5432

app = Flask(__name__)

def connect_db():
    return psycopg2.connect(database=DB_DATABASE,
                        host=DB_HOST,
                        user=DB_USER,
                        password=DB_PASS,
                        port=DB_PORT)

@app.get(API_PREFIX + "/search")
def get_search():
    args = request.args
    query = args.get('q')
    sem = args.get('sem').upper()

    if len(query) == 0:
        return jsonify([])

    res = search(query, sem,["Fri"],[[time(8,30,00),time(10,00,00)]],[True,True,True,True,True,False])
    return json.dumps(res, indent=4, sort_keys=True, default=str)

def search(search_terms, semester,days,times,courseLevel):
    db_conn = connect_db()
    cursor = db_conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    semester = semester.upper()

    selects = []
    params = []
    queries = search_terms.split(";")

    cLevel = ""
    if courseLevel[0]:
        cLevel = "AND ("
        if courseLevel[1]:
            if cLevel != "AND (":
                cLevel = cLevel + " OR "
            cLevel = cLevel + "LEFT(course_code, 1) = '1' "
        if courseLevel[2]:
            if cLevel != "AND (":
                cLevel = cLevel + " OR "
            cLevel = cLevel + "LEFT(course_code, 1) = '2' "
        if courseLevel[3]:
            if cLevel != "AND (":
                cLevel = cLevel + " OR "
            cLevel = cLevel + "LEFT(course_code, 1) = '3' "
        if courseLevel[4]:
            if cLevel != "AND (":
                cLevel = cLevel + " OR "
            cLevel = cLevel + "LEFT(course_code, 1) = '4' OR LEFT(course_code, 1) = '5' "
        if courseLevel[5]:
            if cLevel != "AND (":
                cLevel = cLevel + " OR "
            cLevel = cLevel + "LEFT(course_code, 1) = '6' OR LEFT(course_code, 1) = '7' OR LEFT(course_code, 1) = '8'"
        cLevel = cLevel + ")"
    
    # select sections
    for query in queries:
        query_selects = []

        if query.strip() == "":
            continue

        # perform query for each search term
        query = query.replace("*", " ")
        query = query.upper()
        terms = query.split()
        for term in terms:
            if term.strip() == "":
                continue

            query_selects.append("(SELECT * FROM sections "
                   "WHERE ((department || course_code) LIKE %s "
                   "OR UPPER(course_name) LIKE %s "
                   "OR UPPER(faculty) LIKE %s) "
                   "AND sem = %s "
                   "%s"
                   ")")
            params.extend([f'%{term}%', f'%{term}%', f'%{term}%', semester,cLevel])

        selects.append(' INTERSECT '.join(query_selects))

    # union all the selects
    cursor.execute(' UNION '.join(selects), tuple(params))
    sections = cursor.fetchall()

    # group by course and select meetings for each section found
    courses = {}
    for i in range(len(sections)):
        course_id = sections[i]['department'] + sections[i]['course_code']
        section = sections[i]

        

        # add meetings to section
        cursor.execute("SELECT * FROM meetings "
                        "WHERE section_id = %s AND sem = %s", (section['section_id'], semester))

        meetings = cursor.fetchall()
        
        validSection = True
        
        # Search the meeting days to see if it is a forbidden day or forbidden time
        for meeting in meetings:
            if meeting['meeting_type'] != "EXAM":
                meetDays = meeting['meeting_day'].split(",")
                for day in days:
                    if day in meetDays:
                        validSection = False
                        break
                if validSection:
                    for time in times:
                        if not meeting['start_time'] is None:
                            if time[0] <= meeting['start_time'] < time[1] or time[0] < meeting['end_time'] <= time[1]:
                                validSection = False
                                break  
                else:
                    break
                          


        if validSection:
            if course_id not in courses:
                courses[course_id] = {
                    'id': len(courses) + 1,
                    'course': sections[i]['department'] + sections[i]['course_code'],
                    'department': sections[i]['department'],
                    'course_code': sections[i]['course_code'],
                    'course_name': sections[i]['course_name'],
                    'academic_level': sections[i]['academic_level'],
                    'credits': sections[i]['credits'],
                    'sections': []
                }
            
            section['meetings'] = meetings
            courses[course_id]['sections'].append(section)




    db_conn.commit()
    db_conn.close()
    return list(courses.values())

@app.get(API_PREFIX + "/semesters")
def get_semesters():
    db_conn = connect_db()
    cursor = db_conn.cursor()

    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()
    db_conn.commit()

    response = []
    for data in semesters:
        response.append({
            "sem": data[0],
            "name": data[1]
        })

    # sort response by year then semester (winter, summer, fall)
    alpha = 'WSF'
    response.sort(key=lambda x: (x['sem'][1:], alpha.index(x['sem'][0])))

    db_conn.commit()
    db_conn.close()
    return jsonify(response)

@app.get(API_PREFIX + "/departments")
def get_departments():
    db_conn = connect_db()
    cursor = db_conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT department FROM sections GROUP BY department")
    departments = cursor.fetchall()

    out = []
    for department in departments:
        out.append(department['department'])

    db_conn.commit()
    db_conn.close()

    return jsonify(out)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=PORT)
