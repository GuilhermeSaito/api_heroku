from flask import Flask, request, abort, jsonify
from werkzeug.exceptions import HTTPException
import mysql.connector
from mysql.connector import errorcode
import json
import configparser
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def connect_db():
    config = configparser.ConfigParser()
    config.read("config.cfg")

    user = config["db_access"]["GOOGLE_MYSQL_USR"]
    password = config["db_access"]["GOOGLE_MYSQL_PWD"]
    host = config["db_access"]["GOOGLE_MYSQL_END_POINT"]
    port = config["db_access"]["GOOGLE_MYSQL_PORT"]
    db_name = config["db_access"]["GOOGLE_MYSQL_DB_NAME"]

    try:
        cnx = mysql.connector.connect(user = user,
                                    password = password,
                                    host = host,
                                    port = port,
                                    database = db_name)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    return cnx

app = Flask(__name__)

@app.errorhandler(400)
def bad_request(e):
    print(e)
    return jsonify(error=str(e)), 400

#transforma todos os erros padrões de html para json
@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

# # -------------- Retorna todos os produtos cadastrados na base
# @app.route("/getDataProdutos")
# def get_data():
#     cnx = connect_db()
    
#     cursor = cnx.cursor(buffered = True)

#     query = ("SELECT * FROM produtos")

#     cursor.execute(query)
    
#     list_tuple = cursor.fetchall()

#     list_dict = []
#     for tuple in list_tuple:
#         # Da para fazer assim no dic pq as colunas da tabela n mudam, mas se mudar vai ter q mudar aqui tbm
#         dict = {
#             "id": tuple[0],
#             "nome": tuple[1],
#             "quantidade": tuple[2]
#         }
#         list_dict.append(dict)
    
#     return json.dumps(list_dict, indent = 4)

# -------------- Retorna todas as pessoas cadastradas na base
@app.route("/getDataPessoa")
def get_data():
    cnx = connect_db()
    
    cursor = cnx.cursor(buffered = True)

    query = ("SELECT * FROM pessoas")

    cursor.execute(query)
    
    list_tuple = cursor.fetchall()

    list_dict = []
    for tuple in list_tuple:
        # Da para fazer assim no dic pq as colunas da tabela n mudam, mas se mudar vai ter q mudar aqui tbm
        dict = {
            "id": tuple[0],
            "nome": tuple[1],
            "email": tuple[2],
            "senha": tuple[3],
            "vendedor": tuple[4],
            "nome_produto": tuple[5],
            "quantidade_produto": tuple[6]
        }
        list_dict.append(dict)
    
    return json.dumps(list_dict, indent = 4)

@app.route("/insertDataPessoa")
def insertDataPessoa():
    nome = request.args.get('nome', '')
    email = request.args.get('email', '')
    password = request.args.get('password', '')
    vendedor = request.args.get('vendedor', '')

    data_insert = (nome, email, password, vendedor)

    cnx = connect_db()
    
    cursor = cnx.cursor(buffered = True)

    query = ("INSERT INTO pessoas (nome, email, senha, vendedor) VALUES (%s, %s, %s, %s)")

    try:
        cursor.execute(query, data_insert)
        
        cnx.commit()

        cnx.close()
    except mysql.connector.Error as error:
        return json.dumps({
            "message: " : "Error in inserting data: ",
            "error: " : error
        })
        
    
    return json.dumps({
        "message: " : "Successfully inserted data"
    })

# -------------- Valida o acesso da pessoa
@app.route("/validateLogin")
def validate_login():
    email = request.args.get('email', '')
    password = request.args.get('password', '')

    cnx = connect_db()
    
    cursor = cnx.cursor(buffered = True)

    query = ("SELECT * FROM pessoas WHERE email = '" + email + "' AND senha = '" + password + "'")

    print(query)

    cursor.execute(query)
    
    list_tuple = cursor.fetchall()

    if len(list_tuple) > 0:
        list_dict = []
        for tuple in list_tuple:
            # Da para fazer assim no dic pq as colunas da tabela n mudam, mas se mudar vai ter q mudar aqui tbm
            dict = {
                "id": tuple[0],
                "nome": tuple[1],
                "email": tuple[2],
                "senha": tuple[3],
                "vendedor": tuple[4],
                "nome_produto": tuple[5],
                "quantidade_produto": tuple[6]
            }
            list_dict.append(dict)
        
        return json.dumps(list_dict, indent = 4)

    return {}

@app.route("/sendEmail")
def send_email():
    email = request.args.get('email', '')

    message = Mail(
    from_email = 'hanbaikicandymachine@gmail.com',
    to_emails = email,
    subject = 'Sending with Twilio SendGrid is Fun',
    html_content = '<strong>and easy to do anywhere, even with Python</strong>')
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
    except Exception as e:
        return {}
    
    return json.dumps({
        "message: " : "Email sended to " + email
    })

@app.route("/")
def teste():
    return "Hello Another World"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))