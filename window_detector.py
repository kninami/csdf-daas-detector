import winreg
import os
import json
import datetime

def create_json_entry(file_type, file_name, file_path, content, created_time, modified_time):
    return {
        "file_type": file_type,
        "file_name": file_name,
        "file_path": file_path,
        "content": content,
        "created_time": created_time,
        "modified_time": modified_time
    }

def read_registry_value(input_data):
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

def read_local_appdata(input_data):
    local_app_data = os.environ['LOCALAPPDATA']
    parent_folder = os.path.join(local_app_data, input_data["parentDirectory"])
    
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

def get_file_dates(file_path):
    stat = os.stat(file_path)
    
    created = stat.st_ctime if hasattr(stat, 'st_birthtime') else stat.st_mtime
    modified = stat.st_mtime

    created_date = datetime.datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S')
    modified_date = datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')

    return created_date, modified_date

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
                # 파일 날짜 정보 가져오기
                result["created_date"], result["modified_date"] = get_file_dates(file_path)
                with open(file_path, 'r') as file:
                    file_content = json.load(file)
                    extracted_data = extract_keys(file_content, file_info["keys"])                    
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
        ]
    }

    registry, reg_error = read_registry_value(input_data)
    appdata, appdata_error = read_local_appdata(input_data) 
    results = []
    
    if reg_error:
        print(f"Registry error: {reg_error}")
    else:
        results.append(create_json_entry(
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
        results.append(create_json_entry(
            "AppData",
            "File Tree",
            appdata["path"],
            appdata["folder_tree"],
            "",
            ""
        ))

        results.extend([
            create_json_entry(
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
        ]
    }

    registry, reg_error = read_registry_value(input_data)
    appdata, appdata_error = read_local_appdata(input_data) 
    results = []
    
    if reg_error:
        print(f"Registry error: {reg_error}")
    else:
        results.append(create_json_entry(
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
        results.append(create_json_entry(
            "AppData",
            "File Tree",
            appdata["path"],
            appdata["folder_tree"],
            "",
            ""
        ))

        results.extend([
            create_json_entry(
                "AppData",
                setting_data["file_name"],
                setting_data["file_path"],
                setting_data["content"],
                setting_data["created_date"],
                setting_data["modified_date"]
            ) for setting_data in appdata["settings_data"]
        ])

    for result in results:
        print(result)
