import os
import configparser
from pathlib import Path

def get_config():
    """
    設定ファイルを読み込む関数
    
    Returns:
        configparser.ConfigParser: 設定オブジェクト
    """
    config = configparser.ConfigParser()
    
    # 現在のファイルからの相対パスでconfig.iniを探す
    base_dir = Path(__file__).parent.parent
    config_path = os.path.join(base_dir, 'config.ini')
    
    # 設定ファイルを読み込む
    config.read(config_path, encoding='utf-8')
    
    return config
