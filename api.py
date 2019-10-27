from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
app = Flask(__name__)

conn = sqlite3.connect('database.db')
#conn.execute("DROP TABLE posts")
conn.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, journal TEXT, user TEXT, sentiment_score DECIMAL, sentiment_magnitude DECIMAL, sleep INTEGER, wake INTEGER, sleepTime INTEGER, day timestamp)")


@app.route('/makeJournal', methods = ['POST'])
def makeJournal():
    result = request.json
    journal = result["journal"]
    user = result["user"]
    day = datetime.now().strftime("%Y-%m-%d")
    sentiment_score = 0
    sentiment_magnitude = 0
    #sentiment = analysis
    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = "INSERT INTO posts (journal, user, sentiment_score, sentiment_magnitude, sleep, wake, sleepTime,day) VALUES (\"%s\",\"%s\",%f,%f,%d,%d,%d,\"%s\")" %(journal,user,sentiment_score,sentiment_magnitude,sleep,wake,sleepTime,day)
    cursor.execute(command)
    conn.commit()
    return command

#based on date range
@app.route('/getJournal', methods = ['GET'])
def getJournal():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return jsonify(cursor.execute("SELECT * FROM posts LIMIT 10").fetchall())

#date formats should be YYYY-MM-DD
@app.route('/getJournal/<startDate>/<endDate>', methods = ['GET'])
def getJournalDateRange(startDate, endDate):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return jsonify(cursor.execute(f"SELECT * FROM posts WHERE day BETWEEN \'{startDate}\' and \'{endDate}\'").fetchall())

@app.route('/updateJournal/<Id>', methods = ['POST'])
def updaateJournal(Id):
    result = request.json
    journal = result["journal"]
    user = result["user"]
    sentiment_score = 0
    sentiment_magnitude = 0
    #sentiment = analysis
    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = "UPDATE posts SET journal = \"%s\", user = \"%s\", sentiment_score = %f, sentiment_magnitude=%f, sleep = %d, wake = %d, sleepTime = %d WHERE id = %d" % (journal,user,sentiment_score,sentiment_magnitude,sleep,wake,sleepTime,int(Id))
    cursor.execute(command)
    conn.commit()
    return command

def calcSleep(sleep, wake):
    if sleep == wake:
        totalSleep = 24;
    elif sleep > wake:
        totalSleep = wake + (2400 - sleep)
    else:
        totalSleep = wake - sleep
    return totalSleep

if __name__ == '__main__':
   #app.EXPLAIN_TEMPLATE_LOADING = True
   app.run(debug = True)
