import os
import json
import uuid
from datetime import datetime

# Define o diretório de dados
if 'RENDER' in os.environ:
    DATA_DIR = '/tmp'
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

CHAVES_FILE = os.path.join(DATA_DIR, 'chaves_pix.json')
os.makedirs(DATA_DIR, exist_ok=True)

def carregar_chaves_pix():
    print(f"[INFO] Tentando carregar chaves Pix de {CHAVES_FILE}")
    if os.path.exists(CHAVES_FILE):
        try:
            with open(CHAVES_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"[INFO] Conteúdo do arquivo: {content}")
                return json.loads(content)
        except Exception as e:
            print(f"[ERRO] Falha ao carregar chaves Pix: {e}")
            return criar_chaves_padrao()
    else:
        print("[INFO] Arquivo de chaves Pix não encontrado, criando padrão")
        return criar_chaves_padrao()

def salvar_chaves_pix(chaves):
    try:
        print(f"[INFO] Salvando chaves Pix: {json.dumps(chaves, indent=4)}")
        with open(CHAVES_FILE, 'w', encoding='utf-8') as f:
            json.dump(chaves, f, indent=4, ensure_ascii=False)
        print("[INFO] Chaves Pix salvas com sucesso")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao salvar chaves Pix: {e}")
        return False

def criar_chaves_padrao():
    chaves_padrao = [{
        'id': str(uuid.uuid4()),
        'descricao': 'Principal',
        'tipo_chave': 'E-mail',
        'chave': 'exemplo@pix.com',
        'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M')
    }]
    salvar_chaves_pix(chaves_padrao)
    return chaves_padrao

def adicionar_chave_pix(descricao, tipo_chave, chave):
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
