from flask import Flask, request, make_response
import logging
from worker import process_main
from threading import Thread

# start flask application
app = Flask(__name__)


@app.route('/hello', methods=['GET'])
def hello():
    return "Hello World."

@app.route('/stable-patient', methods=['POST'])
def onStablePatient():
    data = request.get_json(force=True)
    thread = Thread(target=process_main, kwargs={'data': data})
    thread.start()
    return make_response({"status": "accepted"})
