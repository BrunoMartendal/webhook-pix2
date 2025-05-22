from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import json
import uuid
from datetime import datetime
import logging
import requests
from utils.chaves_pix_manager import carregar_chaves_pix, adicionar_chave_pix, remover_chave_pix, salvar_transacao_pix, atualizar_transacao_pix
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'segredo_simples'  # Necessário para usar flash()

# Configuração da OpenPix (sandbox para testes)
OPENPIX_API_KEY = os.getenv('OPENPIX_API_KEY')
OPENPIX_API_URL = 'https://api.sandbox.openpix.com.br/openpix/v1'  # URL do sandbox
OPENPIX_HEADERS = {
    'Authorization': f'Bearer {OPENPIX_API_KEY}',
    'Content-Type': 'application/json'
}

# Logs de notificações Pix
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# ROTAS DO FRONT-END
@app.route('/')
def index():
    chaves_pix = carregar_chaves_pix()
    logger.info(f"Chaves Pix carregadas para a página inicial: {json.dumps(chaves_pix, indent=4)}")
    return render_template('index.html', chaves=chaves_pix)

@app.route('/gerar_qrcode', methods=['POST'])
def gerar_qrcode():
    valor = request.form.get('valor')
    chave_id = request.form.get('chave_pix_id')
    moeda = request.form.get('moeda')

    chaves_pix = carregar_chaves_pix()
    chave_pix = next((ch for ch in chaves_pix if ch['id'] == chave_id), None)

    if not chave_pix:
        flash("Chave Pix não encontrada.")
        return redirect(url_for('index'))

    try:
        # Validar valor
        valor_float = float(valor.replace(',', '.'))
        if valor_float <= 0:
            flash("O valor deve ser maior que zero.")
            return redirect(url_for('index'))

        # Criar cobrança Pix na OpenPix
        payload = {
            'value': int(valor_float * 100),  # OpenPix usa centavos
            'correlationID': str(uuid.uuid4()),
            'destination': {
                'pixKey': chave_pix['chave'],
                'type': chave_pix['tipo_chave']
            },
            'comment': f"Pagamento de R${valor_float:.2f} para {chave_pix['descricao']}"
        }
        logger.info(f"Payload enviado para OpenPix: {json.dumps(payload, indent=4)}")
        response = requests.post(f'{OPENPIX_API_URL}/charge', headers=OPENPIX_HEADERS, json=payload)
        response.raise_for_status()
        charge = response.json()

        # Salvar transação
        transacao = salvar_transacao_pix(valor_float, moeda, chave_id, charge['charge']['correlationID'])

        return render_template('qrcode.html',
                             valor=valor_float,
                             chave=chave_pix['chave'],
                             moeda=moeda,
                             txid=charge['charge']['correlationID'],
                             payload=charge['charge']['brCode'],
                             qrcode_url=charge['charge']['qrCodeImage'])
    except Exception as e:
        logger.error(f"Erro ao gerar QR Code: {str(e)}")
        flash(f"Erro ao gerar QR Code: {str(e)}")
        return redirect(url_for('index'))

@app.route('/chaves')
def listar_chaves():
    chaves_pix = carregar_chaves_pix()
    logger.info(f"Chaves Pix carregadas para a lista: {json.dumps(chaves_pix, indent=4)}")
    return render_template('chaves_pix.html', chaves=chaves_pix)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_chave_pix_route():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        tipo_chave = request.form.get('tipo_chave')
        chave = request.form.get('chave')
        logger.info(f"Dados do formulário: descricao={descricao}, tipo_chave={tipo_chave}, chave={chave}")
        if not descricao or not tipo_chave or not chave:
            flash('Todos os campos obrigatórios devem ser preenchidos!')
            return redirect(url_for('adicionar_chave_pix_route'))
        try:
            adicionar_chave_pix(descricao, tipo_chave, chave)
            flash('Chave adicionada com sucesso!')
        except Exception as e:
            flash(f'Erro ao adicionar chave: {str(e)}')
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

# ROTAS PARA WEBHOOK PIX
@app.route('/webhook/pix', methods=['POST'])
def webhook_pix():
    try:
        payload = request.json
        logger.info(f"Notificação Pix recebida: {json.dumps(payload, indent=4)}")
        log_path = salvar_notificacao(payload)
        logger.info(f"Notificação salva em: {log_path}")
        resultado = processar_notificacao_pix(payload)
        return jsonify({
            'status': 'success',
            'message': 'Notificação recebida com sucesso',
            'processamento': resultado
        }), 200
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
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

# ROTAS DE DEPURAÇÃO
@app.route('/debug/chaves')
def debug_chaves_route():
    try:
        with open('/tmp/chaves_pix.json', 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Conteúdo de /tmp/chaves_pix.json: {content}")
        return f"Conteúdo de /tmp/chaves_pix.json:<pre>{content}</pre>"
    except Exception as e:
        logger.error(f"Erro ao ler /tmp/chaves_pix.json: {str(e)}")
        return f"Erro ao ler /tmp/chaves_pix.json: {str(e)}"

@app.route('/debug/transacoes')
def debug_transacoes_route():
    try:
        with open('/tmp/transacoes_pix.json', 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Conteúdo de /tmp/transacoes_pix.json: {content}")
        return f"Conteúdo de /tmp/transacoes_pix.json:<pre>{content}</pre>"
    except Exception as e:
        logger.error(f"Erro ao ler /tmp/transacoes_pix.json: {str(e)}")
        return f"Erro ao ler /tmp/transacoes_pix.json: {str(e)}"

@app.route('/test_write')
def test_write_route():
    test_file = '/tmp/test_write.txt'
    try:
        with open(test_file, 'w') as f:
            f.write('Teste de escrita bem-sucedido')
        logger.info(f"Arquivo escrito em {test_file}")
        return f"Arquivo escrito em {test_file}"
    except Exception as e:
        logger.error(f"Erro ao escrever em {test_file}: {str(e)}")
        return f"Erro ao escrever em {test_file}: {str(e)}"

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
            # Atualizar transação, se aplicável
            if pix_info['status'] in ['COMPLETED', 'CONCLUIDA']:
                transacao = atualizar_transacao_pix(pix_info['txid'], 'CONCLUIDA')
                if transacao:
                    pix_info['proximo_passo'] = f"Pagamento confirmado, aguardando conversão para {transacao['moeda']}"
                else:
                    pix_info['proximo_passo'] = 'Transação não encontrada'

        elif payload.get('event') == 'OPENPIX:TRANSACTION_RECEIVED':
            charge = payload.get('charge', {})
            pm_pix = charge.get('paymentMethods', {}).get('pix', charge.get('customer', {}))
            pix_info.update({
                'status': charge.get('status') or pm_pix.get('status'),
                'valor': (charge.get('value') or pm_pix.get('value', 0)) / 100,  # OpenPix usa centavos
                'txid': charge.get('transactionID') or pm_pix.get('transactionID') or charge.get('correlationID'),
                'e2eid': charge.get('identifier') or pm_pix.get('identifier'),
                'infoPagador': charge.get('customer') or pm_pix.get('payer', {}),
                'type': charge.get('type')
            })
            # Atualizar transação, se aplicável
            if pix_info['status'] in ['COMPLETED', 'CONCLUIDA']:
                transacao = atualizar_transacao_pix(pix_info['txid'], 'CONCLUIDA')
                if transacao:
                    pix_info['proximo_passo'] = f"Pagamento confirmado, aguardando conversão para {transacao['moeda']}"
                else:
                    pix_info['proximo_passo'] = 'Transação não encontrada'

        else:
            return {'status': 'ERROR', 'error': 'Formato de payload desconhecido'}

        if pix_info['status'] in ['COMPLETED', 'CONCLUIDA']:
            logger.info(f"📥 Pagamento confirmado: R${pix_info['valor']:.2f} | TXID: {pix_info['txid']}")
            logger.info(f"👤 Pagador: {pix_info['infoPagador'].get('name') or pix_info['infoPagador'].get('nome')}")

        return pix_info
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
