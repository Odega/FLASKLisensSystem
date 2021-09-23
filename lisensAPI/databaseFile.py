import pymysql
#import paramiko
#import sshtunnel
from flask import current_app

# Database SETUP


def Database(qry):
    # print("Database() entering qry=", qry)
    try:
        mydb = pymysql.connect(
            host=current_app.config['MYSQL_DATABASE_HOST'],
            user=current_app.config['MYSQL_DATABASE_USER'],
            password=current_app.config['MYSQL_DATABASE_PASSWORD'],
            database=current_app.config['MYSQL_DATABASE_DATABASE'],
        )
        print("pymysql - connected")
        mycursor = mydb.cursor()
        sql_query = qry
        mycursor.execute(sql_query)
        print("Query executed..")
        result = mycursor.fetchall()
        print("Fetchall complete..")
        description = mycursor.description
        return result
    except pymysql.Error as err:
        print("Noe gikk galt")
        print(err)
    finally:
        mycursor.close()
        mydb.close()
        print("CLOSED")

# Get Courses
def getStudentCourses(skoleId):
    # print("Database() entering qry=", qry)
    query = "SELECT ci as courseId, ad as activationDate, vt as validTo FROM(SELECT a.courseId as ci, a.activationDate as ad, a.validTo as vt, a.createdDate as cd, a.id as id FROM api.lisenser as a INNER JOIN (SELECT MAX(id)as id, courseId, activationDate, validTo, MAX(createdDate) as createdDate FROM api.lisenser WHERE orgNr = {} GROUP BY courseId) b ON a.courseId = b.courseId AND a.createdDate = b.createdDate AND a.id = b.id) as c;".format(
        skoleId
    )
    try:
        mydb = pymysql.connect(
            host=current_app.config['MYSQL_DATABASE_HOST'],
            user=current_app.config['MYSQL_DATABASE_USER'],
            password=current_app.config['MYSQL_DATABASE_PASSWORD'],
            database=current_app.config['MYSQL_DATABASE_DATABASE'],
            cursorclass=pymysql.cursors.DictCursor,
        )
        print("pymysql - connected - api")
        mycursor = mydb.cursor()
        sql_query = query
        mycursor.execute(sql_query)
        print("Query executed.. - api")
        result = mycursor.fetchall()
        print("Fetchall complete.. - api")
        print(result)
        return result
    except pymysql.Error as err:
        print("Noe gikk galt - api")
        print(err)
    finally:
        mycursor.close()
        mydb.close()
        print("CLOSED")


# Add To Database
def addDatabase(qry):
    startQuery = "INSERT INTO lisenser (orgNr, kommune, skoleNavn, LMnavn, courseId, activationDate, validTo, signatur, createdDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    backupQuery = "INSERT INTO lisenser_backup (orgNr, kommune, skoleNavn, LMnavn, courseId, activationDate, validTo, signatur, createdDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    # print("Database() entering qry=", qry)
    try:
        mydb = pymysql.connect(
            host=current_app.config['MYSQL_DATABASE_HOST'],
            user=current_app.config['MYSQL_DATABASE_USER'],
            password=current_app.config['MYSQL_DATABASE_PASSWORD'],
            database=current_app.config['MYSQL_DATABASE_DATABASE'],
        )
        #print("pymysql - connected")
        mycursor = mydb.cursor()

        toInsert = qry
        mycursor.executemany(startQuery, toInsert)
        #print("Query executed..")

        mydb.commit()
        print(mycursor.rowcount,
                "Record inserted successfully into lisenser table")

        print("Backup table insertion")
        toInsertBackup = qry
        mycursor.executemany(backupQuery, toInsertBackup)
        mydb.commit()
        print(mycursor.rowcount,
                "Record inserted successfully into backup")

        return None
    except pymysql.Error as err:
        print("Noe gikk galt")
        print("Failed to insert record into MySQL table {}".format(err))
    finally:
        mycursor.close()
        mydb.close()
        print("mydb CLOSED")
