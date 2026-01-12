"""
Conversor WebP para JPEG – Aplicação Web

Aplicação web desenvolvida em Flask para conversão de imagens no formato WebP
para JPEG. Suporta conversões individuais e em lote, incluindo ficheiros
comprimidos (ZIP, RAR e 7Z).

Desenvolvido com assistência de IA (GitHub Copilot)
Autor: user1702
Data: Janeiro de 2026
"""

from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import os
import zipfile
import rarfile
import py7zr

# ============================================================================
# CONFIGURAÇÕES GERAIS
# ============================================================================

JPEG_QUALITY = 100  # Qualidade da imagem JPEG (0–100)
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # Limite máximo de upload (500 MB)
SUPPORTED_ARCHIVES = ('.zip', '.rar', '.7z')  # Formatos de ficheiros comprimidos suportados
WEBP_EXTENSION = '.webp'  # Extensão de ficheiros WebP

# ============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO FLASK
# ============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE


# ============================================================================
# CONVERSÃO DE IMAGENS
# ============================================================================

def convert_to_rgb(image):
    """
    Garante que a imagem se encontra no modo RGB.
    Necessário porque o formato JPEG não suporta transparência.

    Args:
        image (PIL.Image): Imagem de entrada

    Returns:
        PIL.Image: Imagem convertida para RGB, se aplicável
    """
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))

        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)

        return background

    return image


def convert_webp_to_jpeg(webp_data):
    """
    Converte uma imagem WebP em JPEG.

    Args:
        webp_data (bytes): Conteúdo binário da imagem WebP

    Returns:
        bytes: Conteúdo binário da imagem JPEG convertida
    """
    image = Image.open(io.BytesIO(webp_data))
    image = convert_to_rgb(image)

    output = io.BytesIO()
    image.save(output, 'JPEG', quality=JPEG_QUALITY)
    output.seek(0)

    return output.getvalue()


# ============================================================================
# EXTRACÇÃO DE FICHEIROS COMPRIMIDOS
# ============================================================================

def extract_webp_from_archive(file_data, filename):
    """
    Extrai imagens WebP de um ficheiro comprimido suportado.

    Args:
        file_data (bytes): Conteúdo binário do ficheiro comprimido
        filename (str): Nome do ficheiro para identificação do formato

    Returns:
        list: Lista de tuplos (nome_ficheiro, dados_webp)
    """
    images = []
    filename = filename.lower()

    try:
        if filename.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(file_data)) as archive:
                images = _extract_from_zip(archive)

        elif filename.endswith('.rar'):
            with rarfile.RarFile(io.BytesIO(file_data)) as archive:
                images = _extract_from_rar(archive)

        elif filename.endswith('.7z'):
            with py7zr.SevenZipFile(io.BytesIO(file_data)) as archive:
                images = _extract_from_7z(archive)

    except Exception as e:
        print(f"Erro ao processar o arquivo {filename}: {e}")

    return images


def _extract_from_zip(archive):
    """Extrai ficheiros WebP de um arquivo ZIP."""
    images = []
    for name in archive.namelist():
        if name.lower().endswith(WEBP_EXTENSION):
            images.append((os.path.basename(name), archive.read(name)))
    return images


def _extract_from_rar(archive):
    """Extrai ficheiros WebP de um arquivo RAR."""
    images = []
    for name in archive.namelist():
        if name.lower().endswith(WEBP_EXTENSION):
            images.append((os.path.basename(name), archive.read(name)))
    return images


def _extract_from_7z(archive):
    """Extrai ficheiros WebP de um arquivo 7Z."""
    images = []
    files = archive.readall()
    for name, bio in files.items():
        if name.lower().endswith(WEBP_EXTENSION):
            images.append((os.path.basename(name), bio.read()))
    return images


# ============================================================================
# PROCESSAMENTO DE FICHEIROS
# ============================================================================

def process_archive_file(uploaded_file):
    """
    Processa um ficheiro comprimido e converte todas as imagens WebP encontradas.

    Args:
        uploaded_file (FileStorage): Ficheiro enviado pelo utilizador

    Returns:
        list: Lista de tuplos (nome_jpeg, dados_jpeg)
    """
    converted_images = []
    file_data = uploaded_file.read()

    webp_images = extract_webp_from_archive(file_data, uploaded_file.filename)

    for name, webp_data in webp_images:
        try:
            jpeg_data = convert_webp_to_jpeg(webp_data)
            output_name = os.path.splitext(name)[0] + '.jpg'
            converted_images.append((output_name, jpeg_data))
        except Exception as e:
            print(f"Erro ao converter {name}: {e}")

    return converted_images


def process_webp_file(uploaded_file):
    """
    Processa um ficheiro WebP individual.

    Args:
        uploaded_file (FileStorage): Ficheiro WebP

    Returns:
        list: Lista com um único ficheiro convertido ou vazia em caso de erro
    """
    try:
        jpeg_data = convert_webp_to_jpeg(uploaded_file.read())
        output_name = os.path.splitext(uploaded_file.filename)[0] + '.jpg'
        return [(output_name, jpeg_data)]
    except Exception as e:
        print(f"Erro ao converter {uploaded_file.filename}: {e}")
        return []


# ============================================================================
# RESPOSTAS HTTP
# ============================================================================

def create_zip_response(converted_images):
    """
    Cria um ficheiro ZIP em memória com as imagens convertidas.

    Args:
        converted_images (list): Lista de imagens JPEG convertidas

    Returns:
        Response: Resposta HTTP com o ficheiro ZIP
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, data in converted_images:
            zip_file.writestr(filename, data)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='imagens_convertidas.zip'
    )


# ============================================================================
# ROTAS DA APLICAÇÃO
# ============================================================================

@app.route('/')
def index():
    """Renderiza a página principal da aplicação."""
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """
    Endpoint responsável pela conversão de ficheiros enviados pelo utilizador.
    """
    files = request.files.getlist('files')

    if not files:
        return 'Nenhum ficheiro enviado', 400

    converted_images = []

    for file in files:
        if not file.filename:
            continue

        name = file.filename.lower()

        if name.endswith(SUPPORTED_ARCHIVES):
            converted_images.extend(process_archive_file(file))
        elif name.endswith(WEBP_EXTENSION):
            converted_images.extend(process_webp_file(file))

    if not converted_images:
        return 'Nenhum ficheiro WebP válido encontrado', 400

    if len(converted_images) == 1:
        filename, data = converted_images[0]
        return send_file(
            io.BytesIO(data),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=filename
        )

    return create_zip_response(converted_images)


# ============================================================================
# EXECUÇÃO DA APLICAÇÃO
# ============================================================================

if __name__ == '__main__':
    # Modo debug activo apenas para ambiente de desenvolvimento
    app.run(debug=True)
