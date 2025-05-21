"""
Script para testar o endpoint webhook de notificações Pix.
Este script simula o envio de uma notificação de pagamento Pix
para o endpoint webhook implementado.
"""

import requests
import json
import uuid
from datetime import datetime

# URL do endpoint webhook (ajuste conforme necessário)
WEBHOOK_URL = "http://localhost:5001/webhook/pix"

# Função para gerar um payload de teste simulando uma notificação da OpenPix
def gerar_payload_teste():
    """
    Gera um payload de teste simulando uma notificação de pagamento Pix da OpenPix.
    
    Returns:
        dict: Payload de teste
    """
    # Gerar IDs únicos para a transação
    txid = str(uuid.uuid4())
    e2eid = f"E{str(uuid.uuid4()).replace('-', '')}"
    
    # Timestamp atual
    timestamp = datetime.now().isoformat()
    
    # Payload de exemplo baseado na documentação da OpenPix
    # Nota: A estrutura exata pode variar, este é um exemplo genérico
    payload = {
        "event": "OPENPIX:PIX_RECEIVED",
        "pix": {
            "status": "COMPLETED",
            "valor": 100.50,  # Valor em reais
            "txid": txid,
            "e2eid": e2eid,
            "horario": timestamp,
            "infoPagador": {
                "nome": "João da Silva",
                "cpf": "12345678900",  # CPF fictício
                "chave": "joao@exemplo.com"
            },
            "chave": "loja@criptofacil.com.br",
            "infoAdicionais": {
                "descricao": "Pagamento de teste"
            }
        },
        "charge": {
            "status": "COMPLETED",
            "correlationID": f"TESTE-{str(uuid.uuid4())[:8]}",
            "createdAt": timestamp,
            "updatedAt": timestamp,
            "value": 10050,  # Valor em centavos
            "comment": "Pagamento de teste via webhook",
            "expiresIn": 3600,
            "type": "DYNAMIC"
        },
        "account": {
            "clientId": "cliente-teste-123",
            "name": "Loja Teste"
        }
    }
    
    return payload

# Função para enviar a notificação de teste para o webhook
def enviar_notificacao_teste():
    """
    Envia uma notificação de teste para o endpoint webhook.
    
    Returns:
        dict: Resposta do servidor
    """
    # Gerar o payload de teste
    payload = gerar_payload_teste()
    
    # Imprimir o payload para referência
    print("Enviando payload de teste:")
    print(json.dumps(payload, indent=4))
    
    # Enviar a requisição POST para o webhook
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Verificar a resposta
        if response.status_code == 200:
            print(f"Notificação enviada com sucesso! Status: {response.status_code}")
            print("Resposta:")
            print(json.dumps(response.json(), indent=4))
            return response.json()
        else:
            print(f"Erro ao enviar notificação. Status: {response.status_code}")
            print("Resposta:")
            print(response.text)
            return {"status": "error", "message": response.text}
    
    except Exception as e:
        print(f"Exceção ao enviar notificação: {str(e)}")
        return {"status": "error", "message": str(e)}

# Função para verificar o status do webhook
def verificar_status_webhook():
    """
    Verifica o status do serviço de webhook.
    
    Returns:
        dict: Informações de status do webhook
    """
    try:
        response = requests.get(f"{WEBHOOK_URL}/status")
        
        if response.status_code == 200:
            print("Status do webhook:")
            print(json.dumps(response.json(), indent=4))
            return response.json()
        else:
            print(f"Erro ao verificar status. Status: {response.status_code}")
            print(response.text)
            return {"status": "error", "message": response.text}
    
    except Exception as e:
        print(f"Exceção ao verificar status: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Verificar o status do webhook
    print("Verificando status do webhook...")
    verificar_status_webhook()
    
    # Enviar uma notificação de teste
    print("\nEnviando notificação de teste...")
    enviar_notificacao_teste()
