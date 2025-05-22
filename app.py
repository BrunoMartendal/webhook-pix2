from flask import Flask, render_template, request, redirect, url_for, flash
from utils.chaves_pix_manager import carregar_chaves_pix, adicionar_chave_pix
import json

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

@app.route('/')
def index():
    chaves_pix = carregar_chaves_pix()
    print(f"[INFO] Chaves Pix carregadas para a página inicial: {json.dumps(chaves_pix, indent=4)}")
    return render_template('index.html', chaves_pix=chaves_pix)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_chave_pix_route():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        tipo_chave = request.form.get('tipo_chave')
        chave = request.form.get('chave')
        print(f"[INFO] Dados do formulário: descricao={descricao}, tipo_chave={tipo_chave}, chave={chave}")
        if not descricao or not tipo_chave or not chave:
            flash('Todos os campos são obrigatórios!')
            return redirect(url_for('adicionar_chave_pix_route'))
        try:
            adicionar_chave_pix(descricao, tipo_chave, chave)
            flash('Chave adicionada com sucesso!')
        except Exception as e:
            flash(f'Erro ao adicionar chave: {str(e)}')
        return redirect(url_for('listar_chaves'))
    return render_template('adicionar_chave_pix.html')

@app.route('/chaves')
def listar_chaves():
    chaves_pix = carregar_chaves_pix()
    return render_template('chaves.html', chaves_pix=chaves_pix)
