import os
import sys
import types

class OrchidModule:
    def __init__(self, module_name, module_path, parent_interpreter):
        self.module_name = module_name
        self.module_path = module_path
        self.parent_interpreter = parent_interpreter
        self.custom_functions = {}
        self.implementations = {}
        self.load_module()

    def load_module(self):
        if not os.path.exists(self.module_path):
            raise FileNotFoundError(f"No such module: {self.module_path}")

        with open(self.module_path, "r") as f:
            lines = f.readlines()

        in_implement = False
        implement_language = None
        python_code_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("implement"):
                _, lang = stripped.split()
                implement_language = lang.lower()
                in_implement = True
                python_code_lines = []
                continue
            if in_implement and stripped == "endimplement":
                if implement_language == "python":
                    code = "\n".join(python_code_lines)
                    mod = types.ModuleType(self.module_name + "_pyimpl")
                    exec(code, mod.__dict__)
                    for fn_name in dir(mod):
                        if not fn_name.startswith("__"):
                            self.implementations[fn_name] = getattr(mod, fn_name)
                in_implement = False
                implement_language = None
                continue
            if in_implement:
                python_code_lines.append(line.rstrip("\n"))
            elif stripped.startswith("func "):
                func_decl = stripped[5:]
                if ":" not in func_decl:
                    continue
                func_name, func_body = map(str.strip, func_decl.split(":", 1))
                self.custom_functions[func_name] = func_body

    def call_function(self, func_name, args):
        if func_name in self.implementations:
            return self.implementations[func_name](*args)
        elif func_name in self.custom_functions:
            self.parent_interpreter.execute_line(self.custom_functions[func_name])
        else:
            raise AttributeError(f"Function '{func_name}' not found in module '{self.module_name}'.")

class OrchidInterpreter:
    def __init__(self):
        self.last_write = ""
        self.hostname = ">>>"
        self.variables = {}
        self.skip_lines = False
        self.modules = {}
        self.functions = self.build_builtin_functions()
        self.orchid_functions = self.build_orchid_functions()
        self.script_implementations = {}

    def build_builtin_functions(self):
        builtin_funcs = {
            "echo": lambda x: print(x),
            "reverse": lambda x: print(x[::-1]),
            "upper": lambda x: print(x.upper()),
            "lower": lambda x: print(x.lower()),
            "len": lambda x: print(len(x)),
            "repeat": lambda x, n: print(x * int(n)),
        }
        for idx in range(6, 41):
            builtin_funcs[f"custom_fn_{idx}"] = lambda *a, n=idx: print(f"Custom function {n} called with args: {a}")
        return builtin_funcs

    def build_orchid_functions(self):
        return {}

    def execute_line(self, line, current_file="<input>"):
        try:
            line = line.strip()
            if self.skip_lines:
                if line == "" or line.startswith("//"):
                    return
                if "=" in line and any(k in line for k in ["Publisher Name", "ScriptName", "URL"]):
                    return
                self.skip_lines = False

            if line.startswith("use "):
                self.handle_use(line[4:].strip())
            elif line.startswith("[Publisher Information]"):
                self.skip_lines = True
                return
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
                content = self.do_var_sub(line[len("write="):].strip().strip('"'))
                self.last_write = content
                print(content)
            elif line.startswith("grape.spam="):
                count_str = line[len("grape.spam="):].strip().strip('"')
                if not count_str.isdigit():
                    raise ValueError(f"Invalid spam count: {count_str}")
                for _ in range(int(count_str)):
                    print(self.last_write)
            elif line.startswith("func "):
                self.handle_func_declaration(line)
            elif line.startswith("call "):
                self.handle_func_call(line)
            elif line.startswith("#include "):
                self.handle_include(line[len("#include "):].strip())
            elif line.startswith("implement python"):
                self.handle_implement_python_block(current_file)
            elif not line or line.startswith("//"):
                pass
            else:
                raise SyntaxError(f"Unrecognized syntax: {line}")

        except Exception as e:
            print("most recent call lasted")
            print(f"execption: {str(e)}")
            print("Press Enter to continue...")
            self.wait_for_key_press()

    def handle_use(self, module_ref):
        module_path = module_ref.replace(".", os.sep) + ".orchid"
        module_name = module_ref.split(".")[-1]
        module = OrchidModule(module_name, module_path, self)
        self.modules[module_name] = module

    def handle_func_declaration(self, line):
        try:
            decl = line[5:]
            if ":" not in decl:
                raise ValueError("Function declaration must be in format: func name: body")
            name, body = map(str.strip, decl.split(":", 1))
            self.orchid_functions[name] = body
        except Exception as e:
            print(f"Error in function declaration: {str(e)}")

    def handle_func_call(self, line):
        tokens = line.split()
        if len(tokens) < 2:
            print("Usage: call <function> [args...]")
            return
        funcname = tokens[1]
        args = tokens[2:]
        if funcname in self.script_implementations:
            return self.script_implementations[funcname](*args)
        for module in self.modules.values():
            if funcname in module.implementations or funcname in module.custom_functions:
                module.call_function(funcname, args)
                return
        if funcname in self.functions:
            self.functions[funcname](*args)
        elif funcname in self.orchid_functions:
            self.execute_line(self.orchid_functions[funcname])
        else:
            print(f"Function '{funcname}' not found.")

    def handle_include(self, header):
        if not header.endswith(".orch"):
            header += ".orch"
        if not os.path.exists(header):
            print(f"Header file '{header}' not found.")
            return
        with open(header, "r") as f:
            for line in f:
                self.execute_line(line.strip(), current_file=header)

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

            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("implement python"):
                    i = self.handle_implement_python_block_from_lines(lines, i)
                else:
                    self.execute_line(line, current_file=filename)
                    i += 1

            print(f"Script '{filename}' loaded successfully.")
        except Exception as e:
            print("most recent call lasted")
            print(f"execption: Failed to load script '{filename}': {str(e)}")
            print("Press Enter to continue...")
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
        left_val = self.do_var_sub(left.strip())
        right_val = self.do_var_sub(right.strip())
        if left_val == right_val:
            self.execute_line(command.strip())

    def print_help(self):
        print("------ Orchid 1.2 Help ------")
        print("Core Commands:")
        print("  use <module.module>     - Load an Orchid module")
        print("  load <filename>         - Load and run an .orchid script")
        print("  #include <file.orch>    - Include header (.orch file)")
        print("  write=\"text\"           - Print text to screen")
        print("  grape.spam=\"N\"         - Repeat last write N times")
        print("  help                    - Show this help message")
        print("\nAdvanced Functions:")
        print("  let.var=\"name:value\"   - Define a variable")
        print("  math.add=\"x+y\"         - Add numbers")
        print("  math.sub=\"x-y\"         - Subtract numbers")
        print("  exit.now=\"true\"        - (optional) Stop running script")
        print("  if.equals=\"a=b:do\"     - Run if equal")
        print("  func name: body         - Define custom function")
        print("  call name [args...]     - Call a function")
        print("\nModules & Implementation:")
        print("  Modules are .orchid files, can have 'implement python ... endimplement' blocks")
        print("  You can add custom functions to modules")
        print("  Module and script functions may call Python code via 'implement python'")
        print("\n\033[90mScript Certificates:")
        print("  [Publisher Information]")
        print("  Publisher Name=Your Name")
        print("  ScriptName=Your App")
        print("  URL=https://your.site\033[0m")
        print("-----------------------------")

    def wait_for_key_press(self):
        input()

    def run_shell(self):
        print("Orchid 1.2 (The Real Generation) Copyright (c) Zohan Haque")
        print("Welcome to the Orchid Shell!")
        while True:
            try:
                line = input(self.hostname + " ")
                self.execute_line(line)
            except KeyboardInterrupt:
                print("\nExiting Orchid Shell.")
                break

    def handle_implement_python_block(self, current_file):
        print("Error: 'implement python' is only supported in full script mode or module loading.")

    def handle_implement_python_block_from_lines(self, lines, start_idx):
        code_lines = []
        i = start_idx + 1
        while i < len(lines):
            if lines[i].strip() == "endimplement":
                break
            code_lines.append(lines[i].rstrip("\n"))
            i += 1
        code = "\n".join(code_lines)
        mod = types.ModuleType("__script_pyimpl")
        exec(code, mod.__dict__)
        for fn_name in dir(mod):
            if not fn_name.startswith("__"):
                self.script_implementations[fn_name] = getattr(mod, fn_name)
        return i + 1

    def do_var_sub(self, s):
        out = ""
        i = 0
        while i < len(s):
            if s[i] == "$":
                j = i+1
                varname = ""
                while j < len(s) and (s[j].isalnum() or s[j] == "_"):
                    varname += s[j]
                    j += 1
                if varname and varname in self.variables:
                    out += str(self.variables[varname])
                    i = j
                else:
                    out += "$"
                    i += 1
            else:
                out += s[i]
                i += 1
        return out

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
