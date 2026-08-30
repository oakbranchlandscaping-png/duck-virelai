# PUSH — Ring Ontology kernel: the notecard, isolated

Push-ready control arm. Two commands from a fresh Mac terminal:

```sh
cd ~/Desktop/duck-virelai/kaggle/ring-ontology/source-dataset && kaggle datasets create -p . -r zip
```

```sh
cd ~/Desktop/duck-virelai/kaggle/ring-ontology/kernel && kaggle kernels push -p .
```

Then Save & Run All on
<https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-ring-ontology-share>.
After each run:

```sh
kaggle kernels output stephenkaskin/taaf-duck-virelai-ring-ontology-share -p ~/Desktop/duck-virelai/runs/kaggle-ring-ontology-run1/kaggle-output
```

Run at least twice, changing the output directory suffix for run 2. This arm differs
from r0-p2 only by the static ontology notecard in `prompts.py`; it adds no Captain or
Virelai runtime code.
