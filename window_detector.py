import winreg
import os
import json
from datetime import datetime
import glob
import helper_functions

def get_cookies(input_data):
    target_folder, error = helper_functions.is_directory_exist(input_data)
    cookie_path_components = input_data["cookiePath"]
    cookies = []
    if not error:
        full_cookie_path = os.path.join(target_folder, *cookie_path_components)
        if os.path.exists(full_cookie_path):
            for file in os.listdir(full_cookie_path):
                if file == "Cookies":
                    file_path = os.path.join(full_cookie_path, file)
                    encryption_key = helper_functions.get_encryption_key() 
                    content = helper_functions.parse_cookie_file(full_cookie_path, encryption_key)
                    print(content)
                    cookies.append({
                        "file_type": "Cookie",
                        "file_name": file,
                        "file_path": file_path,
                        "content": content,
                        "created_date": get_file_date(file_path, 'created'),
                        "modified_date": get_file_date(file_path, 'modified')
                    })
    return cookies

def get_logs(input_data):
    target_folder, error = helper_functions.is_directory_exist(input_data)
    logs = []
    if not error:        
        log_path = os.path.join(target_folder, 'logs')
        if os.path.exists(log_path):
            for file in glob.glob(os.path.join(log_path, '*.log')):
                content = helper_functions.read_log_content(file)
                logs.append({
                    "file_type": "Log",
                    "file_name": os.path.basename(file),
                    "file_path": file,
                    "content": content,
                    "created_date": get_file_date(file, 'created'),
                    "modified_date": get_file_date(file, 'modified')
                })
    return logs

def get_local_registry(input_data):
    reg_path = input_data["registryPath"]
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        value_name, value_data, value_type = winreg.EnumValue(reg_key, 0)
        results = {
            "name": value_name,
            "data": value_data,
            "type": value_type
        }
        
        winreg.CloseKey(reg_key)
        return results, None
    except Exception as e:
        return None, e

def get_local_appdata(input_data):
    appdata_path = os.environ['LOCALAPPDATA']
    parent_folder = os.path.join(appdata_path, input_data["parentDirectory"])
    
    if not os.path.exists(parent_folder):
        return None, f"{str(parent_folder)} folder not found"
    
    target_folder = os.path.join(parent_folder, input_data["targetDirectory"])
    if not os.path.exists(target_folder):
        return None, f"{str(target_folder)} folder not found"
    
    try:
        result = {
            "path": target_folder,
            "folder_tree": explore_folder_tree(target_folder),
            "settings_data": get_settings_files(target_folder, input_data["settingsFiles"])
        }
        return result, None
    except Exception as e:
        return None, f"Error processing data: {str(e)}"

def get_file_date(file_path, date_type):
    if os.path.exists(file_path):
        if date_type == 'created':
            return datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        elif date_type == 'modified':
            return datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    return ""

def get_settings_files(target_folder, settings_files):
    results = []
    for file_info in settings_files:
        result = {
            "file_name": file_info["fileName"],
            "file_path": target_folder,
            "extract_flag": False,
            "content": "",
            "error_flag": False,
            "error_msg": "",
            "created_date": "",
            "modified_date": ""
        }
        
        file_path = os.path.join(target_folder, result["file_name"])
        if os.path.exists(file_path):
            try:
                result["created_date"] = get_file_date(file_path, 'created')
                result["modified_date"] = get_file_date(file_path, 'modified')
                
                with open(file_path, 'r') as file:
                    file_content = json.load(file)
                    extracted_data = helper_functions.extract_keys(file_content, file_info["keys"])                    
                    if extracted_data:
                        result["extract_flag"] = True
                        result["content"] = json.dumps(extracted_data, indent=2)
                    else:
                        result["error_flag"] = True
                        result["error_msg"] = "No matching keys found"
            except Exception as e:
                result["error_flag"] = True
                result["error_msg"] = f"Error reading file: {str(e)}"
        else:
            result["error_flag"] = True
            result["error_msg"] = f"File does not exist: {file_path}"
        
        results.append(result)
    
    return results

def explore_folder_tree(folder_path, indent=""):
    result = []
    if os.path.exists(folder_path):
        result.append(f"{indent}{os.path.basename(folder_path)}:")
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                result.append(explore_folder_tree(item_path, indent + "  "))
            else:
                result.append(f"{indent}  {item}")
    
    return "\n".join(result)

def main():
    input_data = {
        "serviceName": "Amazon WorkSpaces",
        "targetDirectory": "Amazon WorkSpaces",
        "parentDirectory": "Amazon Web Services",
        "registryPath": "Software\\Amazon Web Services, LLC\\Amazon WorkSpaces",
        "settingsFiles": [
            {
                "fileName": "UserSettings.json",
                "keys": ["CurrentRegistration"]
            },
            {
                "fileName": "RegistrationList.json",
                "keys": ["RegistrationCode", "RegionKey", "OrgName"]
            }
        ],
        "cookiePath": ['webview2', 'EBWebView', 'Default', 'Network']
    }

    registry, reg_error = get_local_registry(input_data)
    appdata, appdata_error = get_local_appdata(input_data) 

    results = []    
    results.extend(get_logs(input_data))
    results.extend(get_cookies(input_data))
    
    if reg_error:
        print(f"Registry error: {reg_error}")
    else:
        results.append(helper_functions.create_json_entry(
            "Registry",
            input_data["registryPath"],
            fr"HKEY_CURRENT_USER\{input_data['registryPath']}",
            registry,
            "",
            ""
        ))

    if appdata_error:
        print(f"AppData error: {appdata_error}")
    elif appdata:
        results.append(helper_functions.create_json_entry(
            "AppData",
            "File Tree",
            appdata["path"],
            appdata["folder_tree"],
            "",
            ""
        ))

        results.extend([
            helper_functions.create_json_entry(
                "AppData",
                setting_data["file_name"],
                setting_data["file_path"],
                setting_data["content"],
                setting_data["created_date"],
                setting_data["modified_date"]
            ) for setting_data in appdata["settings_data"]
        ])

    return results

if __name__ == "__main__":
    main()
