
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    admin = db.Column(db.Boolean, default=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(250), nullable=False)

@app.route('/')
def index():
    produtos = Produto.query.limit(8).all()
    return render_template('index.html', produtos=produtos)

@app.route('/produtos')
def produtos():
    todos = Produto.query.all()
    return render_template('produtos.html', produtos=todos)

@app.route('/produto/<int:id>')
def produto(id):
    p = Produto.query.get_or_404(id)
    return render_template('produto.html', produto=p)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!')
            return redirect(url_for('cadastro'))
        novo = Usuario(email=email, nome=nome)
        novo.set_senha(senha)
        db.session.add(novo)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça login.')
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = Usuario.query.filter_by(email=email).first()
        if user and user.checar_senha(senha):
            session['usuario_id'] = user.id
            session['usuario_nome'] = user.nome
            session['usuario_admin'] = user.admin
            flash('Login realizado com sucesso!')
            return redirect(url_for('index'))
        flash('Email ou senha incorretos!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.')
    return redirect(url_for('index'))

def inicializar_carrinho():
    if 'carrinho' not in session:
        session['carrinho'] = {}

@app.route('/adicionar_carrinho/<int:produto_id>', methods=['POST'])
def adicionar_carrinho(produto_id):
    inicializar_carrinho()
    quantidade = int(request.form.get('quantidade', 1))
    carrinho = session['carrinho']
    carrinho[str(produto_id)] = carrinho.get(str(produto_id), 0) + quantidade
    session['carrinho'] = carrinho
    flash('Produto adicionado ao carrinho!')
    return redirect(url_for('carrinho'))

@app.route('/carrinho')
def carrinho():
    inicializar_carrinho()
    carrinho = session['carrinho']
    produtos_carrinho = []
    total = 0

    for pid, qtd in carrinho.items():
        produto = Produto.query.get(int(pid))
        if produto:
            subtotal = produto.preco * qtd
            total += subtotal
            produtos_carrinho.append({
                'produto': produto,
                'quantidade': qtd,
                'subtotal': subtotal
            })

    return render_template('carrinho.html', produtos=produtos_carrinho, total=total)

@app.route('/remover_carrinho/<int:produto_id>')
def remover_carrinho(produto_id):
    inicializar_carrinho()
    carrinho = session['carrinho']
    pid = str(produto_id)
    if pid in carrinho:
        del carrinho[pid]
        session['carrinho'] = carrinho
        flash('Produto removido do carrinho.')
    return redirect(url_for('carrinho'))

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        db.create_all()
        print("Banco de dados criado.")
    app.run(debug=True)
