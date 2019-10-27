from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

from datetime import datetime

from ml.daybookml.analysis import analyze_journal
from ml.daybookml.summary import top_emotion_effectors

import threading

app = Flask(__name__)
logging.basicConfig(filename='../daybook.log', level=logging.DEBUG)
CORS(app)

conn = sqlite3.connect('database.db')
conn.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, journal TEXT, user TEXT, sentiment DECIMAL, sleep TEXT, wake TEXT, sleepTime DECIMAL, day timestamp)")
#"category" below refer to event, people, location, other
conn.execute("CREATE TABLE IF NOT EXISTS sentiments (id INTEGER, category TEXT, word TEXT, sentiment_score DECIMAL, sentiment_magnitude DECIMAL)")

def run_sentiment(journal_text, journal_id):
    app.logger.info("running sentiment")
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

    app.logger.info(f"[INFO] Done running sentiment for journal {journal_id}")

class AlreadyExist403(Exception):
    pass

@app.errorhandler(AlreadyExist403)
def already_exist_error(error):
    return "Journal with that date already exists!", 403

def makeJournal(result):
    journal = result["journal"]
    user = result["user"]
    day = result["date"]

    # sanity check
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"SELECT EXISTS(SELECT 1 FROM posts WHERE day = \"{day}\" AND user = \"{user}\");"
    if cursor.execute(command).fetchall()[0][0]:
        raise AlreadyExist403

    sentiment = 0 # We'll spawn a thread to fix this soon.
    sleep = result["sleep"]
    wake = result["wake"]
    sleepTime = calcSleep(sleep, wake)

    command = f"INSERT INTO posts (journal, user, sentiment, sleep, wake, sleepTime, day) VALUES (\"{journal}\",\"{user}\",{sentiment},\"{sleep}\",\"{wake}\",{sleepTime},\"{day}\")"
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

    command = f"UPDATE posts SET journal = \"{journal}\", sleep = \"{sleep}\", wake = \"{wake}\", sleepTime = {sleepTime} WHERE id = {journal_id}"
    cursor.execute(command)
    conn.commit()

    sent_thr = threading.Thread(target=run_sentiment, args=(result["journal"], journal_id,))
    sent_thr.start()
    return jsonify(journal_id)

#date formats should be YYYY-MM-DD
@app.route('/getJournal/<user>/<startDate>/<endDate>', methods = ['GET'])
def getJournalDateRange(user,startDate, endDate):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    resp = cursor.execute(f"SELECT * FROM posts WHERE day BETWEEN \'{startDate}\' AND \'{endDate}\' AND user = \"{user}\" ORDER BY day DESC").fetchall()
    result = []
    elt_order = ['id', 'content', 'user', 'sentiment', 'sleepTime', 'wakeupTime', 'sleepAmount', 'date']
    for entry in resp:
        result.append({elt: entry[i] for i, elt in enumerate(elt_order) if elt != False})
    return jsonify(result)

@app.route('/getSingleJournal/<user>/<journal_id>', methods = ['GET'])
def getSingleJournal(user, journal_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"SELECT EXISTS(SELECT 1 FROM posts WHERE id = {journal_id} AND user = \"{user}\");"
    if not cursor.execute(command).fetchall()[0][0]:
        #return jsonify("Invalid id/user pair")
        raise UserMismatch403

    resp = cursor.execute(f"SELECT * FROM posts WHERE id = {journal_id} AND user = \"{user}\"").fetchall()
    elt_order = ['id', 'content', 'user', 'sentiment', 'sleepTime', 'wakeupTime', 'sleepAmount', 'date']
    return jsonify({elt: resp[0][i] for i, elt in enumerate(elt_order) if elt != False})


@app.route('/emotionEffectors/<user>/<startDate>/<endDate>', methods = ['GET'])
def getEmotionEffectors(user, startDate, endDate):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    command = f"SELECT category, word, sentiment_score, sentiment_magnitude FROM posts p INNER JOIN sentiments s WHERE p.id = s.id AND day BETWEEN \'{startDate}\' AND \'{endDate}\' AND user = \"{user}\""
    resp = cursor.execute(command).fetchall()

    entity_dict = {
        'events': [],
        'people': [],
        'locations': [],
        'other': []
    }

    for word in resp:
        entity_dict[word[0]].append((word[1], word[2], word[3]))

    processed_effectors = top_emotion_effectors(entity_dict)

    final_ret = {
        'events': {
            'happy': [],
            'sad': []
        },
        'people': {
            'happy': [],
            'sad': []
        },
        'locations': {
            'happy': [],
            'sad': []
        },
        'other': {
            'happy': [],
            'sad': []
        }
    }

    for category in processed_effectors:
        for word in processed_effectors[category]:
            if len(final_ret[category]['happy']) >= 5:
                break
            if word[1] < 0:
                break

            append_dict = {
                "entity": word[0],
                "sentiment": word[1]
            }

            final_ret[category]['happy'].append(append_dict)

        for word in list(reversed(processed_effectors[category])):
            if len(final_ret[category]['sad']) >= 5:
                break
            if word[1] >= 0:
                break

            append_dict = {
                "entity": word[0],
                "sentiment": word[1]
            }

            final_ret[category]['sad'].append(append_dict)

    return jsonify(final_ret)

@app.route('/updateJournal/<journal_id>', methods = ['POST'])
def _make_update_journal(journal_id):
    journal_id = int(journal_id)
    result = request.json
    if journal_id == 0:
        return makeJournal(result)
    else:
        return updateJournal(journal_id, result)

def calcSleep(sleep, wake):
    sleepList = sleep.split(":")
    wakeList = wake.split(":")
    sleepMin = (int(sleepList[0]) * 60) + int(sleepList[1])
    wakeMin = (int(wakeList[0]) * 60) + int(wakeList[1])
    if sleepMin == wakeMin:
        totalMin = 24 * 60
    elif sleepMin > wakeMin:
        totalMin = wakeMin + (1440 - sleepMin)
    else:
        totalMin = wakeMin - sleepMin
    totalHour = totalMin / 60
    return totalHour

if __name__ == '__main__':
   #app.EXPLAIN_TEMPLATE_LOADING = True
   app.run(host='0.0.0.0', port=5000, debug=True)
