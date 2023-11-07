import os
import sqlite3
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')

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
    data = df.groupby(by='release_year').agg({'release_year': 'count'})

    # Prepare data for the bar chart
    data.rename(columns={'release_year': 'movies'}, inplace=True)
    data.reset_index(drop=True)
    data['year'] = data.index
    data['year'] = pd.to_numeric(data['year'])

    # Generate the bar chart
    plt.figure(figsize=(16, 12), dpi=80)
    plt.title("Movies by year")
    plt.xlabel("Years")
    plt.ylabel("Number of movies")

    # Customize the chart
    plt.bar(data['year'], data['movies'], linewidth=2)
    plt.grid(True)

    # Optionally, rotate x-axis labels if needed
    plt.xticks(rotation=45)

    # Save the chart to a file instead of showing it
    plt.savefig('chart.png')
    plt.close()

    return


@app.route('/draw-chart')
def graph_endpoint():
    sql, bbdd = open_db("database.db")
    query = "SELECT * FROM movies;"
    sql.execute(query)
    movies = sql.fetchall()
    generate_movie_release_chart(movies)

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
            save = 1
            line = {'title': '', 'release_year': ''}
            parts = item['title'].split(" (")
            if len(parts) == 2:
                line['title'] = parts[0]
                line['release_year'] = parts[1][:-1].replace(")", "")
            if len(parts) == 3:
                line['title'] = parts[0]+" ("+parts[1]
                line['release_year'] = parts[2][:-1].replace(")", "")
            if len(line['release_year']) == 4:
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
    my_response.headers['Content-Type'] = headers['Content-Type']

    # Close the in-memory file
    temp_file.close()

    # Return the response
    return my_response
