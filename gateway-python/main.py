import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from typing import Any, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from clustering_engine import (
    build_sorted_pairs,
    compute_euclidia_matrix,
    compute_residuals,
    hierarchical_clustering,
)
from etl_recommender import run_etl_and_recommend
from file_parser import parse_uploaded_file

BINARY_EXE_PATH = r"C:\Dev\builds\c-binario-debug\c_binario.exe"
MAHALANOBIS_EXE_PATH = r"C:\Dev\builds\c-mahalanobis-debug\c_mahalanobis.exe"
GOWER_SERVICE_URL = "http://localhost:8080/api/gower/distance"

ALLOWED_EXTENSIONS = {".csv", ".txt", ".data", ".xlsx", ".docx"}

app = FastAPI(title="Gateway de Agrupamiento Jerárquico Multi-Motor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClusterRequest(BaseModel):
    engine: str
    linkage: str = "COMPLETE"
    labels: List[str]
    headers: List[str]
    column_types: List[str]
    matrix: List[List[Any]]
    binary_metric: Optional[str] = "JACCARD"


def _run_c_executable(exe_path: str, payload: dict[str, Any], engine_name: str) -> dict[str, Any]:
    if not os.path.exists(exe_path):
        raise HTTPException(
            status_code=500,
            detail=f"No se encontró el ejecutable de {engine_name} en: {exe_path}",
        )

    tmp_in_path = None
    tmp_out_path = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fin:
            json.dump(payload, fin, ensure_ascii=False)
            tmp_in_path = fin.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fout:
            tmp_out_path = fout.name

        completed = subprocess.run(
            [exe_path, tmp_in_path, tmp_out_path],
            capture_output=True,
            text=True,
            timeout=20,
        )

        if completed.returncode != 0:
            stderr_msg = (completed.stderr or completed.stdout or "").strip()
            raise HTTPException(
                status_code=400,
                detail=f"Error en motor {engine_name} (código {completed.returncode}): {stderr_msg}",
            )

        # Algunos ejecutables escriben el JSON al archivo de salida y otros a stdout
        if os.path.exists(tmp_out_path) and os.path.getsize(tmp_out_path) > 0:
            with open(tmp_out_path, "r", encoding="utf-8") as f:
                return json.load(f)

        stdout_clean = (completed.stdout or "").strip()
        if stdout_clean:
            return json.loads(stdout_clean)

        raise HTTPException(
            status_code=500,
            detail=f"El motor {engine_name} no devolvió salida JSON válida.",
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=f"Tiempo de espera agotado al ejecutar el motor {engine_name}.",
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Salida JSON inválida desde {engine_name}: {exc}",
        )
    finally:
        for path in (tmp_in_path, tmp_out_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def invoke_c_binary(req: ClusterRequest):
    if any(t != "BINARY" for t in req.column_types):
        raise HTTPException(
            status_code=400,
            detail="El motor Binario (C) requiere variables estrictamente binarias (0 y 1).",
        )

    payload = {
        "labels": req.labels,
        "headers": req.headers,
        "metric": req.binary_metric or "JACCARD",
        "matrix": req.matrix,
    }
    parsed = _run_c_executable(BINARY_EXE_PATH, payload, "BINARIO")
    dist_matrix = parsed.get("distanceMatrix") or parsed.get("distance_matrix")
    if not dist_matrix:
        raise HTTPException(status_code=500, detail="El motor Binario no devolvió 'distanceMatrix'.")

    notes = parsed.get("notes") or [f"Distancia binaria calculada en C ({req.binary_metric or 'JACCARD'})."]
    return dist_matrix, notes


def invoke_c_mahalanobis(req: ClusterRequest):
    if any(t not in ("NUMERIC", "BINARY") for t in req.column_types):
        raise HTTPException(
            status_code=400,
            detail="Mahalanobis requiere variables puramente numéricas.",
        )

    payload = {
        "labels": req.labels,
        "headers": req.headers,
        "matrix": req.matrix,
    }
    parsed = _run_c_executable(MAHALANOBIS_EXE_PATH, payload, "MAHALANOBIS")
    dist_matrix = parsed.get("distanceMatrix") or parsed.get("distance_matrix")
    if not dist_matrix:
        raise HTTPException(status_code=500, detail="El motor Mahalanobis no devolvió 'distanceMatrix'.")

    notes = parsed.get("notes") or ["Distancia de Mahalanobis calculada en C."]
    return dist_matrix, notes


def invoke_java_gower(req: ClusterRequest):
    payload = {
        "labels": req.labels,
        "headers": req.headers,
        "columnTypes": req.column_types,
        "matrix": req.matrix,
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        GOWER_SERVICE_URL,
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(
            status_code=400,
            detail=f"Java respondió HTTP {exc.code}: {body}",
        )
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo conectar con Gower (Java) en {GOWER_SERVICE_URL}: {exc}",
        )

    if not parsed.get("ok", True):
        raise HTTPException(
            status_code=400,
            detail=parsed.get("error", "Error en Gower (Java)"),
        )

    dist_matrix = parsed.get("distanceMatrix") or parsed.get("distance_matrix")
    if not dist_matrix:
        raise HTTPException(status_code=500, detail="Gower (Java) no devolvió 'distanceMatrix'.")

    report = parsed.get("report", "Distancia de Gower calculada en Java Spring Boot.")
    return dist_matrix, [report]


def execute_clustering(req: ClusterRequest) -> dict[str, Any]:
    engine = (req.engine or "").strip().upper()
    linkage = (req.linkage or "COMPLETE").strip().upper()

    if engine == "BINARY":
        dist_matrix, notes = invoke_c_binary(req)

    elif engine == "EUCLIDEAN":
        if any(t not in ("NUMERIC", "BINARY") for t in req.column_types):
            raise HTTPException(
                status_code=400,
                detail="Euclidea con residuos requiere variables puramente numéricas.",
            )
        residuals, means = compute_residuals(req.matrix)
        dist_matrix = compute_euclidia_matrix(residuals)
        notes = [
            "Distancia euclidiana calculada en Python sobre residuos centrados en la media.",
            f"Medias por columna: {[round(m, 4) for m in means]}",
        ]

    elif engine == "MAHALANOBIS":
        dist_matrix, notes = invoke_c_mahalanobis(req)

    elif engine == "GOWER":
        dist_matrix, notes = invoke_java_gower(req)

    else:
        raise HTTPException(
            status_code=501,
            detail=f"El microservicio {engine} aún no está conectado.",
        )

    sorted_pairs = build_sorted_pairs(req.labels, dist_matrix)
    history, dendrogram = hierarchical_clustering(req.labels, dist_matrix, linkage=linkage)

    return {
        "engine": engine,
        "linkage": linkage,
        "labels": req.labels,
        "headers": req.headers,
        "distance_matrix": dist_matrix,
        "sorted_pairs": sorted_pairs,
        "history": history,
        "dendrogram": dendrogram,
        "notes": notes,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "engines": {
            "binary_c_exists": os.path.exists(BINARY_EXE_PATH),
            "mahalanobis_c_exists": os.path.exists(MAHALANOBIS_EXE_PATH),
            "gower_url": GOWER_SERVICE_URL,
        },
    }


@app.post("/api/analyze-etl")
@app.post("/api/upload")
async def analyze_etl_endpoint(
    file: UploadFile = File(...),
    has_header: bool = Form(True),
    has_id: bool = Form(True),
    target_engine: str = Form("AUTO"),
):
    filename = (file.filename or "").strip()
    lower_name = filename.lower()

    if not any(lower_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido en '{filename}'. Extensiones válidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo subido está vacío.")

    try:
        parsed = parse_uploaded_file(
            filename=filename,
            content=content,
            has_header=has_header,
            has_id=has_id,
        )
        return run_etl_and_recommend(
            headers=parsed["headers"],
            labels=parsed["labels"],
            raw_matrix=parsed["matrix"],
            target_engine=target_engine,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cluster")
def cluster_endpoint(req: ClusterRequest):
    return execute_clustering(req)