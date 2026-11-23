const API_BASE = "http://localhost:8000/api";

const CLUSTER_PALETTE = [
    "#38bdf8", "#10b981", "#f59e0b", "#f43f5e", "#a855f7",
    "#ec4899", "#14b8a6", "#eab308", "#6366f1", "#84cc16",
    "#fb923c", "#22d3ee", "#e879f9", "#4ade80", "#f87171"
];

let selectedFile = null;
let currentETLData = null;

const fileInput = document.getElementById("fileInput");
const btnSelectFile = document.getElementById("btnSelectFile");
const dropZone = document.getElementById("dropZone");
const fileNameTag = document.getElementById("fileName");
const btnRunETL = document.getElementById("btnRunETL");
const engineSelect = document.getElementById("engineSelect");
const binaryMetricGroup = document.getElementById("binaryMetricGroup");
const btnExecuteClustering = document.getElementById("btnExecuteClustering");

function getGroupColor(index) {
    if (index < CLUSTER_PALETTE.length) {
        return CLUSTER_PALETTE[index];
    }
    const hue = (index * 137.508) % 360;
    return `hsl(${hue.toFixed(1)}, 75%, 58%)`;
}

function getEngineDisplayName(engineCode) {
    switch ((engineCode || "").toUpperCase()) {
        case "BINARY":
            return "Binario (C)";
        case "GOWER":
            return "Gower (Java)";
        case "EUCLIDEAN":
            return "Euclidia (Python)";
        case "MAHALANOBIS":
            return "Mahalanobis (C)";
        default:
            return engineCode;
    }
}

// Eventos de selección de archivo
btnSelectFile.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => handleFileSelection(e.target.files[0]));

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#38bdf8";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "#334155";
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#334155";
    if (e.dataTransfer.files.length) {
        handleFileSelection(e.dataTransfer.files[0]);
    }
});

function handleFileSelection(file) {
    if (!file) return;
    selectedFile = file;
    fileNameTag.textContent = `Archivo listo: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    btnRunETL.disabled = false;
}

engineSelect.addEventListener("change", () => {
    binaryMetricGroup.style.display = engineSelect.value === "BINARY" ? "flex" : "none";
});

//Enviar archivo al Gateway para ETL, Validación y Recomendación
btnRunETL.addEventListener("click", async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("has_header", document.getElementById("hasHeader").checked);
    formData.append("has_id", document.getElementById("hasIdCol").checked);
    formData.append("target_engine", document.getElementById("targetEnginePreview").value);

    btnRunETL.textContent = "Procesando ETL...";
    btnRunETL.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/analyze-etl`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error en el análisis ETL");

        currentETLData = data;
        renderETLSection(data);
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        btnRunETL.textContent = "Analizar y Validar Datos";
        btnRunETL.disabled = false;
    }
});

function renderETLSection(data) {
    const etlSection = document.getElementById("etlSection");
    etlSection.classList.remove("hidden");

    const rec = data.recommendation;
    const banner = document.getElementById("recommendationBanner");
    banner.innerHTML = `
        <strong>Diagnóstico de Variables:</strong> ${rec.variable_summary}<br>
        <strong>Programa Recomendado:</strong> <span style="color:#38bdf8; font-weight:bold;">${getEngineDisplayName(rec.recommended_engine)}</span>
        — ${rec.reason}
    `;

    if (rec.recommended_engine) {
        engineSelect.value = rec.recommended_engine;
        engineSelect.dispatchEvent(new Event("change"));
    }

    const logList = document.getElementById("etlReportList");
    logList.innerHTML = "";
    (data.etl_report || []).forEach(item => {
        const li = document.createElement("li");
        li.className = (item.type === "WARNING" || item.type === "DROPPED") ? "warn" : "ok";
        li.textContent = `[${item.step}] ${item.message}`;
        logList.appendChild(li);
    });

    const table = document.getElementById("cleanMatrixTable");
    table.innerHTML = "";

    const thead = document.createElement("thead");
    const trHead = document.createElement("tr");
    trHead.innerHTML = `<th>ID</th>` + (data.headers || []).map(h => `<th>${h}</th>`).join("");
    thead.appendChild(trHead);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    (data.clean_matrix || []).forEach((row, idx) => {
        const tr = document.createElement("tr");
        const label = (data.labels && data.labels[idx]) ? data.labels[idx] : `E${idx + 1}`;
        tr.innerHTML = `<td><strong>${label}</strong></td>` + row.map(val => `<td>${val}</td>`).join("");
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
}

//Ejecutar Microservicio de Distancia + Agrupamiento Jerárquico
btnExecuteClustering.addEventListener("click", async () => {
    if (!currentETLData) return;

    const payload = {
        engine: engineSelect.value,
        binary_metric: document.getElementById("binarySubmetric").value,
        linkage: document.getElementById("linkageSelect").value,
        labels: currentETLData.labels,
        headers: currentETLData.headers,
        column_types: currentETLData.column_types,
        matrix: currentETLData.clean_matrix
    };

    btnExecuteClustering.textContent = "Calculando...";
    btnExecuteClustering.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/cluster`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Error al ejecutar el agrupamiento");

        renderClusteringResults(result, payload.engine, payload.linkage);
    } catch (err) {
        alert(`Fallo en ejecución: ${err.message}`);
    } finally {
        btnExecuteClustering.textContent = "Calcular Distancias y Agrupar";
        btnExecuteClustering.disabled = false;
    }
});

function renderClusteringResults(result, engine, linkage) {
    const resultsSection = document.getElementById("resultsSection");
    resultsSection.classList.remove("hidden");
    document.getElementById("activeEngineLabel").textContent =
        `${getEngineDisplayName(engine)} | Eslabonamiento: ${linkage}`;

    if (result.engine_etl_notes && result.engine_etl_notes.length > 0) {
        const logList = document.getElementById("etlReportList");
        result.engine_etl_notes.forEach(note => {
            const li = document.createElement("li");
            li.className = "ok";
            li.textContent = `[${getEngineDisplayName(engine)}] ${note}`;
            logList.appendChild(li);
        });
    }

    renderDistanceMatrix(result.labels, result.distance_matrix);

    const pairsBody = document.querySelector("#sortedPairsTable tbody");
    pairsBody.innerHTML = "";
    (result.sorted_pairs || []).forEach((p, idx) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td><strong>${p.pair}</strong></td>
            <td>${Number(p.distance).toFixed(4)}</td>
        `;
        pairsBody.appendChild(tr);
    });

    const historyBody = document.querySelector("#historyTable tbody");
    historyBody.innerHTML = "";
    const historyList = result.history || [];

    historyList.forEach((step, idx) => {
        const color = getGroupColor(idx);
        step.color = color;

        if (result.dendrogram && Array.isArray(result.dendrogram.merges) && result.dendrogram.merges[idx]) {
            result.dendrogram.merges[idx].color = color;
        }

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${step.etapa}</strong></td>
            <td>${step.grupo_1}</td>
            <td>${step.grupo_2}</td>
            <td><span style="color:${color}; font-weight:bold;">■ ${step.grupo_n}</span></td>
            <td><strong>${Number(step.coef).toFixed(4)}</strong></td>
        `;
        historyBody.appendChild(tr);
    });

    drawDendrogram(result.dendrogram, historyList);
}

function renderDistanceMatrix(labels, matrix) {
    const table = document.getElementById("distanceMatrixTable");
    table.innerHTML = "";

    const thead = document.createElement("thead");
    thead.innerHTML = `<tr><th>-</th>${(labels || []).map(l => `<th>${l}</th>`).join("")}</tr>`;
    table.appendChild(thead);

    let minVal = Infinity;
    for (let i = 0; i < matrix.length; i++) {
        for (let j = i + 1; j < matrix.length; j++) {
            if (matrix[i][j] < minVal) {
                minVal = matrix[i][j];
            }
        }
    }

    const tbody = document.createElement("tbody");
    matrix.forEach((row, i) => {
        const tr = document.createElement("tr");
        let cells = `<th>${labels[i]}</th>`;
        row.forEach((val, j) => {
            const numVal = Number(val);
            if (i === j) {
                cells += `<td class="diag">0.0000</td>`;
            } else if (Math.abs(numVal - minVal) < 1e-9) {
                cells += `<td class="min-dist">${numVal.toFixed(4)}</td>`;
            } else {
                cells += `<td>${numVal.toFixed(4)}</td>`;
            }
        });
        tr.innerHTML = cells;
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
}

function drawDendrogram(dendrogramData, history) {
    const canvas = document.getElementById("dendrogramCanvas");
    const ctx = canvas.getContext("2d");

    if (!dendrogramData || !Array.isArray(dendrogramData.leaf_order)) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
    }

    const leaves = dendrogramData.leaf_order;
    const merges = dendrogramData.merges || [];

    const width = Math.max(680, leaves.length * 75);
    const height = 430;
    canvas.width = width;
    canvas.height = height;

    ctx.clearRect(0, 0, width, height);

    const padLeft = 65;
    const padRight = 30;
    const padTop = 32;
    const padBottom = 60;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const maxDist = Math.max(...merges.map(m => Number(m.height) || 0), 0.0001) * 1.12;

    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(padLeft, padTop);
    ctx.lineTo(padLeft, padTop + plotH);
    ctx.lineTo(padLeft + plotW, padTop + plotH);
    ctx.stroke();

    ctx.fillStyle = "#94a3b8";
    ctx.font = "11px monospace";
    ctx.textAlign = "right";
    for (let t = 0; t <= 5; t++) {
        const val = (maxDist / 5) * t;
        const y = padTop + plotH - (val / maxDist) * plotH;
        ctx.fillText(val.toFixed(3), padLeft - 8, y + 4);

        ctx.strokeStyle = "rgba(71, 85, 105, 0.25)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(padLeft + plotW, y);
        ctx.stroke();
    }
    const nodeCoords = {};
    const stepX = plotW / Math.max(leaves.length, 1);
    ctx.textAlign = "center";

    leaves.forEach((leaf, idx) => {
        const x = padLeft + stepX * (idx + 0.5);
        const y = padTop + plotH;
        nodeCoords[leaf] = { x, y };

        ctx.fillStyle = "#f8fafc";
        ctx.font = "bold 12px sans-serif";
        ctx.fillText(leaf, x, y + 22);
    });

    merges.forEach((merge, idx) => {
        const c1 = nodeCoords[merge.left];
        const c2 = nodeCoords[merge.right];
        if (!c1 || !c2) return;

        const stageColor = merge.color || (history[idx] && history[idx].color) || getGroupColor(idx);
        const mergeHeight = Number(merge.height) || 0;
        const yMerge = padTop + plotH - (mergeHeight / maxDist) * plotH;
        const xMid = (c1.x + c2.x) / 2;

        ctx.strokeStyle = stageColor;
        ctx.lineWidth = 3;

        ctx.beginPath();
        ctx.moveTo(c1.x, c1.y);
        ctx.lineTo(c1.x, yMerge);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(c2.x, c2.y);
        ctx.lineTo(c2.x, yMerge);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(c1.x, yMerge);
        ctx.lineTo(c2.x, yMerge);
        ctx.stroke();

        ctx.fillStyle = stageColor;
        ctx.font = "bold 11px sans-serif";
        ctx.fillText(`${merge.new_group} (${mergeHeight.toFixed(3)})`, xMid, yMerge - 6);

        nodeCoords[merge.new_group] = { x: xMid, y: yMerge };
    });
}