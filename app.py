from flask import Flask, render_template, request, redirect, url_for, flash
from utils.chaves_pix_manager import carregar_chaves_pix, adicionar_chave_pix
import json
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Rota de depuração para visualizar o conteúdo do arquivo JSON
@app.route('/debug/chaves')
def debug_chaves():
    try:
        with open('/tmp/chaves_pix.json', 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[INFO] Conteúdo de /tmp/chaves_pix.json: {content}")
        return f"Conteúdo de /tmp/chaves_pix.json:<pre>{content}</pre>"
    except Exception as e:
        print(f"[ERRO] Erro ao ler /tmp/chaves_pix.json: {str(e)}")
        return f"Erro ao ler /tmp/chaves_pix.json: {str(e)}"

# Rota de teste para verificar permissões de escrita
@app.route('/test_write')
def test_write():
    test_file = '/tmp/test_write.txt'
    try:
        with open(test_file, 'w') as f:
            f.write('Teste de escrita bem-sucedido')
        print(f"[INFO] Arquivo escrito em {test_file}")
        return f"Arquivo escrito em {test_file}"
    except Exception as e:
        print(f"[ERRO] Erro ao escrever em {test_file}: {str(e)}")
        return f"Erro ao escrever em {test_file}: {str(e)}"

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
    print(f"[INFO] Chaves Pix carregadas para a lista: {json.dumps(chaves_pix, indent=4)}")
    return render_template('chaves.html', chaves_pix=chaves_pix)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
