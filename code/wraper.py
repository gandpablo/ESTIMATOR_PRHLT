import json
import subprocess
import sys
from pathlib import Path


def fix_token(token):
    for dash in ("\u2013", "\u2014", "\u2015", "\u2212"):
        token = token.replace(dash, "-")
    return token


def get_experiment_dir(tool, outdir, K, remain, trim, metric, grouped):
    outdir = str(Path(outdir).absolute())
    t_flag = int(remain)

    if tool == "lm":
        trim_flag = int(trim is not None)
        lim = 0.0 if trim is None else trim
        if grouped:
            experiment = f"lm_grouped_K{K}_t{t_flag}_tr{trim_flag}_lim{lim}"
        else:
            experiment = f"lm_K{K}_t{t_flag}_tr{trim_flag}_lim{lim}"
    elif tool == "sx":
        trim_flag = int(trim is not None)
        lim = 0.0 if trim is None else trim
        if grouped:
            experiment = f"simplex_grouped_K{K}_t{t_flag}_tr{trim_flag}_lim{lim}"
        else:
            experiment = f"simplex_K{K}_t{t_flag}_tr{trim_flag}_lim{lim}"
    else:
        if grouped:
            experiment = f"ts_grouped_K{K}_t{t_flag}"
        else:
            experiment = f"ts_K{K}_t{t_flag}_{metric}"

    return Path(outdir) / experiment


def get_expected_inputs(tool, archivo_calibracion, archivo_evaluacion, outdir, K, remain, trim, metric, grouped):
    experiment_dir = get_experiment_dir(tool, outdir, K, remain, trim, metric, grouped)
    expected = {
        "archivo1": str(Path(archivo_calibracion).absolute()),
        "archivo2": str(Path(archivo_evaluacion).absolute()),
        "K": K,
        "t": remain,
        "grouped": grouped,
        "outdir": str(Path(outdir).absolute()),
        "experiment_dir": str(experiment_dir.absolute()),
    }

    if tool in {"lm", "sx"}:
        expected["trim"] = trim is not None
        expected["lim"] = 0.0 if trim is None else trim
    elif not grouped:
        expected["optimization"] = metric

    return expected, experiment_dir


def should_recalculate(experiment_dir):
    prompt = (
        f"\nEl experimento:\n"
        f"{experiment_dir}\n"
        "ya existe con la misma entrada.\n"
        "¿Sobrescribir y recalcular? [y/N]: "
    )
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        print("No se pudo leer la respuesta. Se cancela para no sobrescribir.")
        return False

    return answer in {"y", "yes", "s", "si", "sí"}


def die(message):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(2)


args = [fix_token(arg) for arg in sys.argv[1:]]

if len(args) < 4:
    die("uso: estimator lm|sx|ts archivo_calibracion archivo_evaluacion outdir ...")

tool = args[0]
archivo_calibracion = args[1]
archivo_evaluacion = args[2]
outdir = args[3]

if tool not in {"lm", "sx", "ts"}:
    die("el primer argumento debe ser lm, sx o ts")

K = None
remain = False
trim = None
metric = "ce"
grouped = False

i = 4
while i < len(args):
    token = args[i]

    if token in {"grouped", "--grouped"}:
        grouped = True
        i += 1
        continue

    if token in {"remain", "--remain"}:
        remain = True
        i += 1
        continue

    if token.startswith("--trim:") or token.startswith("trim:"):
        trim = float(token.split(":", 1)[1])
        i += 1
        continue

    if token in {"--trim", "trim"}:
        trim = float(args[i + 1])
        i += 2
        continue

    if tool == "ts" and token in {"ce", "dE", "DE"}:
        metric = token
        i += 1
        continue

    try:
        K = int(token)
    except ValueError:
        die(f"argumento no reconocido: {token}")
    i += 1

if K is None:
    if grouped:
        die("K es obligatorio si se usa --grouped; se usa sólo para nombrar el experimento")
    K = 100

if grouped:
    metric = None

expected_inputs, experiment_dir = get_expected_inputs(
    tool,
    archivo_calibracion,
    archivo_evaluacion,
    outdir,
    K,
    remain,
    trim,
    metric,
    grouped,
)

metadata_path = experiment_dir / "metadata.json"
if metadata_path.is_file():
    try:
        with metadata_path.open() as f:
            metadata = json.load(f)
    except (OSError, json.JSONDecodeError):
        metadata = None

    if metadata is not None:
        saved_inputs = metadata.get("inputs", {})
        if all(saved_inputs.get(key) == value for key, value in expected_inputs.items()):
            if not should_recalculate(experiment_dir):
                print("Experimento cancelado. Se conservan los resultados existentes.")
                raise SystemExit(0)

base_dir = Path(__file__).resolve().parent

scripts = {
    "lm": base_dir / "toolkitLm.py",
    "sx": base_dir / "toolkitSimplex.py",
    "ts": base_dir / "toolkitTs.py",
}

cmd = [
    sys.executable,
    str(scripts[tool]),
    archivo_calibracion,
    archivo_evaluacion,
]

cmd.append(str(K))

if tool == "ts" and not grouped:
    cmd.append(metric)

if remain:
    cmd.append("--remain")

if grouped:
    cmd.append("--grouped")

if tool in {"lm", "sx"} and trim is not None:
    cmd.extend(["--trim", "True", "--lim", str(trim)])

cmd.extend(["--outdir", outdir])

result = subprocess.run(cmd)
raise SystemExit(result.returncode)
