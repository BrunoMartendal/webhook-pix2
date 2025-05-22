import os
import json
import uuid
from datetime import datetime

# Define o diretório onde os dados serão armazenados
if 'RENDER' in os.environ:
    DATA_DIR = '/tmp'
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

CHAVES_FILE = os.path.join(DATA_DIR, 'chaves_pix.json')

# Garante que o diretório de dados exista
os.makedirs(DATA_DIR, exist_ok=True)

def carregar_chaves_pix():
    """Carrega as chaves Pix do arquivo JSON ou cria padrão se não existir."""
    if os.path.exists(CHAVES_FILE):
        try:
            with open(CHAVES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERRO carregar_chaves_pix] {e}")
            return criar_chaves_padrao()
    else:
        return criar_chaves_padrao()

def salvar_chaves_pix(chaves):
    """Salva a lista de chaves Pix no arquivo JSON."""
    try:
        with open(CHAVES_FILE, 'w', encoding='utf-8') as f:
            json.dump(chaves, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERRO salvar_chaves_pix] {e}")
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
    salvar_chaves_pix(chaves_padrao)
    return chaves_padrao

def adicionar_chave_pix(descricao, tipo_chave, chave):
    """Adiciona uma nova chave Pix e salva no arquivo."""
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
        raise Exception("Falha ao salvar chaves Pix")
    return nova_chave

def remover_chave_pix(chave_id):
    """Remove uma chave Pix pelo ID e salva a lista atualizada."""
    chaves = carregar_chaves_pix()
    chaves_filtradas = [c for c in chaves if c['id'] != chave_id]
    if len(chaves_filtradas) != len(chaves):
        salvar_chaves_pix(chaves_filtradas)
        return True
    return False
