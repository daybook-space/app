from flask import Flask, request, jsonify
import sqlite3

from ml.daybookml.analysis import analyze_journal
from ml.daybookml.summary import top_emotion_effectors

import threading

app = Flask(__name__)

conn = sqlite3.connect('database.db')
#conn.execute("DROP TABLE posts")
#conn.execute("DROP TABLE sentiments")
conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, journal TEXT, user TEXT, sentiment DECIMAL, sleep INTEGER, wake INTEGER, sleepTime INTEGER)")
#"category" below refer to event, people, location, other
conn.execute("CREATE TABLE sentiments (id INTEGER, category TEXT, word TEXT, sentiment DECIMAL, sentiment_magnitude DECIMAL)")

def run_sentiment(journal_text, journal_id):
    print("[INFO] running sentiment")
    sentiment, entity_dict = analyze_journal(journal_text)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"UPDATE posts SET sentiment = {sentiment} WHERE id = {journal_id}"
    cursor.execute(command)

    for category in entity_dict:
        for entity in entity_dict[category]:
            command = f"INSERT INTO sentiments (id, category, word, sentiment_score, sentiment_magnitude) VALUES ({journal_id}, \"{category}\", \"{entity[0]}\", {entity[1]}, {entity[2]})"
            cursor.execute(sentimentCommand)

    conn.commit()

    print(f"[INFO] Done running sentiment for journal {journal_id}")

def makeJournal(result):
    journal = result["journal"]
    user = result["user"]
    sentiment = 0 # We'll spawn a thread to fix this soon.
    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = "INSERT INTO posts (journal, user, sentiment, sleep, wake, sleepTime) VALUES (\"%s\",\"%s\",%d,%d,%d,%d,%d)" %(journal, user, sentiment, sleep, wake, sleepTime)
    cursor.execute(command)
    journal_id = cursor.lastrowid
    conn.commit()

    sent_thr = threading.Thread(target=run_sentiment, args=(result["journal"], journal_id,))
    sent_thr.start()
    return jsonify(journal_id)

def updateJournal():
    journal_id = result["id"]
    journal = result["journal"]
    user = result["user"]

    # sanity check!
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"SELECT EXISTS(SELECT 1 FROM posts WHERE id = {journal_id}, user = \"{user}\");"
    if not cursor.execute(command):
        return jsonify("Invalid id/user pair")

    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)
    try:
        command = f"UPDATE posts SET journal = \"{journal}\", sleep = {sleep}, wake = {wake}, sleepTime = {sleepTime} WHERE id = {journal_id}"
        cursor.execute(command)

        command = f"DELETE FROM sentiments WHERE id = {journal_id}"
        cursor.execute(command)
        conn.commit()

        sent_thr = threading.Thread(target=run_sentiment, args=(result["journal"], journal_id,))
        sent_thr.start()
        return jsonify(0)
    except:
        return jsonify(-1)

@app.route('/updateJournal', methods = ['POST'])
def _make_update_journal():
    result = request.json
    if result['id'] == 0:
        return makeJournal(request)
    else:
        return updateJournal(request)

#based on date range
@app.route('/getJournal', methods = ['GET'])
def getJournal():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return jsonify(cursor.execute("SELECT * FROM sentiments LIMIT 10").fetchall())

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
