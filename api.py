from flask import Flask, request, jsonify
import sqlite3

from datetime import datetime

from ml.daybookml.analysis import analyze_journal
from ml.daybookml.summary import top_emotion_effectors

import threading

app = Flask(__name__)

conn = sqlite3.connect('database.db')
try:
    conn.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, journal TEXT, user TEXT, sentiment DECIMAL, sleep INTEGER, wake INTEGER, sleepTime INTEGER, day timestamp)")
    #"category" below refer to event, people, location, other
    conn.execute("CREATE TABLE IF NOT EXISTS sentiments (id INTEGER, category TEXT, word TEXT, sentiment_score DECIMAL, sentiment_magnitude DECIMAL)")
except:
    pass

def run_sentiment(journal_text, journal_id):
    print("[INFO] running sentiment")
    sentiment, entity_dict = analyze_journal(journal_text)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"UPDATE posts SET sentiment = {sentiment} WHERE id = {journal_id}"
    cursor.execute(command)

    command = f"DELETE FROM sentiments WHERE id = {journal_id}"
    cursor.execute(command)

    for category in entity_dict:
        for entity in entity_dict[category]:
            command = f"INSERT INTO sentiments (id, category, word, sentiment_score, sentiment_magnitude) VALUES ({journal_id}, \"{category}\", \"{entity[0]}\", {entity[1]}, {entity[2]})"
            cursor.execute(command)

    conn.commit()

    print(f"[INFO] Done running sentiment for journal {journal_id}")

def makeJournal(result):
    journal = result["journal"]
    user = result["user"]
    day = datetime.now().strftime("%Y-%m-%d")
    sentiment = 0 # We'll spawn a thread to fix this soon.
    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = "INSERT INTO posts (journal, user, sentiment, sleep, wake, sleepTime, day) VALUES (\"%s\",\"%s\",%d,%d,%d,%d,\"%s\")" %(journal, user, sentiment, sleep, wake, sleepTime, day)
    cursor.execute(command)
    journal_id = cursor.lastrowid
    conn.commit()

    sent_thr = threading.Thread(target=run_sentiment, args=(result["journal"], journal_id,))
    sent_thr.start()
    return jsonify(journal_id)

class UserMismatch403(Exception):
    pass

@app.errorhandler(UserMismatch403)
def special_page_not_found(error):
    return "Username and Journal ID do not match, or journal does not exist!", 403

def updateJournal(journal_id, result):
    journal = result["journal"]
    user = result["user"]

    # sanity check!
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"SELECT EXISTS(SELECT 1 FROM posts WHERE id = {journal_id} AND user = \"{user}\");"
    if not cursor.execute(command).fetchall()[0][0]:
        #return jsonify("Invalid id/user pair")
        raise UserMismatch403

    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)
    try:
        command = f"UPDATE posts SET journal = \"{journal}\", sleep = {sleep}, wake = {wake}, sleepTime = {sleepTime} WHERE id = {journal_id}"
        cursor.execute(command)
        conn.commit()

        sent_thr = threading.Thread(target=run_sentiment, args=(result["journal"], journal_id,))
        sent_thr.start()
        return jsonify(0)
    except:
        return jsonify(-1)

#date formats should be YYYY-MM-DD
@app.route('/getJournal/<startDate>/<endDate>', methods = ['GET'])
def getJournalDateRange(startDate, endDate):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return jsonify(cursor.execute(f"SELECT * FROM posts WHERE day BETWEEN \'{startDate}\' and \'{endDate}\'").fetchall())

@app.route('/updateJournal/<journal_id>', methods = ['POST'])
def _make_update_journal(journal_id):
    journal_id = int(journal_id)
    result = request.json
    if journal_id == 0:
        return makeJournal(result)
    else:
        return updateJournal(journal_id, result)

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
