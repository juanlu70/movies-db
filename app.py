import os
import sqlite3
import pandas as pd
# import matplotlib
# matplotlib.use('Agg')

from flask import Flask, send_file, make_response

import csv
import io

app = Flask(__name__)

movies = [
    {'title': 'Movie 1', 'release_year': 2018},
    {'title': 'Movie 2', 'release_year': 2019},
    {'title': 'Movie 3', 'release_year': 2019},
    {'title': 'Movie 4', 'release_year': 2020},
    {'title': 'Movie 5', 'release_year': 2020},
    {'title': 'Movie 6', 'release_year': 2021},
]


# -- open sqlite3 file database by name --
def open_db(filename: str):
    path = os.path.dirname(__file__)
    sql_file = os.path.join(path, filename)
    bbdd = sqlite3.connect(sql_file)
    bbdd.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
    sql = bbdd.cursor()

    return sql, bbdd


def generate_movie_release_chart(movies):
    # Count the number of movies released each year
    df = pd.DataFrame(movies)
    

    # Prepare data for the bar chart

    # Generate the bar chart
    
    # Customize the chart

    # Optionally, rotate x-axis labels if needed
    plt.xticks(rotation=45)

    # Save the chart to a file instead of showing it
    plt.savefig('chart.png')
    plt.close()


@app.route('/draw-chart')
def graph_endpoint():
    generate_movie_release_chart(movies)

    # Return the generated chart as a file download
    return send_file('chart.png', mimetype='image/png')


@app.route('/load-data')
def load_data_endpoint():
    # Your load_data_endpoint endpoint logic here
    csv_list = []
    with open("movies.csv", "r") as fp:
        reader = csv.DictReader(fp)
        for item in reader:
            csv_list.append(item)
        fp.close()

    # -- get year in a sparated column, discard films without year --
    movies = []
    for item in csv_list:
        brackets = item['title'].count('(')
        if brackets > 0:
            line = {'title': '', 'release_year': ''}
            parts = item['title'].split(" (")
            if len(parts) == 2:
                line['title'] = parts[0]
                line['release_year'] = parts[1][:-1]
            if len(parts) == 3:
                line['title'] = parts[0]+" ("+parts[1]
                line['release_year'] = parts[2][:-1]
            print(line)
            movies.append(line)

    # -- add movies to database --
    sql, bbdd = open_db("database.db")

    for row in movies:
        sql.execute("INSERT INTO movies (title, release_year) VALUES (?, ?);", (row['title'],
                                                                                row['release_year']))
    bbdd.commit()

    return 'load_data_endpoint endpoint'


@app.route('/export-data')
def export_data():
    # Set the response headers to indicate a CSV file download
    headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=movies.csv'
    }

    # Create a temporary in-memory file to write the CSV data
    temp_file = io.StringIO("movies.csv")
    writer = csv.DictWriter(temp_file, fieldnames=['title', 'release_year'])

    # Write the CSV header
    writer.writeheader()

    # Write each movie as a CSV row
    for movie in movies:
        writer.writerow(movie)

    # Move the file pointer to the beginning of the file
    temp_file.seek(0)
    temp_file.close()

    # Create a Flask response with the CSV file
    my_response = make_response(send_file("movies.csv"))
    my_response.mimetype('text/csv')

    # Close the in-memory file
    temp_file.close()

    # Return the response
    return my_response
