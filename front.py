from flask import Flask, render_template_string, redirect, request
import requests
import json

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
    <div class="pagination">
        {% if page > 1 %}
            <a href="/?page={{ page - 1 }}">Anterior</a>
        {% endif %}
        <span>Página {{ page }} de {{ pages }}</span>
        {% if page < pages %}
            <a href="/?page={{ page + 1 }}">Siguiente</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    page = int(request.args.get("page", 1))
    per_page = 5
    local_count = len(user_movies)

    # SIEMPRE pide el total real de la API (aunque solo pidas 1 película)
    try:
        resp_total = requests.get(f"{API_URL}?page=0&size=1", timeout=5)
        data_total = resp_total.json()
        total_api = data_total.get("totalElements", 0)
    except Exception:
        total_api = 0

    if page == 1:
        api_needed = max(0, per_page - local_count)
        api_movies = []
        if api_needed > 0:
            api_url = f"{API_URL}?page=0&size={api_needed}&sort=carMovieYear,desc"
            try:
                resp = requests.get(api_url, timeout=5)
                data = resp.json()
                api_movies = data.get("Movies", [])
            except Exception:
                api_movies = []
        movies_page = user_movies[:per_page] + api_movies
    else:
        # Calcula cuántas páginas ocupan las locales
        local_pages = (local_count + per_page - 1) // per_page
        api_page = page - local_pages
        if api_page < 1:
            movies_page = []
        else:
            api_url = f"{API_URL}?page={api_page-1}&size={per_page}&sort=carMovieYear,desc"
            try:
                resp = requests.get(api_url, timeout=5)
                data = resp.json()
                movies_page = data.get("Movies", [])
            except Exception:
                movies_page = []

    # El total de páginas es locales + total de la API
    total_all = local_count + total_api
    pages = (total_all + per_page - 1) // per_page

    return render_template_string(
        TEMPLATE,
        movies=movies_page,
        page=page,
        pages=pages
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
    if movie_id.startswith("user-"):
        user_movies = [m for m in user_movies if m["id"] != movie_id]
    else:
        try:
            resp = requests.delete(
                f"{API_URL}/{movie_id}",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print("DELETE status:", resp.status_code, resp.text)
        except Exception as e:
            print("Error al eliminar en la API:", e)
    return redirect("/")

@app.route("/edit", methods=["GET", "POST"])
def edit_movie():
    movie_id = request.values.get("id")
    # Si es local
    if movie_id.startswith("user-"):
        movie = next((m for m in user_movies if m["id"] == movie_id), None)
        if not movie:
            return redirect("/")
        if request.method == "POST":
            movie["carMovieName"] = request.form["carMovieName"]
            movie["carMovieYear"] = request.form["carMovieYear"]
            movie["duration"] = request.form["duration"]
            return redirect("/")
    # Si es de la API
    else:
        if request.method == "POST":
            payload = {
                "carMovieName": request.form["carMovieName"],
                "carMovieYear": request.form["carMovieYear"],
                "duration": request.form["duration"]
            }
            try:
                resp = requests.put(
                    f"{API_URL}/{movie_id}",
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                print("PUT status:", resp.status_code, resp.text)
            except Exception as e:
                print("Error al actualizar en la API:", e)
            return redirect("/")
        # GET: obtener datos actuales de la API
        try:
            resp = requests.get(f"{API_URL}/{movie_id}", timeout=5)
            if resp.status_code == 200:
                movie = resp.json()
            else:
                return redirect("/")
        except Exception:
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
           # Si la API devuelve un objeto con los campos correctos
                movie = resp.json()  
           # Si la API envía los datos anidados, ajusta aquí:     
            #movie = movie.get("Movie", movie)  
            else:        
                movie = None      
        except Exception:       
            movie = None   
    if not movie or not all(k in movie for k in ("id", "carMovieName", "carMovieYear", "duration")):
                    
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