from flask import Flask, render_template
from utility import page_description

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html",description=page_description)


if __name__=="__main__":
    app.run(debug=True)