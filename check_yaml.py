import yaml
import sys

try:
    with open(sys.argv[1], 'r') as f:
        yaml.safe_load(f)
    print("YAML is valid")
except Exception as e:
    print(f"YAML error: {e}")
