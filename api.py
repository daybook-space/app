from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

conn = sqlite3.connect('database.db')
#conn.execute("DROP TABLE posts")
#conn.execute("DROP TABLE sentiments")
conn.execute("CREATE TABLE posts (Id INTEGER PRIMARY KEY AUTOINCREMENT, journal TEXT, user TEXT, sentiment_score DECIMAL, sentiment_magnitude DECIMAL, sleep INTEGER, wake INTEGER, sleepTime INTEGER)")
#"category" below refer to event, people, location, other
conn.execute("CREATE TABLE sentiments (Id INTEGER, category TEXT, word TEXT, sentiment_score DECIMAL, sentiment_magnitude DECIMAL)")

@app.route('/makeJournal', methods = ['POST'])
def makeJournal():
    result = request.json
    journal = result["journal"]
    user = result["user"]
    sentiment_score = result["sentiment_score"]
    sentiment_magnitude = result["sentiment_magnitude"]
    sentiment = analysis
    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = "INSERT INTO posts (journal, user, sentiment_score, sentiment_magnitude, sleep, wake, sleepTime) VALUES (\"%s\",\"%s\",%d,%d,%d,%d,%d)" %(journal,user,sentiment_score,sentiment_magnitude,sleep,wake,sleepTime)
    cursor.execute(command)
    Id = result["Id"]
    category = result["category"]
    word = result["word"]
    sentimentCommand = "INSERT INTO sentiments (Id, category, word, sentiment_score, sentiment_magnitude) VALUES (%d,\"%s\",\"%s\",%f,%f)" %(Id, category, word, sentiment_score, sentiment_magnitude)
    cursor.execute(sentimentCommand)
    lastId = cursor.lastrowid
    conn.commit()
    return sentimentCommand

#based on date range
@app.route('/getJournal', methods = ['GET'])
def getJournal():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return jsonify(cursor.execute("SELECT * FROM sentiments LIMIT 10").fetchall())

@app.route('/updateJournal', methods = ['POST'])
def updateJournal():
    result = request.json
    journal = result["journal"]
    user = result["user"]
    sentiment_score = 0
    sentiment_magnitude = 0
    #sentiment = analysis
    sleep = result["sleep"]
    wake = result["wake"]
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = "UPDATE posts (journal, user, sentiment_score, sentiment_magnitude, sleep, wake) VALUES (\"%s\",\"%s\",%d,%d,%d,%d)" %(journal,user,sentiment_score,sentiment_magnitude,sleep,wake)
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
    return (totalSleep / 100)

if __name__ == '__main__':
   #app.EXPLAIN_TEMPLATE_LOADING = True
   app.run(debug = True)