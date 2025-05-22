import os
import json
import uuid
from datetime import datetime

# Diretório para armazenar o arquivo de chaves Pix
# No Render, é melhor usar um diretório temporário que tenha permissões de escrita garantidas
if 'RENDER' in os.environ:
    # No Render, use o diretório /tmp que tem permissões de escrita
    DATA_DIR = '/tmp'
else:
    # Em ambiente local, use o diretório data na raiz do projeto
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

CHAVES_FILE = os.path.join(DATA_DIR, 'chaves_pix.json')

# Garantir que o diretório de dados exista
os.makedirs(DATA_DIR, exist_ok=True)

def carregar_chaves_pix():
    """Carrega as chaves Pix do arquivo JSON. Se o arquivo não existir, cria chaves padrão."""
    if os.path.exists(CHAVES_FILE):
        try:
            with open(CHAVES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            print(f"Erro ao carregar chaves Pix: {e}")
            return criar_chaves_padrao()
    else:
        return criar_chaves_padrao()

def salvar_chaves_pix(chaves):
    """Salva as chaves Pix no arquivo JSON."""
    try:
        # Garantir que o diretório exista antes de tentar escrever
        os.makedirs(os.path.dirname(CHAVES_FILE), exist_ok=True)
        
        with open(CHAVES_FILE, 'w', encoding='utf-8') as f:
            json.dump(chaves, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar chaves Pix: {e}")
        # Em caso de erro, tente salvar em um local alternativo
        try:
            fallback_file = os.path.join('/tmp', 'chaves_pix_fallback.json')
            with open(fallback_file, 'w', encoding='utf-8') as f:
                json.dump(chaves, f, indent=4, ensure_ascii=False)
            print(f"Chaves salvas no arquivo alternativo: {fallback_file}")
            return True
        except Exception as fallback_error:
            print(f"Erro ao salvar no local alternativo: {fallback_error}")
            return False

def criar_chaves_padrao():
    """Cria chaves Pix padrão para novos usuários."""
    chaves_padrao = [
        {
            'id': str(uuid.uuid4()),
            'descricao': 'Principal',
            'tipo_chave': 'E-mail',
            'chave': 'exemplo@pix.com',
            'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M')
        },
        {
            'id': str(uuid.uuid4()),
            'descricao': 'Conta PJ',
            'tipo_chave': 'Telefone',
            'chave': '+55 47 99622-9999',
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
    salvar_chaves_pix(chaves)
    return nova_chave

def remover_chave_pix(chave_id):
    """Remove uma chave Pix pelo ID e salva o arquivo atualizado."""
    chaves = carregar_chaves_pix()
    chaves_atualizadas = [ch for ch in chaves if ch['id'] != chave_id]
    
    if len(chaves) != len(chaves_atualizadas):
        salvar_chaves_pix(chaves_atualizadas)
        return True
    return False
