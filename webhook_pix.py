from flask import Flask, request, jsonify
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__)

# Diretório para armazenar logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def salvar_notificacao(payload):
    """Salva a notificação recebida em um arquivo JSON."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    notification_id = str(uuid.uuid4())[:8]
    filename = f"pix_notification_{timestamp}_{notification_id}.json"
    filepath = os.path.join(LOGS_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(payload, f, indent=4)
    return filepath

def processar_notificacao_pix(payload):
    """Processa a notificação de pagamento Pix recebida (OpenPix + Woovi)."""
    try:
        pix_info = {
            'event': payload.get('event', payload.get('evento', 'UNKNOWN')),
            'notification_id': str(uuid.uuid4()),
            'raw_payload': payload
        }

        # Caso 1: padrão original OpenPix
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

        # Caso 2: payload do Woovi sandbox
        elif payload.get('event') == 'OPENPIX:TRANSACTION_RECEIVED' or payload.get('evento') == 'teste_webhook':
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
            return {
                'status': 'ERROR',
                'error': 'Formato de payload desconhecido',
                'raw_payload': payload
            }

        if pix_info['status'] in ['COMPLETED', 'CONCLUIDA']:
            print(f"📥 Pagamento confirmado: R${pix_info['valor']} | TXID: {pix_info['txid']}")
            print(f"👤 Pagador: {pix_info['infoPagador'].get('name') or pix_info['infoPagador'].get('nome')}")

        return pix_info

    except Exception as e:
        print(f"Erro ao processar notificação: {e}")
        return {
            'status': 'ERROR',
            'error': str(e),
            'raw_payload': payload
        }

@app.route('/webhook/pix', methods=['POST'])
def webhook_pix():
    """Endpoint para receber notificações de pagamentos Pix da OpenPix."""
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
        print(f"Erro ao processar webhook: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erro ao processar notificação: {str(e)}'
        }), 500

@app.route('/webhook/pix/status', methods=['GET'])
def webhook_status():
    """Endpoint para verificar o status do serviço de webhook."""
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
        return jsonify({
            'status': 'error',
            'message': f'Erro ao verificar status: {str(e)}'
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Página principal com informações sobre o serviço."""
    return """
    <html>
        <head>
            <title>Webhook Pix - OpenPix</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }
                h1 {
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                .info {
                    background-color: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .endpoint {
                    background-color: #e9f7ef;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
                code {
                    background-color: #f1f1f1;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Webhook para Notificações Pix - OpenPix</h1>
                
                <div class="info">
                    <h2>Sobre este serviço</h2>
                    <p>Este serviço recebe notificações de pagamentos Pix da plataforma OpenPix e processa os eventos para integração com o sistema de conversão para criptomoedas.</p>
                </div>
                
                <h2>Endpoints disponíveis:</h2>
                
                <div class="endpoint">
                    <h3>POST /webhook/pix</h3>
                    <p>Endpoint principal para receber notificações de pagamentos Pix.</p>
                    <p>Este endpoint deve ser configurado na plataforma OpenPix para receber as notificações.</p>
                </div>
                
                <div class="endpoint">
                    <h3>GET /webhook/pix/status</h3>
                    <p>Verifica o status do serviço e lista as últimas notificações recebidas.</p>
                </div>
                
                <div class="info">
                    <h2>Como configurar na OpenPix</h2>
                    <p>1. Acesse a plataforma OpenPix</p>
                    <p>2. Vá para Configurações > APIs > Webhooks</p>
                    <p>3. Clique em "Criar Webhook"</p>
                    <p>4. Configure o webhook com a URL: <code>https://seu-dominio.com/webhook/pix</code></p>
                    <p>5. Selecione o evento "Pix recebido"</p>
                    <p>6. Ative o webhook e salve as configurações</p>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
