import os
import json
import uuid
from datetime import datetime
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

# Define o diretório onde os dados serão armazenados
if 'RENDER' in os.environ:
    DATA_DIR = '/tmp'
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

CHAVES_FILE = os.path.join(DATA_DIR, 'chaves_pix.json')

# Garante que o diretório de dados exista
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"Diretório de dados configurado: {DATA_DIR}")

def carregar_chaves_pix():
    """Carrega as chaves Pix do arquivo JSON ou cria padrão se não existir."""
    logger.info(f"Tentando carregar chaves de {CHAVES_FILE}")
    if os.path.exists(CHAVES_FILE):
        try:
            with open(CHAVES_FILE, 'r', encoding='utf-8') as f:
                chaves = json.load(f)
                logger.info(f"Chaves carregadas: {json.dumps(chaves, indent=4)}")
                return chaves
        except Exception as e:
            logger.error(f"Erro ao carregar chaves_pix: {str(e)}")
            return criar_chaves_padrao()
    else:
        logger.info(f"Arquivo {CHAVES_FILE} não existe, criando chaves padrão")
        return criar_chaves_padrao()

def salvar_chaves_pix(chaves):
    """Salva a lista de chaves Pix no arquivo JSON."""
    logger.info(f"Tentando salvar chaves em {CHAVES_FILE}")
    try:
        with open(CHAVES_FILE, 'w', encoding='utf-8') as f:
            json.dump(chaves, f, indent=4, ensure_ascii=False)
        logger.info(f"Chaves salvas com sucesso em {CHAVES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar chaves_pix: {str(e)}")
        return False

def criar_chaves_padrao():
    """Cria uma lista padrão de chaves Pix."""
    chaves_padrao = [
        {
            'id': str(uuid.uuid4()),
            'descricao': 'Principal',
            'tipo_chave': 'E-mail',
            'chave': 'exemplo@pix.com',
            'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
    ]
    logger.info(f"Criando chaves padrão: {json.dumps(chaves_padrao, indent=4)}")
    salvar_chaves_pix(chaves_padrao)
    return chaves_padrao

def adicionar_chave_pix(descricao, tipo_chave, chave):
    """Adiciona uma nova chave Pix e salva no arquivo."""
    logger.info(f"Adicionando chave: descricao={descricao}, tipo_chave={tipo_chave}, chave={chave}")
    chaves = carregar_chaves_pix()
    nova_chave = {
        'id': str(uuid.uuid4()),
        'descricao': descricao,
        'tipo_chave': tipo_chave,
        'chave': chave,
        'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    chaves.append(nova_chave)
    if not salvar_chaves_pix(chaves):
        logger.error("Falha ao salvar chaves Pix")
        raise Exception("Falha ao salvar chaves Pix")
    logger.info(f"Chave adicionada com sucesso: {json.dumps(nova_chave, indent=4)}")
    return nova_chave

def remover_chave_pix(chave_id):
    """Remove uma chave Pix pelo ID e salva a lista atualizada."""
    logger.info(f"Tentando remover chave com ID: {chave_id}")
    chaves = carregar_chaves_pix()
    chaves_filtradas = [c for c in chaves if c['id'] != chave_id]
    if len(chaves_filtradas) != len(chaves):
        if salvar_chaves_pix(chaves_filtradas):
            logger.info(f"Chave com ID {chave_id} removida com sucesso")
            return True
        else:
            logger.error("Falha ao salvar chaves após remoção")
            return False
    logger.warning(f"Chave com ID {chave_id} não encontrada")
    return False
