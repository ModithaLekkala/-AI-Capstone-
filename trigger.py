#trigger.py
import json
import subprocess

# --- CONFIGURACIÓN CORREGIDA ---
# Nombres exactos basados en tu código P4
JSON_FILE = "rules.json"
P4_TABLE = "ingress.decision_table"  # Nombre completo y correcto de la tabla
P4_ACTION_PREFIX = "ingress."       # Prefijo correcto para las acciones

# LA LISTA DE CLAVES CORRECTA Y EN ORDEN
# Esta lista debe coincidir EXACTAMENTE con la definición 'key' en tu tabla P4
FIELD_ORDER = [
    "win_maxlength",
    "win_minlength",
    "win_psh",
    "win_pkglength",
    "win_pkgcount"
]

# La prioridad es importante para las reglas ternarias (ternary)
DEFAULT_PRIORITY = "10" 

def format_rule_entry(rule):
    """
    Formatea una regla JSON en un comando válido para simple_switch_CLI.
    """
    action_name = rule.get("action_name")
    if not action_name:
        raise ValueError("Falta 'action_name' en la regla")

    match_fields_str = ""
    for field in FIELD_ORDER:
        if field in rule["match"]:
            # El formato para ternary/range en simple_switch_CLI es valor&&&mascara
            low, mask = rule["match"][field]
            match_fields_str += f" {low}&&&{mask}"
        else:
            raise ValueError(f"Campo faltante en JSON: {field}")
    
    # Construye el nombre completo de la acción: "ingress." + "drop" -> "ingress.drop"
    full_action_name = P4_ACTION_PREFIX + action_name
    
    # Construye el comando final
    cmd = f"table_add {P4_TABLE} {full_action_name}{match_fields_str} => {DEFAULT_PRIORITY}"
    
    return cmd

def load_rules_to_switch(json_file):
    """
    Carga las reglas del archivo JSON al switch usando simple_switch_CLI.
    """
    try:
        with open(json_file, "r") as f:
            rules = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] No se pudo encontrar el archivo de reglas: {json_file}")
        return
    except json.JSONDecodeError:
        print(f"[ERROR] El archivo {json_file} no es un JSON válido.")
        return

    valid_cmds = []
    print(f"Procesando {len(rules)} reglas desde {json_file}...")
    for i, rule in enumerate(rules):
        try:
            cmd = format_rule_entry(rule)
            valid_cmds.append(cmd)
        except Exception as e:
            print(f"[ERROR] Regla #{i+1} descartada: {e}")

    print(f"\n{len(valid_cmds)} reglas válidas serán insertadas...\n")

    if not valid_cmds:
        print("No hay comandos válidos para ejecutar.")
        return

    # Conecta con el CLI del switch y envía todos los comandos
    cli_input = "\n".join(valid_cmds) + "\nexit\n"
    process = subprocess.Popen(
        ["simple_switch_CLI"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=cli_input)

    print("--- SALIDA DEL SWITCH ---")
    print(stdout)
    if stderr:
        print("--- ERRORES DEL SWITCH ---")
        print(stderr)

if __name__ == "__main__":
    load_rules_to_switch(JSON_FILE)
