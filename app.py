from flask import Flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)

FlaskInstrumentor.instrument_app(app)


@app.route("/")
def hello():
    return "Hello World!"


app.run(debug=True)
