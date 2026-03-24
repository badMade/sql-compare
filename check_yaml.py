import yaml
import sys

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <file.yaml>", file=sys.stderr)
    sys.exit(1)

file_path = sys.argv[1]
try:
    with open(file_path, 'r') as f:
        yaml.safe_load(f)
    print(f"YAML is valid: {file_path}")
except (FileNotFoundError, yaml.YAMLError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
