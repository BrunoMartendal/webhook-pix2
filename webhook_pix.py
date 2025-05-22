from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_simples'  # Necessário para usar flash()

# Logs de notificações Pix
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Chaves Pix (simulação)
chaves_pix = ['minhachave@email.com', 'outrachave@dominio.com']

# ROTAS DO FRONT-END
@app.route('/')
def index():
    return render_template('index.html', chaves=chaves_pix)

@app.route('/gerar_qrcode', methods=['POST'])
def gerar_qrcode():
    valor = request.form.get('valor')
    chave = request.form.get('chave')
    moeda = request.form.get('moeda')

    # Simula geração de QR Code (futuramente conecte com OpenPix)
    qrcode_url = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=FAKEPIX'
    payload = f"000201010212FAKEPIX{valor}{chave}{moeda}"

    return render_template('qrcode.html', valor=valor, chave=chave, moeda=moeda, payload=payload, qrcode_url=qrcode_url)

@app.route('/chaves')
def listar_chaves():
    return render_template('chaves_pix.html', chaves=chaves_pix)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_chave_pix_route():
    if request.method == 'POST':
        chave = request.form.get('chave')
        if chave:
            chaves_pix.append(chave)
            flash('Chave adicionada com sucesso!')
        return redirect(url_for('listar_chaves'))
    return render_template('adicionar_chave_pix.html')

@app.route('/remover/<chave>')
def remover_chave(chave):
    if chave in chaves_pix:
        chaves_pix.remove(chave)
        flash('Chave removida com sucesso.')
    return redirect(url_for('listar_chaves'))

# ROTAS PARA WEBHOOK PIX
@app.route('/webhook/pix', methods=['POST'])
def webhook_pix():
    try:
        payload = request.json
        print(f"Notificação Pix recebida: {payload}")
        log_path = salvar_notificacao(payload)
        print(f"Notificação salva em: {log_path}")
        resultado = processar_notificacao_pix(payload)
        return {
            'status': 'success',
            'message': 'Notificação recebida com sucesso',
            'processamento': resultado
        }, 200
    except Exception as e:
        print(f"Erro ao processar webhook: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/webhook/pix/status', methods=['GET'])
def webhook_status():
    try:
        arquivos = os.listdir(LOGS_DIR)
        arquivos.sort(reverse=True)
        ultimas_notificacoes = arquivos[:10]
        return {
            'status': 'online',
            'message': 'Serviço de webhook Pix está ativo',
            'ultimas_notificacoes': ultimas_notificacoes,
            'total_notificacoes': len(arquivos)
        }, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

# FUNÇÕES AUXILIARES
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

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/debug/chaves')
def debug_chaves():
    try:
        with open('/tmp/chaves_pix.json', 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Conteúdo de /tmp/chaves_pix.json: {content}")
        return f"Conteúdo de /tmp/chaves_pix.json:<pre>{content}</pre>"
    except Exception as e:
        logger.error(f"Erro ao ler /tmp/chaves_pix.json: {str(e)}")
        return f"Erro ao ler /tmp/chaves_pix.json: {str(e)}"

@app.route('/test_write')
def test_write():
    test_file = '/tmp/test_write.txt'
    try:
        with open(test_file, 'w') as f:
            f.write('Teste de escrita bem-sucedido')
        logger.info(f"Arquivo escrito em {test_file}")
        return f"Arquivo escrito em {test_file}"
    except Exception as e:
        logger.error(f"Erro ao escrever em {test_file}: {str(e)}")
        return f"Erro ao escrever em {test_file}: {str(e)}"

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/debug/chaves')
def debug_chaves():
    try:
        with open('/tmp/chaves_pix.json', 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Conteúdo de /tmp/chaves_pix.json: {content}")
        return f"Conteúdo de /tmp/chaves_pix.json:<pre>{content}</pre>"
    except Exception as e:
        logger.error(f"Erro ao ler /tmp/chaves_pix.json: {str(e)}")
        return f"Erro ao ler /tmp/chaves_pix.json: {str(e)}"

@app.route('/test_write')
def test_write():
    test_file = '/tmp/test_write.txt'
    try:
        with open(test_file, 'w') as f:
            f.write('Teste de escrita bem-sucedido')
        logger.info(f"Arquivo escrito em {test_file}")
        return f"Arquivo escrito em {test_file}"
    except Exception as e:
        logger.error(f"Erro ao escrever em {test_file}: {str(e)}")
        return f"Erro ao escrever em {test_file}: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
