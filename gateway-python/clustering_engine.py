import math


def compute_residuals(matrix, mode="mean_centered"):
    """
    Calcula residuos por columna antes de obtener la distancia de Euclidia.
    - mean_centered: r_ij = x_ij - promedio(col_j)
    """
    n = len(matrix)
    if n == 0:
        return []
    m = len(matrix[0])
    residuals = [[0.0] * m for _ in range(n)]

    for j in range(m):
        col = [float(matrix[i][j]) for i in range(n)]
        if mode == "mean_centered":
            ref = sum(col) / n
        else:
            ref = 0.0

        for i in range(n):
            residuals[i][j] = round(col[i] - ref, 6)

    return residuals


def compute_euclidia_matrix(matrix, residual_mode="mean_centered"):
    """
    Calcula la matriz de distancias euclidianas a partir de los residuos
    de cada observación respecto a su columna.
    """
    residuals = compute_residuals(matrix, mode=residual_mode)
    n = len(residuals)
    dist = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            s = sum((residuals[i][k] - residuals[j][k]) ** 2 for k in range(len(residuals[i])))
            d = math.sqrt(s)
            dist[i][j] = dist[j][i] = d

    return dist


def build_sorted_pairs(labels, dist_matrix):
    """
    Devuelve todos los pares únicos ordenados de menor a mayor distancia.
    """
    pairs = []
    n = len(labels)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append({
                "pair": f"({labels[i]}, {labels[j]})",
                "distance": dist_matrix[i][j],
            })
    pairs.sort(key=lambda x: x["distance"])
    return pairs


def hierarchical_clustering(labels, base_dist, linkage: str):
    """
    Ejecuta agrupamiento jerárquico aglomerativo con eslabonamiento:
    - VMC (Vecino Más Cercano / mínimo)
    - VML (Vecino Más Lejano / máximo)
    - PROMEDIO (UPGMA / promedio de distancias entre miembros)

    Retorna:
    - history: lista con campos etapa, grupo_1, grupo_2, grupo_n, coef
    - dendrogram: leaf_order y merges para dibujar el árbol
    """
    linkage_norm = (linkage or "VMC").upper()
    clusters = [{"name": lbl, "members": [i]} for i, lbl in enumerate(labels)]
    history = []
    merges = []

    def cluster_distance(c1, c2):
        dists = [base_dist[i][j] for i in c1["members"] for j in c2["members"]]
        if linkage_norm == "VML":
            return max(dists)
        if linkage_norm == "PROMEDIO":
            return sum(dists) / len(dists)
        return min(dists)  # VMC por defecto

    etapa = 1
    while len(clusters) > 1:
        best_i, best_j = 0, 1
        best_dist = float("inf")

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = cluster_distance(clusters[i], clusters[j])
                if d < best_dist - 1e-12:
                    best_dist = d
                    best_i, best_j = i, j

        c1 = clusters[best_i]
        c2 = clusters[best_j]
        new_name = f"G{etapa}"

        history.append({
            "etapa": etapa,
            "grupo_1": c1["name"],
            "grupo_2": c2["name"],
            "grupo_n": new_name,
            "coef": best_dist,
        })

        merges.append({
            "left": c1["name"],
            "right": c2["name"],
            "new_group": new_name,
            "height": best_dist,
            "members": c1["members"] + c2["members"],
        })

        merged_cluster = {
            "name": new_name,
            "members": c1["members"] + c2["members"],
        }
        for idx in sorted([best_i, best_j], reverse=True):
            clusters.pop(idx)
        clusters.append(merged_cluster)
        etapa += 1

    leaf_order = [labels[idx] for idx in clusters[0]["members"]]
    return history, {"leaf_order": leaf_order, "merges": merges}