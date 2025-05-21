# Documentação da Integração de Notificações Pix via OpenPix

## Visão Geral

Este documento descreve a implementação de um sistema para detecção automática de recebimento de pagamentos Pix, utilizando a plataforma OpenPix como intermediária. A solução consiste em um endpoint webhook que recebe notificações em tempo real quando um pagamento Pix é realizado, permitindo a automação do fluxo de conversão para criptomoedas.

## Arquitetura da Solução

A solução implementada segue a seguinte arquitetura:

1. **Cliente** - Realiza um pagamento Pix para a chave do lojista
2. **Banco** - Processa o pagamento e notifica a OpenPix
3. **OpenPix** - Recebe a notificação do banco e envia para o webhook configurado
4. **Webhook** - Recebe, valida e processa a notificação
5. **Sistema de Conversão** - (Próxima etapa) Converte o valor recebido em criptomoeda

### Componentes Implementados

1. **Endpoint Webhook** (`webhook_pix.py`) - Servidor Flask que recebe as notificações da OpenPix
2. **Processador de Notificações** - Lógica para extrair e processar os dados do pagamento
3. **Sistema de Logs** - Armazenamento de todas as notificações recebidas para auditoria
4. **Simulador de Testes** (`test_webhook.py`) - Ferramenta para testar o webhook localmente

## Formato do Payload da OpenPix

A OpenPix envia notificações no seguinte formato JSON:

```json
{
    "event": "OPENPIX:PIX_RECEIVED",
    "pix": {
        "status": "COMPLETED",
        "valor": 100.50,
        "txid": "e12ca412-872b-43d4-aace-9db1fe394aa7",
        "e2eid": "Ee3d6c916d8e344af93ae50e96a842779",
        "horario": "2025-05-21T10:41:18.818571",
        "infoPagador": {
            "nome": "João da Silva",
            "cpf": "12345678900",
            "chave": "joao@exemplo.com"
        },
        "chave": "loja@criptofacil.com.br",
        "infoAdicionais": {
            "descricao": "Pagamento de teste"
        }
    },
    "charge": {
        "status": "COMPLETED",
        "correlationID": "TESTE-6d7800a4",
        "createdAt": "2025-05-21T10:41:18.818571",
        "updatedAt": "2025-05-21T10:41:18.818571",
        "value": 10050,
        "comment": "Pagamento de teste via webhook",
        "expiresIn": 3600,
        "type": "DYNAMIC"
    },
    "account": {
        "clientId": "cliente-teste-123",
        "name": "Loja Teste"
    }
}
```

### Campos Importantes

- `event`: Tipo de evento (ex: "OPENPIX:PIX_RECEIVED")
- `pix.status`: Status do pagamento ("COMPLETED" quando concluído)
- `pix.valor`: Valor do pagamento em reais
- `pix.txid`: Identificador da transação
- `pix.e2eid`: Identificador end-to-end do Pix
- `pix.infoPagador`: Informações sobre o pagador
- `pix.chave`: Chave Pix do recebedor
- `charge`: Informações sobre a cobrança

## Configuração do Webhook na OpenPix

Para configurar o webhook na plataforma OpenPix, siga os passos abaixo:

1. Acesse a plataforma OpenPix (https://app.openpix.com.br/)
2. Faça login com suas credenciais
3. Navegue até "Configurações" > "APIs" > "Webhooks"
4. Clique em "Criar Webhook"
5. Preencha os campos:
   - **Nome**: Nome descritivo para o webhook (ex: "Notificação Pix para Cripto")
   - **Evento**: Selecione "Pix recebido"
   - **URL**: URL pública do seu endpoint (ex: https://seu-dominio.com/webhook/pix)
   - **Ativo**: Marque como ativo
6. Salve as configurações

## Implementação do Endpoint Webhook

O endpoint webhook foi implementado usando Flask e está disponível no arquivo `webhook_pix.py`. Ele oferece as seguintes funcionalidades:

1. **Recebimento de Notificações** - Endpoint POST `/webhook/pix`
2. **Verificação de Status** - Endpoint GET `/webhook/pix/status`
3. **Documentação** - Página principal com informações sobre o serviço

### Processamento de Notificações

Quando uma notificação é recebida, o sistema:

1. Salva o payload completo em um arquivo de log para auditoria
2. Extrai as informações relevantes do pagamento
3. Verifica se o pagamento foi concluído com sucesso
4. Prepara os dados para a próxima etapa (conversão para cripto)

## Testes Realizados

O sistema foi testado usando um simulador local que envia payloads no formato da OpenPix. Os testes confirmaram que:

1. O endpoint recebe corretamente as notificações
2. O sistema processa e extrai os dados do pagamento
3. Os logs são gerados corretamente para auditoria
4. O endpoint responde com status 200 para notificações válidas

## Próximos Passos

Para completar a integração e automatizar o fluxo completo, os próximos passos são:

1. **Expor o Endpoint Publicamente** - Tornar o webhook acessível pela internet
2. **Cadastrar na OpenPix** - Configurar o webhook na plataforma OpenPix
3. **Implementar Integração com Corretora** - Conectar com APIs de corretoras como Binance
4. **Desenvolver Lógica de Conversão** - Implementar a conversão automática para criptomoedas
5. **Implementar Sistema de Notificação** - Notificar o lojista sobre o status da conversão

## Considerações de Segurança

Para garantir a segurança da integração, recomenda-se:

1. **Validação de Origem** - Implementar validação da origem das notificações
2. **HTTPS** - Usar apenas conexões seguras (HTTPS)
3. **Idempotência** - Garantir que pagamentos não sejam processados mais de uma vez
4. **Logs Detalhados** - Manter logs detalhados para auditoria e resolução de problemas

## Instruções de Uso

### Requisitos

- Python 3.6+
- Flask
- Requests (para testes)

### Instalação

1. Clone o repositório ou copie os arquivos para seu servidor
2. Instale as dependências:
   ```
   pip install flask requests
   ```
3. Configure o servidor para expor o endpoint publicamente
4. Inicie o servidor:
   ```
   python webhook_pix.py
   ```

### Testes Locais

Para testar localmente, use o script `test_webhook.py`:

```
python test_webhook.py
```

Este script simula o envio de uma notificação de pagamento Pix para o webhook local.

## Conclusão

A implementação do webhook para notificações Pix via OpenPix oferece uma solução prática e eficiente para a detecção automática de recebimentos Pix. Esta é a primeira etapa para a automação completa do fluxo de conversão para criptomoedas, permitindo que lojistas recebam pagamentos em Pix e automaticamente convertam para Bitcoin ou USDT.

A escolha da OpenPix como intermediária simplifica significativamente a implementação, eliminando a necessidade de lidar diretamente com certificados digitais e complexidades técnicas das APIs bancárias.
