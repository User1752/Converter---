""".
Conversor de WebP para JPEG - Aplicação Web

Este aplicativo Flask permite converter imagens WebP para JPEG através de uma interface web.
Suporta conversão de arquivos individuais ou em lote, incluindo arquivos compactados.

Desenvolvido com assistência de IA (GitHub Copilot)
Autor: henri
Data: Janeiro 2026
"""

from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import os
import zipfile
import rarfile
import py7zr

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

JPEG_QUALITY = 100  # Qualidade da conversão JPEG (0-100, onde 100 é máxima)
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # Tamanho máximo de upload: 500MB
SUPPORTED_ARCHIVES = ('.zip', '.rar', '.7z')  # Formatos de arquivo compactado suportados
WEBP_EXTENSION = '.webp'  # Extensão de arquivo WebP

# ============================================================================
# INICIALIZAÇÃO DO APLICATIVO FLASK
# ============================================================================

app = Flask(__name__)
# Define o tamanho máximo de arquivo que pode ser enviado ao servidor
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE


# ============================================================================
# FUNÇÕES DE CONVERSÃO DE IMAGEM
# ============================================================================

def convert_to_rgb(image):
    """
    Converte imagem para RGB se necessário (JPEG não suporta transparência).
    
    Args:
        image: Objeto PIL Image a ser convertido
        
    Returns:
        Imagem convertida para RGB ou imagem original se já estiver em RGB
        
    Nota:
        - RGBA: Imagem com canal alpha (transparência)
        - LA: Escala de cinza com alpha
        - P: Imagem com paleta de cores
        Todas essas são convertidas para RGB com fundo branco
    """
    if image.mode in ('RGBA', 'LA', 'P'):
        # Cria uma nova imagem RGB com fundo branco
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        
        if image.mode == 'RGBA':
            # Para imagens RGBA, usa o canal alpha como máscara
            rgb_image.paste(image, mask=image.split()[-1])
        else:
            # Para outros modos, cola diretamente
            rgb_image.paste(image)
        
        return rgb_image
    
    # Se já estiver em RGB, retorna sem modificações
    return image


def convert_webp_to_jpeg(webp_data):
    """
    Converte dados WebP para JPEG e retorna bytes.
    
    Args:
        webp_data: Dados binários do arquivo WebP (bytes ou BytesIO)
        
    Returns:
        Dados binários do arquivo JPEG convertido (bytes)
        
    Raises:
        Exception: Se houver erro ao abrir ou converter a imagem
    """
    # Abre a imagem WebP a partir dos dados binários
    image = Image.open(io.BytesIO(webp_data))
    
    # Converte para RGB se necessário (remove transparência)
    image = convert_to_rgb(image)
    
    # Cria um buffer de bytes para armazenar a imagem convertida
    output = io.BytesIO()
    
    # Salva a imagem como JPEG no buffer com qualidade máxima
    image.save(output, 'JPEG', quality=JPEG_QUALITY)
    
    # Volta para o início do buffer para leitura
    output.seek(0)
    
    # Retorna os dados binários do JPEG
    return output.getvalue()


# ============================================================================
# FUNÇÕES DE EXTRAÇÃO DE ARQUIVOS COMPACTADOS
# ============================================================================

def extract_webp_from_archive(file_data, filename):
    """
    Extrai imagens WebP de arquivos ZIP, RAR ou 7Z.
    
    Args:
        file_data: Dados binários do arquivo compactado
        filename: Nome do arquivo para identificar o tipo
        
    Returns:
        Lista de tuplas (nome_arquivo, dados_binarios) com as imagens WebP encontradas
        
    Nota:
        Esta função serve como dispatcher, delegando para funções específicas
        de acordo com o tipo de arquivo compactado.
    """
    images = []
    file_lower = filename.lower()
    
    try:
        # Identifica o tipo de arquivo e chama a função apropriada
        if file_lower.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(file_data), 'r') as archive:
                images = _extract_from_zip(archive)
        
        elif file_lower.endswith('.rar'):
            with rarfile.RarFile(io.BytesIO(file_data), 'r') as archive:
                images = _extract_from_rar(archive)
        
        elif file_lower.endswith('.7z'):
            with py7zr.SevenZipFile(io.BytesIO(file_data), 'r') as archive:
                images = _extract_from_7z(archive)
    
    except Exception as e:
        # Registra o erro no console, mas não interrompe o processamento
        print(f"Erro ao extrair arquivo {filename}: {str(e)}")
    
    return images


def _extract_from_zip(archive):
    """
    Extrai arquivos WebP de um arquivo ZIP.
    
    Args:
        archive: Objeto ZipFile aberto
        
    Returns:
        Lista de tuplas (nome_base_arquivo, dados_webp)
    """
    images = []
    # Percorre todos os arquivos dentro do ZIP
    for file_name in archive.namelist():
        # Verifica se é um arquivo WebP
        if file_name.lower().endswith(WEBP_EXTENSION):
            # Lê o conteúdo do arquivo
            webp_data = archive.read(file_name)
            # Adiciona apenas o nome do arquivo (sem caminho) e seus dados
            images.append((os.path.basename(file_name), webp_data))
    return images


def _extract_from_rar(archive):
    """
    Extrai arquivos WebP de um arquivo RAR.
    
    Args:
        archive: Objeto RarFile aberto
        
    Returns:
        Lista de tuplas (nome_base_arquivo, dados_webp)
    """
    images = []
    # Percorre todos os arquivos dentro do RAR
    for file_name in archive.namelist():
        # Verifica se é um arquivo WebP
        if file_name.lower().endswith(WEBP_EXTENSION):
            # Lê o conteúdo do arquivo
            webp_data = archive.read(file_name)
            # Adiciona apenas o nome do arquivo (sem caminho) e seus dados
            images.append((os.path.basename(file_name), webp_data))
    return images


def _extract_from_7z(archive):
    """
    Extrai arquivos WebP de um arquivo 7Z.
    
    Args:
        archive: Objeto SevenZipFile aberto
        
    Returns:
        Lista de tuplas (nome_base_arquivo, dados_webp)
        
    Nota:
        7Z funciona diferente - readall() retorna um dicionário com todos os arquivos
    """
    images = []
    # Lê todos os arquivos do 7Z de uma vez
    all_files = archive.readall()
    # Percorre o dicionário de arquivos
    for file_name, bio in all_files.items():
        # Verifica se é um arquivo WebP
        if file_name.lower().endswith(WEBP_EXTENSION):
            # bio é um objeto BytesIO, então lemos seu conteúdo
            images.append((os.path.basename(file_name), bio.read()))
    return images


# ============================================================================
# FUNÇÕES DE PROCESSAMENTO DE ARQUIVOS
# ============================================================================

def process_archive_file(uploaded_file):
    """
    Processa um arquivo compactado e retorna lista de imagens convertidas.
    
    Args:
        uploaded_file: Objeto FileStorage do Flask com o arquivo enviado
        
    Returns:
        Lista de tuplas (nome_jpeg, dados_jpeg) com as imagens convertidas
        
    Processo:
        1. Lê o arquivo compactado
        2. Extrai todos os arquivos WebP
        3. Converte cada um para JPEG
        4. Retorna lista com os JPEGs convertidos
    """
    converted = []
    
    # Lê todo o conteúdo do arquivo compactado para memória
    file_data = uploaded_file.read()
    
    # Extrai todas as imagens WebP do arquivo
    extracted_images = extract_webp_from_archive(file_data, uploaded_file.filename)
    
    # Converte cada imagem WebP para JPEG
    for filename, webp_data in extracted_images:
        try:
            # Converte WebP para JPEG
            jpeg_data = convert_webp_to_jpeg(webp_data)
            
            # Gera o nome do arquivo de saída (troca .webp por .jpg)
            output_name = os.path.splitext(filename)[0] + '.jpg'
            
            # Adiciona à lista de convertidos
            converted.append((output_name, jpeg_data))
        except Exception as e:
            # Se falhar, registra erro mas continua processando outros arquivos
            print(f"Erro ao converter {filename}: {str(e)}")
    
    return converted


def process_webp_file(uploaded_file):
    """
    Processa um arquivo WebP individual.
    
    Args:
        uploaded_file: Objeto FileStorage do Flask com o arquivo WebP
        
    Returns:
        Lista com uma tupla (nome_jpeg, dados_jpeg) ou lista vazia se houver erro
    """
    try:
        # Lê o arquivo e converte para JPEG
        jpeg_data = convert_webp_to_jpeg(uploaded_file.read())
        
        # Gera o nome do arquivo de saída
        output_name = os.path.splitext(uploaded_file.filename)[0] + '.jpg'
        
        # Retorna como lista para manter consistência com process_archive_file
        return [(output_name, jpeg_data)]
    except Exception as e:
        # Se falhar, registra erro e retorna lista vazia
        print(f"Erro ao converter {uploaded_file.filename}: {str(e)}")
        return []


# ============================================================================
# FUNÇÕES DE RESPOSTA HTTP
# ============================================================================

def create_zip_response(converted_images):
    """
    Cria um arquivo ZIP com as imagens convertidas e retorna como resposta HTTP.
    
    Args:
        converted_images: Lista de tuplas (nome_arquivo, dados_jpeg)
        
    Returns:
        Objeto de resposta Flask com o arquivo ZIP para download
        
    Nota:
        O ZIP é criado em memória (BytesIO) para não precisar salvar em disco
    """
    # Cria um buffer de bytes para o arquivo ZIP
    zip_buffer = io.BytesIO()
    
    # Cria o arquivo ZIP em modo de escrita com compressão
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Adiciona cada imagem convertida ao ZIP
        for filename, img_data in converted_images:
            zip_file.writestr(filename, img_data)
    
    # Volta para o início do buffer para leitura
    zip_buffer.seek(0)
    
    # Retorna o arquivo para download
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='converted_images.zip'
    )


# ============================================================================
# ROTAS DO APLICATIVO FLASK
# ============================================================================

@app.route('/')
def index():
    """
    Rota principal que renderiza a página HTML do conversor.
    
    Returns:
        Página HTML renderizada (index.html)
    """
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """
    Endpoint para conversão de WebP para JPEG.
    
    Aceita:
        - Arquivos .webp individuais
        - Múltiplos arquivos .webp
        - Arquivos compactados (.zip, .rar, .7z) contendo .webp
        
    Returns:
        - Arquivo JPEG único se apenas 1 imagem for convertida
        - Arquivo ZIP contendo múltiplos JPEGs se mais de 1 imagem for convertida
        - Erro 400 se nenhum arquivo válido for encontrado
        
    Método HTTP: POST
    Form data: files (array de arquivos)
    """
    # Obtém a lista de arquivos enviados pelo formulário
    files = request.files.getlist('files')
    
    # Valida se algum arquivo foi enviado
    if not files:
        return 'Nenhum arquivo enviado', 400
    
    # Lista para armazenar as imagens convertidas
    converted_images = []
    
    # Processa cada arquivo enviado
    for uploaded_file in files:
        # Ignora arquivos sem nome (campos vazios)
        if not uploaded_file.filename:
            continue
        
        # Converte o nome para minúsculas para comparação
        filename_lower = uploaded_file.filename.lower()
        
        # Processa arquivos compactados (ZIP, RAR, 7Z)
        if filename_lower.endswith(SUPPORTED_ARCHIVES):
            # Extrai e converte todos os WebP do arquivo compactado
            converted_images.extend(process_archive_file(uploaded_file))
        
        # Processa arquivos WebP individuais
        elif filename_lower.endswith(WEBP_EXTENSION):
            # Converte o arquivo WebP individual
            converted_images.extend(process_webp_file(uploaded_file))
    
    # Valida se alguma imagem foi convertida com sucesso
    if not converted_images:
        return 'Nenhum arquivo .webp válido encontrado', 400
    
    # Se apenas 1 imagem foi convertida, retorna o JPEG diretamente
    if len(converted_images) == 1:
        filename, img_data = converted_images[0]
        return send_file(
            io.BytesIO(img_data),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=filename
        )
    
    # Se múltiplas imagens foram convertidas, retorna como ZIP
    return create_zip_response(converted_images)


# ============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================================

if __name__ == '__main__':
    # Inicia o servidor Flask em modo debug
    # Debug=True permite:
    # - Recarregamento automático ao modificar o código
    # - Mensagens de erro detalhadas no navegador
    # - Console interativo em caso de erros
    # ATENÇÃO: Nunca use debug=True em produção!
    app.run(debug=True)