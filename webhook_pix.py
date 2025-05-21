"""
Módulo para receber notificações de pagamentos Pix via webhook da OpenPix.
Este endpoint será registrado na plataforma OpenPix para receber notificações
quando um pagamento Pix for recebido.
"""

from flask import Flask, request, jsonify
import json
import os
import uuid
import os
from datetime import datetime

# Criar a pasta para armazenar os logs de notificações
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Função para salvar a notificação recebida em um arquivo de log
def salvar_notificacao(payload):
    """
    Salva a notificação recebida em um arquivo de log para análise posterior.
    
    Args:
        payload (dict): O payload da notificação recebida
    
    Returns:
        str: O caminho do arquivo onde a notificação foi salva
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    notification_id = str(uuid.uuid4())[:8]
    filename = f"pix_notification_{timestamp}_{notification_id}.json"
    filepath = os.path.join(LOGS_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(payload, f, indent=4)
    
    return filepath

# Função para processar a notificação de pagamento Pix
def processar_notificacao_pix(payload):
    """
    Processa a notificação de pagamento Pix recebida.
    
    Args:
        payload (dict): O payload da notificação recebida
    
    Returns:
        dict: Informações processadas do pagamento
    """
    # Extrair informações relevantes do payload
    try:
        # Verificar se o payload segue o formato da OpenPix
        if 'pix' in payload:
            # Formato OpenPix: dados dentro do objeto 'pix'
            pix_data = payload['pix']
            
            pix_info = {
                'status': pix_data.get('status', 'UNKNOWN'),
                'valor': pix_data.get('valor', 0),
                'txid': pix_data.get('txid', ''),
                'e2eid': pix_data.get('e2eid', ''),
                'horario': pix_data.get('horario', datetime.now().isoformat()),
                'infoPagador': pix_data.get('infoPagador', {}),
                'chave': pix_data.get('chave', ''),
                'notification_id': str(uuid.uuid4()),
                'event': payload.get('event', 'UNKNOWN')
            }
            
            # Informações adicionais da cobrança, se disponíveis
            if 'charge' in payload:
                charge_data = payload['charge']
                pix_info['charge'] = {
                    'correlationID': charge_data.get('correlationID', ''),
                    'value': charge_data.get('value', 0),
                    'comment': charge_data.get('comment', '')
                }
            
            # Verificar se é uma notificação de pagamento concluído
            if pix_info['status'] == 'CONCLUIDA' or pix_info['status'] == 'COMPLETED':
                # Aqui seria o ponto de integração com a conversão para cripto
                # Por enquanto, apenas registramos o evento
                print(f"Pagamento Pix recebido: {pix_info['valor']} - ID: {pix_info['txid']}")
                print(f"Pagador: {pix_info['infoPagador'].get('nome', 'N/A')}")
                print(f"Chave Pix: {pix_info['chave']}")
        else:
            # Formato genérico ou desconhecido
            pix_info = {
                'status': payload.get('status', 'UNKNOWN'),
                'valor': payload.get('valor', 0),
                'txid': payload.get('txid', ''),
                'e2eid': payload.get('e2eid', ''),
                'horario': payload.get('horario', datetime.now().isoformat()),
                'infoPagador': payload.get('infoPagador', {}),
                'chave': payload.get('chave', ''),
                'notification_id': str(uuid.uuid4()),
                'raw_payload': payload
            }
        
        return pix_info
    
    except Exception as e:
        print(f"Erro ao processar notificação: {str(e)}")
        return {
            'status': 'ERROR',
            'error': str(e),
            'raw_payload': payload
        }

# Configuração da aplicação Flask
app = Flask(__name__)

@app.route('/webhook/pix', methods=['POST'])
def webhook_pix():
    """
    Endpoint para receber notificações de pagamentos Pix da OpenPix.
    
    Returns:
        Response: Resposta HTTP para a requisição
    """
    try:
        # Receber o payload da requisição
        payload = request.json
        
        # Registrar a notificação recebida
        print(f"Notificação Pix recebida: {payload}")
        
        # Salvar a notificação para análise posterior
        log_path = salvar_notificacao(payload)
        print(f"Notificação salva em: {log_path}")
        
        # Processar a notificação
        resultado = processar_notificacao_pix(payload)
        
        # Responder com sucesso
        return jsonify({
            'status': 'success',
            'message': 'Notificação recebida com sucesso',
            'processamento': resultado
        }), 200
    
    except Exception as e:
        # Registrar o erro
        print(f"Erro ao processar webhook: {str(e)}")
        
        # Responder com erro
        return jsonify({
            'status': 'error',
            'message': f'Erro ao processar notificação: {str(e)}'
        }), 500

@app.route('/webhook/pix/status', methods=['GET'])
def webhook_status():
    """
    Endpoint para verificar o status do serviço de webhook.
    
    Returns:
        Response: Resposta HTTP com o status do serviço
    """
    # Listar as últimas notificações recebidas
    try:
        arquivos = os.listdir(LOGS_DIR)
        arquivos.sort(reverse=True)  # Ordenar por mais recentes
        ultimas_notificacoes = arquivos[:10]  # Pegar as 10 últimas
        
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

# Rota principal para documentação
@app.route('/', methods=['GET'])
def index():
    """
    Página principal com informações sobre o serviço.
    
    Returns:
        str: HTML com informações sobre o serviço
    """
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
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
