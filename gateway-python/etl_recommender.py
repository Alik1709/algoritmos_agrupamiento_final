NULL_TOKENS = {"", "na", "n/a", "null", "nan", "none", "?", "-", "."}

def _try_float(val: str):
    try:
        v = float(val.replace(",", "."))
        return v if v == v and abs(v) != float("inf") else None
    except ValueError:
        return None

def run_etl_and_recommend(headers, labels, raw_matrix, target_engine: str = "AUTO"):
    etl_report = []
    expected_cols = len(headers)
    valid_labels = []
    valid_rows = []

    # 1. Filtrar filas incompletas, vacías o con valores nulos/basura
    for idx, (lbl, row) in enumerate(zip(labels, raw_matrix)):
        if len(row) != expected_cols:
            etl_report.append({
                "step": "LIMPIEZA",
                "type": "DROPPED",
                "message": f"Fila '{lbl}' descartada: tiene {len(row)} columnas (se esperaban {expected_cols})."
            })
            continue

        if any(cell.strip().lower() in NULL_TOKENS for cell in row):
            etl_report.append({
                "step": "LIMPIEZA",
                "type": "DROPPED",
                "message": f"Fila '{lbl}' descartada: contiene valores vacíos o nulos (NA/NaN)."
            })
            continue

        valid_labels.append(lbl)
        valid_rows.append(row)

    if len(valid_rows) < 2:
        raise ValueError("Tras la limpieza ETL quedaron menos de 2 registros válidos.")

    # 2. Detectar tipo de cada columna (BINARY, NUMERIC, CATEGORICAL)
    col_types = []
    clean_matrix = [[] for _ in valid_rows]

    for c_idx in range(expected_cols):
        col_vals = [r[c_idx] for r in valid_rows]
        parsed_nums = [_try_float(v) for v in col_vals]

        if all(n is not None for n in parsed_nums):
            unique_vals = set(parsed_nums)
            if unique_vals.issubset({0.0, 1.0}):
                col_types.append("BINARY")
                for r_idx, n in enumerate(parsed_nums):
                    clean_matrix[r_idx].append(int(n))
            else:
                col_types.append("NUMERIC")
                for r_idx, n in enumerate(parsed_nums):
                    clean_matrix[r_idx].append(round(n, 6))
        else:
            col_types.append("CATEGORICAL")
            for r_idx, v in enumerate(col_vals):
                clean_matrix[r_idx].append(v.strip())

    etl_report.append({
        "step": "TIPADO",
        "type": "OK",
        "message": f"Variables clasificadas: " + ", ".join(f"{h} ({t})" for h, t in zip(headers, col_types))
    })

    # 3. Validación específica si el usuario forzó un motor en la vista previa
    if target_engine == "BINARY" and any(t != "BINARY" for t in col_types):
        etl_report.append({
            "step": "VALIDACIÓN BINARIA",
            "type": "WARNING",
            "message": "Advertencia: Hay columnas no binarias; el motor Binario (C) rechazará valores distintos de 0 y 1."
        })
    elif target_engine in ("EUCLIDEAN", "MAHALANOBIS") and "CATEGORICAL" in col_types:
        etl_report.append({
            "step": "VALIDACIÓN NUMÉRICA",
            "type": "WARNING",
            "message": f"Advertencia: Existen variables categóricas; {target_engine} requiere solo variables numéricas."
        })

    # 4. Generar recomendación inteligente
    unique_types = set(col_types)
    if unique_types == {"BINARY"}:
        rec = {
            "recommended_engine": "BINARY",
            "variable_summary": f"{expected_cols} variables estrictamente binarias (0 y 1).",
            "reason": "Todos los atributos son dicotómicos; se recomienda Binario en C (Jaccard/Sokal) o Euclidia como alternativa."
        }
    elif "CATEGORICAL" in unique_types:
        rec = {
            "recommended_engine": "GOWER",
            "variable_summary": f"Variables mixtas detectadas ({', '.join(sorted(unique_types))}).",
            "reason": "Al existir atributos categóricos/mixtos, la distancia de Gower (Java) es la única métrica adecuada."
        }
    else:
        if len(valid_rows) > expected_cols + 2 and expected_cols >= 2:
            rec = {
                "recommended_engine": "MAHALANOBIS",
                "variable_summary": f"{expected_cols} variables numéricas continuas con {len(valid_rows)} observaciones.",
                "reason": "Dataset numérico con suficientes muestras para estimar la matriz de covarianza (Mahalanobis en C) o usar Euclidia (Python)."
            }
        else:
            rec = {
                "recommended_engine": "EUCLIDEAN",
                "variable_summary": f"{expected_cols} variables numéricas.",
                "reason": "Variables puramente numéricas; Euclidiana en Python es directa y estable sin requerir inversión de covarianza."
            }

    return {
        "headers": headers,
        "labels": valid_labels,
        "column_types": col_types,
        "clean_matrix": clean_matrix,
        "etl_report": etl_report,
        "recommendation": rec
    }