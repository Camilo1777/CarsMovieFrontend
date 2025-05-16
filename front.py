from flask import Flask, render_template_string, redirect, request
import requests

app = Flask(__name__)

user_movies = []

API_URL = "https://carsmoviesinventoryproject-production.up.railway.app/api/v1/carsmovies"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cars Movies Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        table { border-collapse: collapse; width: 80%; margin: auto; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #4CAF50; color: white; }
        caption { font-size: 1.5em; margin-bottom: 10px; }
        .pagination { margin: 20px auto; text-align: center; }
        .pagination a { margin: 0 5px; text-decoration: none; color: #4CAF50; }
        .pagination span { margin: 0 5px; color: #888; }
        .add-form { width: 80%; margin: 20px auto; padding: 10px; border: 1px solid #4CAF50; border-radius: 5px; }
        .add-form input { margin: 5px; padding: 5px; }
        .add-form button { padding: 5px 10px; background: #4CAF50; color: white; border: none; border-radius: 3px; }
    </style>
</head>
<body>
    <form class="add-form" method="post" action="/add">
        <label>Movie Name: <input type="text" name="carMovieName" required></label>
        <label>Year: <input type="number" name="carMovieYear" required></label>
        <label>Duration (min): <input type="number" name="duration" required></label>
        <button type="submit">Add Movie</button>
    </form>
    
    <form class="add-form" method="get" action="/buscar">
        <label>Buscar por ID: <input type="text" name="id" required></label>
        <button type="submit" style="background:#3498db;">Buscar</button>
    </form>
    <table>
        <caption>Cars Movies Dashboard</caption>
        <tr>
            <th>ID</th>
            <th>Movie Name</th>
            <th>Year</th>
            <th>Duration (min)</th>
            <th>Acción</th>
        </tr>
        {% for movie in movies %}
        <tr>
            <td>{{ movie.id }}</td>
            <td>{{ movie.carMovieName }}</td>
            <td>{{ movie.carMovieYear }}</td>
            <td>{{ movie.duration }}</td>
            <td>
                <form method="post" action="/delete" style="display:inline;">
                    <input type="hidden" name="id" value="{{ movie.id }}">
                    <button type="submit" style="background:#e74c3c;color:white;border:none;padding:4px 8px;border-radius:3px;">Eliminar</button>
                </form>
                <form method="get" action="/edit" style="display:inline;">
                    <input type="hidden" name="id" value="{{ movie.id }}">
                    <button type="submit" style="background:#f1c40f;color:black;border:none;padding:4px 8px;border-radius:3px;">Editar</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def dashboard():
    # Trae las películas de la API
    try:
        resp = requests.get(API_URL, timeout=5)
        data = resp.json()
        api_movies = data.get("Movies", [])
    except Exception:
        api_movies = []
    # Combina las locales y las de la API (locales primero)
    all_movies = user_movies + api_movies
    return render_template_string(
        TEMPLATE,
        movies=all_movies
    )

@app.route("/add", methods=["POST"])
def add_movie():
    new_movie = {
        "id": f"user-{len(user_movies)+1}",
        "carMovieName": request.form["carMovieName"],
        "carMovieYear": request.form["carMovieYear"],
        "duration": request.form["duration"]
    }
    user_movies.insert(0, new_movie)
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete_movie():
    movie_id = request.form.get("id")
    global user_movies
    user_movies = [m for m in user_movies if m["id"] != movie_id]
    return redirect("/")

@app.route("/edit", methods=["GET", "POST"])
def edit_movie():
    movie_id = request.values.get("id")
    movie = next((m for m in user_movies if m["id"] == movie_id), None)
    if not movie:
        return redirect("/")
    if request.method == "POST":
        movie["carMovieName"] = request.form["carMovieName"]
        movie["carMovieYear"] = request.form["carMovieYear"]
        movie["duration"] = request.form["duration"]
        return redirect("/")
    return f"""
    <h2>Editar Película</h2>
    <form method="post">
        <input type="hidden" name="id" value="{movie['id']}">
        <label>Movie Name: <input type="text" name="carMovieName" value="{movie['carMovieName']}" required></label><br>
        <label>Year: <input type="number" name="carMovieYear" value="{movie['carMovieYear']}" required></label><br>
        <label>Duration (min): <input type="number" name="duration" value="{movie['duration']}" required></label><br>
        <button type="submit">Guardar</button>
        <a href="/">Cancelar</a>
    </form>
    """

@app.route("/buscar")
def buscar():
    movie_id = request.args.get("id")
    # Buscar en las películas locales
    movie = next((m for m in user_movies if m["id"] == movie_id), None)
    # Si no está local, buscar en la API
    if not movie:
        try:
            resp = requests.get(f"{API_URL}/{movie_id}", timeout=5)
            if resp.status_code == 200:
                movie = resp.json()
        except Exception:
            movie = None
    if not movie:
        return "<h2>No se encontró la película con ese ID.</h2><a href='/'>Volver</a>"
    # Mostrar los datos de la película encontrada
    return f"""
    <h2>Película encontrada</h2>
    <ul>
        <li><b>ID:</b> {movie['id']}</li>
        <li><b>Nombre:</b> {movie['carMovieName']}</li>
        <li><b>Año:</b> {movie['carMovieYear']}</li>
        <li><b>Duración:</b> {movie['duration']} min</li>
    </ul>
    <a href="/">Volver</a>
    """

if __name__ == "__main__":
    app.run(debug=True)