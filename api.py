from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

conn = sqlite3.connect('database.db')
conn.execute("DROP TABLE posts")
conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, journal TEXT, user TEXT, sentiment_score INTEGER, sentiment_magnitude INTEGER, sleep INTEGER, wake INTEGER)")


@app.route('/makeJournal', methods = ['POST'])
def makeJournal():
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
    command = "INSERT INTO posts (journal,user,sentiment_score,sentiment_magnitude,sleep,wake) VALUES (\"" + journal +"\",\"" + user + "\"," + str(sentiment_score) + "," str(sentiment_magnitude) + "," + str(sleep) + "," + str(wake) +")"
    cursor.execute(command)
    conn.commit()
    return command

#based on date range
@app.route('/getJournal', methods = ['GET'])
def getJournal():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return jsonify(cursor.execute("SELECT * FROM posts LIMIT 10").fetchall())

@app.route('/updateJournal', methods = ['POST'])
def updateJournal():
    result = request.json
    journal = request.json["journal"]
    sentiment = 0
    sleep = 0
    wake = 0
    conn = sqlite3.connect('database.db')
    conn.execute("UPDATE posts SET journal = %s, sentiment = %d, sleep = %d, wake = %d WHERE journal = %s" %(journal,sentiment,sleep,wake))

if __name__ == '__main__':
   #app.EXPLAIN_TEMPLATE_LOADING = True
   app.run(debug = True)
