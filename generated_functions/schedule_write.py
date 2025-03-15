import json, os, ast, time
import msvcrt
import importlib, sys
import schedule



#schedule.every().hour.do(update_hourly)
#schedule.every(30).minutes.do(update_every_30_minutes)
#schedule.every().day.at("00:00").do(update_daily)


def write_values():
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script folder
    sys.path.append(script_dir)
    data_extracted = {}
    result_list = []
    with open(os.path.join(script_dir, "display.json"), 'r') as file:
        data = json.load(file)

    for key, field in data.items():
        if field["display"] == 1:
            data_extracted[key] = field


    for key, field in data_extracted.items():
        arg = ast.literal_eval(field["args"])
        function = field["function"]
        print("arg", arg)
        print("function", function)
        module_name = function
        name_function = function
        module = importlib.import_module(module_name)
        func = getattr(module, name_function, None)

        if func:
            if field["update"] == "never":
                pass
            elif field["update"] == "once":
                result = func(*arg)
                field["value"] = result
                field["update"] = "never"
            else:
                result = func(*arg)
                field["value"] = result
        else:
            f"error calling {name_function} function"


    for key, field in data.items():  # Iterate over key-value pairs
        for key2, field2 in data_extracted.items():
            if key == key2:
                field = field2

    with open(os.path.join(script_dir, "display.json"), 'w') as file:
        size = os.path.getsize(os.path.join(script_dir, "display.json"))  # get the file size
        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, size)
        json.dump(data, file, indent=4)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, size)


if __name__ == "__main__":
    print(write_values())
