# cloud-app-permission-scanner

## Installation

### From source (local)

```bash
git clone https://github.com/syndaez/cloud-app-permission-scanner.git
cd cloud-app-permission-scanner
pip install .
```

### Development mode

If you're making changes to the source code, install in editable mode so your changes take effect immediately without reinstalling:

```bash
pip install -e .
```

### From GitHub (directly)

```bash
pip install git+https://github.com/syndaez/cloud-app-permission-scanner.git
```

### Verify installation

```bash
cloud-app-permission-scanner --help
```

## Usage

```bash
cloud-app-permission-scanner \
  --root /path/to/classes \
  --include-re '.*com/example/.*' \
  --exclude-re '.*generated.*' \
  --out permissions-policy.json
```

Options:

- `--include-re`: regex applied to each discovered class file path; only matching files are scanned.
- `--exclude-re`: regex applied to each discovered class file path; matching files are skipped.

Examples:

```bash
# include only package classes under com/example
cloud-app-permission-scanner --root . --include-re '.*com/example/.*'

# skip generated classes and test classes
cloud-app-permission-scanner --root . --exclude-re '.*(generated|test).*'

# combine both filters
cloud-app-permission-scanner --root . --include-re '.*com/example/.*' --exclude-re '.*generated.*'
```
