from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import json
import uuid
from datetime import datetime

# Importa as funções de utilitário
from utils.chaves_pix_manager import (
carregar_chaves_pix,
adicionar_chave_pix,
remover_chave_pix,
salvar_chaves_pix
)

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'

# -------------------- ROTAS DE FRONT-END --------------------

@app.route('/')
def index():
    chaves_pix = carregar_chaves_pix()
    return render_template('index.html', chaves_pix=chaves_pix)

@app.route('/gerar_qrcode', methods=['POST'])
def gerar_qrcode():
    valor = request.form.get('valor')
    chave_pix_id = request.form.get('chave_pix_id')
    moeda = request.form.get('moeda')

    chaves_pix = carregar_chaves_pix()
    chave_pix = next((ch for ch in chaves_pix if ch['id'] == chave_pix_id), None)

    if not chave_pix:
        flash("Chave Pix não encontrada.")
        return redirect(url_for('index'))

    payload = f"000201010212FAKEPIX{valor}{chave_pix['chave']}{moeda}"
    qrcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={payload}"

    return render_template("qrcode.html", valor=valor, chave=chave_pix['chave'], moeda=moeda, payload=payload, qrcode_url=qrcode_url)

@app.route('/chaves')
def listar_chaves():
    chaves_pix = carregar_chaves_pix()
    return render_template('chaves_pix.html', chaves_pix=chaves_pix)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_chave_pix_route():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        tipo_chave = request.form.get('tipo_chave')
        chave = request.form.get('chave')

        if not descricao or not tipo_chave or not chave:
            flash('Todos os campos são obrigatórios!')
            return redirect(url_for('adicionar_chave_pix_route'))

        adicionar_chave_pix(descricao, tipo_chave, chave)
        flash('Chave adicionada com sucesso!')
        return redirect(url_for('listar_chaves'))

    return render_template('adicionar_chave_pix.html')

@app.route('/remover/<chave_id>', methods=['POST'])
def remover_chave(chave_id):
    sucesso = remover_chave_pix(chave_id)
    if sucesso:
        flash('Chave removida com sucesso!')
    else:
        flash('Chave não encontrada.')
    return redirect(url_for('listar_chaves'))

# -------------------- WEBHOOK PIX --------------------

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

@app.route('/webhook/pix', methods=['POST'])
def webhook_pix():
    try:
        payload = request.json
        print(f"Notificação Pix recebida: {payload}")
        log_path = salvar_notificacao(payload)
        print(f"Notificação salva em: {log_path}")
        resultado = processar_notificacao_pix(payload)
        return jsonify({
            'status': 'success',
            'message': 'Notificação recebida com sucesso',
            'processamento': resultado
        }), 200
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/pix/status', methods=['GET'])
def webhook_status():
    try:
        arquivos = os.listdir(LOGS_DIR)
        arquivos.sort(reverse=True)
        ultimas_notificacoes = arquivos[:10]
        return jsonify({
            'status': 'online',
            'message': 'Serviço de webhook Pix está ativo',
            'ultimas_notificacoes': ultimas_notificacoes,
            'total_notificacoes': len(arquivos)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -------------------- FUNÇÕES AUXILIARES --------------------

def salvar_notificacao(payload):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    notification_id = str(uuid.uuid4())[:8]
    filename = f"pix_notification_{timestamp}_{notification_id}.json"
    filepath = os.path.join(LOGS_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(payload, f, indent=4)
    return filepath

def processar_notificacao_pix(payload):
    try:
        pix_info = {
            'event': payload.get('event', payload.get('evento', 'UNKNOWN')),
            'notification_id': str(uuid.uuid4()),
            'raw_payload': payload
        }

        if 'pix' in payload and isinstance(payload['pix'], dict):
            pix = payload['pix']
            pix_info.update({
                'status': pix.get('status'),
                'valor': pix.get('valor'),
                'txid': pix.get('txid'),
                'e2eid': pix.get('e2eid'),
                'infoPagador': pix.get('infoPagador', {}),
                'type': pix.get('type', payload.get('type'))
            })

        elif payload.get('event') == 'OPENPIX:TRANSACTION_RECEIVED':
            charge = payload.get('charge', {})
            pm_pix = charge.get('paymentMethods', {}).get('pix', charge.get('customer', {}))
            pix_info.update({
                'status': charge.get('status') or pm_pix.get('status'),
                'valor': charge.get('value') or pm_pix.get('value'),
                'txid': charge.get('transactionID') or pm_pix.get('transactionID'),
                'e2eid': charge.get('identifier') or pm_pix.get('identifier'),
                'infoPagador': charge.get('customer') or pm_pix.get('payer', {}),
                'type': charge.get('type')
            })

        else:
            return {'status': 'ERROR', 'error': 'Formato de payload desconhecido'}

        if pix_info['status'] in ['COMPLETED', 'CONCLUIDA']:
            print(f"📥 Pagamento confirmado: R${pix_info['valor']} | TXID: {pix_info['txid']}")
            print(f"👤 Pagador: {pix_info['infoPagador'].get('name') or pix_info['infoPagador'].get('nome')}")

        return pix_info

    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}

# -------------------- EXECUÇÃO LOCAL --------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
