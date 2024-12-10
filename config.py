import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    
    # 数据库配置
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST') or 'localhost',
        'user': os.environ.get('DB_USER') or 'root',
        'password': os.environ.get('DB_PASSWORD') or 'Qwe!@#123',
        'db': os.environ.get('DB_NAME') or 'yjsds2',
        'charset': 'utf8mb4',
        'cursorclass': 'DictCursor'
    }
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 