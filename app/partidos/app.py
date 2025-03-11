from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask import jsonify
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os


# Configurar Flask
app = Flask(__name__)

load_dotenv()

# Configurar la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de la base de datos
class Partido(db.Model):
    __tablename__ = 'partidos'
    id = db.Column(db.Integer, primary_key=True)
    local = db.Column(db.String(100))
    visitante = db.Column(db.String(100))
    gol_local = db.Column(db.Integer)
    gol_visitante = db.Column(db.Integer)
    estadio = db.Column(db.String(100))
    competencia = db.Column(db.String(100))
    fecha = db.Column(db.Date)
    rating = db.Column(db.Float)
    link = db.Column(db.String(255)) 

# Ruta principal
@app.route('/')
def index():
    partidos = Partido.query.all()
    df = pd.DataFrame([{column.name: getattr(partido, column.name) for column in Partido.__table__.columns} for partido in partidos])
    
    if df.empty:
        return render_template('index.html', graph_html="<h3>No hay datos disponibles</h3>")
    
    # Gráfico de goles locales
    fig_local = px.bar(df, x='local', y='gol_local', title='Goles anotados por equipo local', labels={'local': 'Equipo', 'gol_local': 'Goles'})
    graph_local = pio.to_html(fig_local, full_html=False)
    
    # Gráfico de goles visitantes
    fig_visitante = px.bar(df, x='visitante', y='gol_visitante', title='Goles anotados por equipo visitante', labels={'visitante': 'Equipo', 'gol_visitante': 'Goles'})
    graph_visitante = pio.to_html(fig_visitante, full_html=False)
    
    return render_template('index.html', graph_local=graph_local, graph_visitante=graph_visitante)

@app.route('/data')
def get_data():
    partidos = Partido.query.all()
    data = [{column.name: getattr(partido, column.name) for column in Partido.__table__.columns} for partido in partidos]
    return jsonify(data)

@app.route('/ultimo_partido')
def ultimo_partido():
    ultimo = Partido.query.order_by(Partido.fecha.desc()).first()
    
    if not ultimo:
        return {"error": "No hay partidos registrados"}

    return {
        "local": ultimo.local,
        "visitante": ultimo.visitante,
        "gol_local": ultimo.gol_local,
        "gol_visitante": ultimo.gol_visitante,
        "competencia": ultimo.competencia,
        "fecha": ultimo.fecha.strftime('%Y-%m-%d'),
    }

#obtiene los resultados de los partidos para sabear victorias, empates etc. 
@app.route('/resultados')
def resultados():
    partidos = Partido.query.all()

    if not partidos:
        return jsonify({"error": "No hay partidos registrados"})

    resultados = {"victoria": 0, "empate": 0, "derrota": 0}

    for partido in partidos:
        if partido.gol_local > partido.gol_visitante:
            resultados["victoria"] += 1
        elif partido.gol_local == partido.gol_visitante:
            resultados["empate"] += 1
        else:
            resultados["derrota"] += 1

    return jsonify(resultados)


@app.route('/river_stats')
def river_stats():
    partidos_river = Partido.query.filter(
        (Partido.local == "River") | (Partido.visitante == "River")
    ).all()

    if not partidos_river:
        return jsonify({"error": "No hay partidos de River registrados"})

    victorias = 0
    empates = 0
    derrotas = 0

    for partido in partidos_river:
        if partido.local == "River":
            if partido.gol_local > partido.gol_visitante:
                victorias += 1
            elif partido.gol_local < partido.gol_visitante:
                derrotas += 1
            else:
                empates += 1
        elif partido.visitante == "River":
            if partido.gol_visitante > partido.gol_local:
                victorias += 1
            elif partido.gol_visitante < partido.gol_local:
                derrotas += 1
            else:
                empates += 1

    return jsonify({"victorias": victorias, "empates": empates, "derrotas": derrotas})

#mejor y peor racha.
@app.route('/river_streaks')
def river_streaks():
    partidos_river = Partido.query.filter(
        (Partido.local == "River") | (Partido.visitante == "River")
    ).order_by(Partido.fecha).all()

    if not partidos_river:
        return jsonify({"error": "No hay partidos de River registrados"})

    mejor_racha_invicta = 0
    mejor_racha_actual = 0
    peor_racha_sin_ganar = 0
    peor_racha_actual = 0

    for partido in partidos_river:
        resultado = None
        if partido.local == "River":
            if partido.gol_local > partido.gol_visitante:
                resultado = "victoria"
            elif partido.gol_local < partido.gol_visitante:
                resultado = "derrota"
            else:
                resultado = "empate"
        elif partido.visitante == "River":
            if partido.gol_visitante > partido.gol_local:
                resultado = "victoria"
            elif partido.gol_visitante < partido.gol_local:
                resultado = "derrota"
            else:
                resultado = "empate"

        if resultado in ["victoria", "empate"]:
            mejor_racha_actual += 1
            peor_racha_actual = 0
        else:
            peor_racha_actual += 1
            mejor_racha_actual = 0

        mejor_racha_invicta = max(mejor_racha_invicta, mejor_racha_actual)
        peor_racha_sin_ganar = max(peor_racha_sin_ganar, peor_racha_actual)

    return jsonify({
        "mejor_racha_invicta": mejor_racha_invicta,
        "peor_racha_sin_ganar": peor_racha_sin_ganar
    })

# Ruta para partidos donde River fue visitante
@app.route('/partidos_visitante')
def partidos_visitante():
    partidos = Partido.query.filter_by(visitante="River").order_by(Partido.fecha.desc()).all()
    
    data = [{
        "local": partido.local,
        "visitante": partido.visitante,
        "gol_local": partido.gol_local,
        "gol_visitante": partido.gol_visitante,
        "competencia": partido.competencia,
        "fecha": partido.fecha.strftime('%Y-%m-%d'),  # Formateo correcto de fecha
        "link": partido.link if partido.link else None,
    } for partido in partidos]

    return jsonify(data)

#estadisticas de cuando river juega de visitnate.
@app.route('/estadisticas_visitante')
def estadisticas_visitante():
    partidos = Partido.query.filter_by(visitante="River").all()
    
    total_partidos = len(partidos)
    victorias = sum(1 for p in partidos if p.gol_visitante > p.gol_local)
    empates = sum(1 for p in partidos if p.gol_visitante == p.gol_local)
    derrotas = sum(1 for p in partidos if p.gol_visitante < p.gol_local)
    
    efectividad = (victorias * 100 / total_partidos) if total_partidos > 0 else 0

    return jsonify({
        "total": total_partidos,
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "efectividad": round(efectividad, 2)
    })


#Partidos que asisti de neutral.
@app.route('/partidos_neutral')
def partidos_neutral():
    partidos = Partido.query.filter(Partido.local != "River", Partido.visitante != "River").order_by(Partido.fecha.desc()).all()

    data = [{
        "local": partido.local,
        "visitante": partido.visitante,
        "gol_local": partido.gol_local,
        "gol_visitante": partido.gol_visitante,
        "competencia": partido.competencia,
        "fecha": partido.fecha.strftime('%Y-%m-%d'),
        "link": partido.link if partido.link else None,
    } for partido in partidos]

    return jsonify(data)

@app.route('/efectividad_neutral')
def efectividad_neutral():
    partidos = Partido.query.filter(Partido.local != "River", Partido.visitante != "River").all()

    if not partidos:
        return jsonify({"error": "No hay partidos neutrales registrados."})

    victorias = sum(1 for p in partidos if p.gol_local > p.gol_visitante)
    empates = sum(1 for p in partidos if p.gol_local == p.gol_visitante)
    derrotas = sum(1 for p in partidos if p.gol_local < p.gol_visitante)
    
    total_partidos = len(partidos)
    efectividad = ((victorias * 3) + (empates * 1)) / (total_partidos * 3) * 100

    return jsonify({
        "total_partidos": total_partidos,
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "efectividad": round(efectividad, 2)
    })


@app.route('/partidos_comparacion')
def partidos_comparacion():
    # Total de partidos por año
    total_partidos = db.session.query(db.func.year(Partido.fecha), db.func.count(Partido.id))\
        .group_by(db.func.year(Partido.fecha)).all()

    # Partidos de River por año (como local o visitante)
    river_partidos = db.session.query(db.func.year(Partido.fecha), db.func.count(Partido.id))\
        .filter((Partido.local == "River") | (Partido.visitante == "River"))\
        .group_by(db.func.year(Partido.fecha)).all()

    # Partidos donde River fue LOCAL
    river_local = db.session.query(db.func.year(Partido.fecha), db.func.count(Partido.id))\
        .filter(Partido.local == "River")\
        .group_by(db.func.year(Partido.fecha)).all()

    # Partidos donde River fue VISITANTE
    river_visitante = db.session.query(db.func.year(Partido.fecha), db.func.count(Partido.id))\
        .filter(Partido.visitante == "River")\
        .group_by(db.func.year(Partido.fecha)).all()

    # Partidos neutrales (ni River local ni visitante)
    partidos_neutrales = db.session.query(db.func.year(Partido.fecha), db.func.count(Partido.id))\
        .filter((Partido.local != "River") & (Partido.visitante != "River"))\
        .group_by(db.func.year(Partido.fecha)).all()

    # Convertir datos a JSON
    data = {
        "total": [{"anio": anio, "cantidad": cantidad} for anio, cantidad in total_partidos],
        "river": [{"anio": anio, "cantidad": cantidad} for anio, cantidad in river_partidos],
        "river_local": [{"anio": anio, "cantidad": cantidad} for anio, cantidad in river_local],
        "river_visitante": [{"anio": anio, "cantidad": cantidad} for anio, cantidad in river_visitante],
        "neutral": [{"anio": anio, "cantidad": cantidad} for anio, cantidad in partidos_neutrales]
    }

    return jsonify(data)




# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)