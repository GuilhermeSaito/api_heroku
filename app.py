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

# def get_quadrate_disponivel(data):
#     list_disponivel = []

#     if not(1 in data):
#         list_disponivel.append(1)
#     if not(2 in data):
#         list_disponivel.append(2)
#     if not(3 in data):
#         list_disponivel.append(3)
#     if not(4 in data):
#         list_disponivel.append(4)

#     return list_disponivel


app = Flask(__name__)

@app.errorhandler(400)
def bad_request(e):
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
            "quantidade_produto": tuple[6],
            "quadrante": tuple[7]
        }
        list_dict.append(dict)
    
    return json.dumps(list_dict, indent = 4)

# EndPoint para ver se pode entrar na tela do Vendedor, ou seja, primeiro o usuario precisa ser Vendedor = 1 e essa funcao deve retornar algo diferente de vazio
@app.route("/canInsertProduct")
def can_insert_product():
    cnx = connect_db()
    
    cursor = cnx.cursor(buffered = True)

    query = ("SELECT quadrante_produto, email, senha FROM pessoas WHERE quadrante_produto = 1 OR quadrante_produto = 2 OR quadrante_produto = 3 OR quadrante_produto = 4 ORDER BY quadrante_produto;")

    cursor.execute(query)
    
    list_tuple = cursor.fetchall()

    list_dict = []
    for tuple in list_tuple:
        dict = {
            "quadrante": tuple[0],
            "email": tuple[1],
            "password": tuple[2]
        }

        list_dict.append(dict)

    return json.dumps(list_dict, indent = 4)

# EndPoint para a tela do Vendedor, para quando ele for adicionar mais produto E para a pagina do cliente, quando apertar o botao de comprar, vai retornar todos os dados iguais menos a quantidade do produto, que vai ser calculado no app e mandado pra ca
@app.route("/updateProduct", methods=['POST'])
def update_product():
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'Invalid JSON data'})
    
    emails = data.get("email_app")
    passwords = data.get("password_app")
    nomesProduto = data.get("nome_produtos_app")
    quantidadesProdutos = data.get("quantidade_produtos_app")
    quadrantesProduto = data.get("quadrante_produtos_app")

    cnx = connect_db()
    
    cursor = cnx.cursor(buffered = True)

    if type(emails) == str:
        query = "UPDATE pessoas SET nome_produto = %s, quantidade_produto = %s, quadrante_produto = %s WHERE email = %s AND senha = %s"
        values = (nomesProduto, quantidadesProdutos, quadrantesProduto, emails, passwords)
        try:
            # cursor.execute(query)
            cursor.execute(query, values)
            
        except mysql.connector.Error as error:
            return json.dumps({
                "message": "Error in updating data",
                "error": str(error)
            })
        cnx.commit()

        cnx.close()
        return json.dumps({
            "message": "Successfully updated data"
        })
    else:
        for nome_produto, quantidade_produto, quadrante_produto, email, password in zip(nomesProduto, quantidadesProdutos, quadrantesProduto, emails, passwords):
            # query = ("UPDATE pessoas SET nome_produto = '" + nome_produto + "', quantidade_produto = " + str(quantidade_produto) + ", quadrante_produto = " + str(quadrante_produto) + " WHERE email = '" + email + "' AND senha = '" + password + "';")
            query = "UPDATE pessoas SET nome_produto = %s, quantidade_produto = %s, quadrante_produto = %s WHERE email = %s AND senha = %s"
            values = (nome_produto, quantidade_produto, quadrante_produto, email, password)
            try:
                # cursor.execute(query)
                cursor.execute(query, values)
                
            except mysql.connector.Error as error:
                return json.dumps({
                    "message": "Error in updating data",
                    "error": str(error)
                })
        cnx.commit()

        cnx.close()
        return json.dumps({
            "message": "Successfully updated data"
        })

# EndPoint para fazer a tela do cliente, mostrando o nome do produto, a quantidade total, quantidade selecionada e os botoes de + ou -, o quadrante serve pra falar pro esp qual motor rodar e quantos quadradinhos devem ser mostrados
@app.route("/getProdutosQuadrante")
def get_produtos_quadrante():
    cnx = connect_db()
    
    cursor = cnx.cursor(buffered = True)

    query = ("SELECT nome, email, nome_produto, quantidade_produto, quadrante_produto, senha FROM pessoas WHERE quadrante_produto = 1 OR quadrante_produto = 2 OR quadrante_produto = 3 OR quadrante_produto = 4 ORDER BY quadrante_produto ASC")

    cursor.execute(query)
    
    list_tuple = cursor.fetchall()

    list_dict = []
    for tuple in list_tuple:
        dict = {
            "nome": tuple[0],
            "email": tuple[1],
            "nome_produto": tuple[2],
            "quantidade_produto": tuple[3],
            "quadrante_produto": tuple[4],
            "password": tuple[5]
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
            "error: " : str(error)
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
    title = request.args.get('title', '')
    content = request.args.get('content', '')

    message = Mail(
    from_email = 'hanbaikicandymachine@gmail.com',
    to_emails = email,
    subject = title,
    html_content = content)
    try:
        sg = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
    except Exception as e:
        return json.dumps({
            "Error message: " : str(e)
        })
    
    return json.dumps({
        "message: " : "Email sended to " + email
    })

@app.route("/")
def teste():
    return "Hello Another World"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))