import os
import sys
import msvcrt

class OrchidInterpreter:
    def __init__(self):
        self.last_write = ""
        self.hostname = ">>>"
        self.variables = {}
        self.skip_lines = False

    def execute_line(self, line, current_file="<input>"):
        try:
            line = line.strip()

            if self.skip_lines:
                if line == "" or line.startswith("//"):
                    return
                if "=" in line and any(k in line for k in ["Publisher Name", "ScriptName", "URL"]):
                    return
                self.skip_lines = False

            if line.startswith("[Publisher Information]"):
                self.skip_lines = True
                return

            if line.startswith("use "):
                self.handle_use(line[4:].strip())
            elif line.startswith("load "):
                self.handle_load(line[5:].strip())
            elif line == "help":
                self.print_help()
            elif line.startswith("let.var="):
                self.handle_variable(line[len("let.var="):])
            elif line.startswith("math.add="):
                self.handle_math(line[len("math.add="):], op="add")
            elif line.startswith("math.sub="):
                self.handle_math(line[len("math.sub="):], op="sub")
            elif line.startswith("exit.now="):
                value = line[len("exit.now="):].strip().strip('"')
                if value.lower() == "true":
                    print("Exiting Orchid...")
                    return
            elif line.startswith("if.equals="):
                self.handle_if_equals(line[len("if.equals="):])
            elif line.startswith("write="):
                content = line[len("write="):].strip().strip('"')
                self.last_write = content
                print(content)
            elif line.startswith("grape.spam="):
                count_str = line[len("grape.spam="):].strip().strip('"')
                if not count_str.isdigit():
                    raise ValueError(f"Invalid spam count: {count_str}")
                for _ in range(int(count_str)):
                    print(self.last_write)
            elif not line or line.startswith("//"):
                pass
            else:
                raise SyntaxError(f"Unrecognized syntax: {line}")

        except Exception as e:
            print("most recent call lasted")
            print(f"execption: {str(e)}")
            print("Press any key to continue...")
            self.wait_for_key_press()

    def handle_use(self, filename):
        self.load_script(filename, silent=True)

    def handle_load(self, filename):
        print(f"Loading script: {filename}")
        self.load_script(filename, silent=False)

    def load_script(self, filename, silent=False):
        if not filename.endswith(".orchid"):
            filename += ".orchid"

        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"No such file: {filename}")

            with open(filename, "r") as f:
                lines = f.readlines()

            publisher_info = self.parse_publisher_info(lines)
            if publisher_info:
                print("Do you want to load this script?")
                print(f"The publisher is {publisher_info.get('Publisher Name', 'Unknown')}")
            else:
                print("Do you want to load this script?")
                print("The Script publisher and information is unknown")

            confirm = input("[y/n]: ").lower()
            if confirm != "y":
                print("Cancelled.")
                return

            for line in lines:
                self.execute_line(line.strip(), current_file=filename)

            print(f"Script '{filename}' loaded successfully.")
        except Exception as e:
            print("most recent call lasted")
            print(f"execption: Failed to load script '{filename}': {str(e)}")
            print("Press any key to continue...")
            self.wait_for_key_press()

    def parse_publisher_info(self, lines):
        info = {}
        for i, line in enumerate(lines):
            if line.strip() == "[Publisher Information]":
                for info_line in lines[i+1:i+5]:
                    if "=" in info_line:
                        key, value = info_line.strip().split("=", 1)
                        info[key.strip()] = value.strip()
                return info if "Publisher Name" in info else None
        return None

    def handle_variable(self, declaration):
        if ":" not in declaration:
            raise ValueError("Expected format: name:value")
        name, value = map(str.strip, declaration.strip('"').split(":", 1))
        self.variables[name] = value

    def handle_math(self, expression, op):
        try:
            if op == "add":
                x, y = map(float, expression.strip('"').split("+"))
                result = x + y
            elif op == "sub":
                x, y = map(float, expression.strip('"').split("-"))
                result = x - y
            else:
                raise ValueError("Unknown math operation")
            print(int(result) if result.is_integer() else result)
        except Exception:
            raise ValueError("Expected format: x+y or x-y with numbers")

    def handle_if_equals(self, condition):
        if ":" not in condition or "=" not in condition:
            raise ValueError("Expected format: a=b:command")
        left, rest = condition.split("=", 1)
        right, command = rest.split(":", 1)
        if left.strip() == right.strip():
            self.execute_line(command.strip())

    def print_help(self):
        print("------ Orchid Help ------")
        print("Core Commands:")
        print("  use <filename>         - Include an .orc script (silent)")
        print("  load <filename>        - Load and run an .orc script")
        print("  write=\"text\"           - Print text to screen")
        print("  grape.spam=\"N\"        - Repeat last write N times")
        print("  help                   - Show this help message")
        print("\nAdvanced Functions:")
        print("  let.var=\"name:value\"  - Define a variable")
        print("  math.add=\"x+y\"         - Add numbers")
        print("  math.sub=\"x-y\"         - Subtract numbers")
        print("  exit.now=\"true\"        - (optional) Stop running script")
        print("  if.equals=\"a=b:do\"     - Run if equal")
        print("\nScript Certificates:")
        print("  [Publisher Information]")
        print("  Publisher Name=Your Name")
        print("  ScriptName=Your App")
        print("  URL=https://your.site")
        print("-------------------------")

    def wait_for_key_press(self):
        if sys.platform == 'win32':
            msvcrt.getch()
        else:
            input()

    def run_shell(self):
        print("Orchid 1.0 Copyright (c) Zohan Haque, All rights reserved")
        print("Welcome to the Orchid Shell!")
        while True:
            try:
                line = input(self.hostname + " ")
                self.execute_line(line)
            except KeyboardInterrupt:
                print("\nExiting Orchid Shell.")
                break

def main():
    if len(sys.argv) > 1:
        script = sys.argv[1]
        orchid = OrchidInterpreter()
        orchid.handle_load(script)
    else:
        orchid = OrchidInterpreter()
        orchid.run_shell()

if __name__ == "__main__":
    main()
