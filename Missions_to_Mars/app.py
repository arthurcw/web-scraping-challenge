from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import scrape_mars

# Create an instance of Flask
app = Flask(__name__)

# Use PyMongo to establish Mongo connection
mongo = PyMongo(app, uri='mongodb://localhost:27017/mars_db')


@app.route("/")
def index():
    mars_data = mongo.db.scrape.find_one_or_404()
    return render_template("index.html", mars=mars_data)


@app.route("/scrape")
def scraper():
    # Scrap data from web
    data = scrape_mars.scrape()

    # Insert data into MongoDB
    mongo.db.scrape.update({}, data, upsert=True)
    
    return redirect("/", code=302)


if __name__ == "__main__":
    app.run(debug=True)
