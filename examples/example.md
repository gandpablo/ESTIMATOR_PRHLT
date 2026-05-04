# Ejemplos mínimos

Los siguientes comandos están pensados para ejecutarse desde la raíz del
proyecto sobre los ejemplos de datos de la carpeta `examples/`

## Ejemplo con lm

```bash
estimator lm examples/calibration.txt examples/evaluation.txt \
  examples/results_lm 3 --remain --trim:1.5
```

## Ejemplo con sx

```bash
estimator sx examples/calibration.txt examples/evaluation.txt \
  examples/results_sx 3 --remain
```

## Ejemplo con ts

```bash
estimator ts examples/calibration_ts.txt examples/evaluation_ts.txt \
  examples/results_ts 3 dE --remain
```

## Ejemplo con ficheros ya agrupados

```bash
estimator lm examples/results_lm/lm_K3_t1_tr1_lim1.5/grouped/calibrationK3 \
  examples/results_lm/lm_K3_t1_tr1_lim1.5/grouped/evaluationK3 \
  examples/results_lm_grouped 3 --grouped --remain --trim:1.5
```
