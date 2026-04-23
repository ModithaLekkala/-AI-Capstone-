import json
import subprocess

# --- CONFIGURATION ---
JSON_FILE = "data/rules.json"
P4_TABLE = "ingress.decision_table"
P4_ACTION_PREFIX = "ingress."
FIELD_ORDER = [
    "win_maxlength",
    "win_minlength",
    "win_psh",
    "win_pkglength",
    "win_pkgcount"
]
DEFAULT_PRIORITY = "10"   # used only when a rule has no "priority" field


def format_rule_entry(rule):
    action_name = rule.get("action_name")
    if not action_name:
        raise ValueError("Falta 'action_name' en la regla")
    match_fields_str = ""
    for field in FIELD_ORDER:
        if field in rule["match"]:
            low, mask = rule["match"][field]
            match_fields_str += " {}&&&{}".format(low, mask)
        else:
            raise ValueError("Campo faltante en JSON: {}".format(field))
    full_action_name = P4_ACTION_PREFIX + action_name
    priority = str(rule.get("priority", DEFAULT_PRIORITY))
    cmd = "table_add {} {}{} => {}".format(
        P4_TABLE, full_action_name, match_fields_str, priority)
    return cmd


def load_rules_to_switch(json_file):
    try:
        with open(json_file, "r") as f:
            rules = json.load(f)
    except FileNotFoundError:
        print("[ERROR] No se pudo encontrar el archivo de reglas: {}".format(json_file))
        return
    except ValueError:
        print("[ERROR] El archivo {} no es un JSON valido.".format(json_file))
        return

    valid_cmds = []
    print("Procesando {} reglas desde {}...".format(len(rules), json_file))

    for i, rule in enumerate(rules):
        try:
            cmd = format_rule_entry(rule)
            valid_cmds.append(cmd)
            print("  [OK] Regla #{}: {}".format(i + 1, cmd))
        except Exception as e:
            print("  [ERROR] Regla #{} descartada: {}".format(i + 1, e))

    print("\n{} reglas validas seran insertadas...\n".format(len(valid_cmds)))

    if not valid_cmds:
        print("No hay comandos validos para ejecutar.")
        return

    cli_input = "\n".join(valid_cmds) + "\nexit\n"

    process = subprocess.Popen(
        ["simple_switch_CLI"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate(input=cli_input.encode())

    print("--- SALIDA DEL SWITCH ---")
    print(stdout.decode())
    if stderr:
        print("--- ERRORES DEL SWITCH ---")
        print(stderr.decode())


if __name__ == "__main__":
    load_rules_to_switch(JSON_FILE)