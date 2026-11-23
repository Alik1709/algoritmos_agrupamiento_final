//
// Created by alisL on 23/11/2026.
//
#include "mahalanobis_core.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int ejecutar_calculo_mahalanobis(
    const ElementoNumerico *elementos,
    int num_elementos,
    int num_vars,
    double *dist_matrix,
    char *reporte_validacion
) {
    if (!elementos || !dist_matrix || !reporte_validacion) return 0;

    if (num_elementos < 2) {
        strcpy(reporte_validacion, "Error: Se requieren al menos 2 elementos para Mahalanobis.");
        return 0;
    }

    if (num_vars < 1 || num_vars > MAX_MAHA_VARS) {
        sprintf(reporte_validacion, "Error: Cantidad de variables (%d) fuera de rango [1..%d].",
                num_vars, MAX_MAHA_VARS);
        return 0;
    }

    // Validar finitud numérica y consistencia de columnas
    for (int i = 0; i < num_elementos; i++) {
        if (elementos[i].num_columnas != num_vars) {
            sprintf(reporte_validacion, "Error en fila %d (%s): columnas inconsistentes.",
                    i + 1, elementos[i].etiqueta);
            return 0;
        }
        for (int j = 0; j < num_vars; j++) {
            double val = elementos[i].datos[j];
            if (isnan(val) || isinf(val)) {
                sprintf(reporte_validacion, "Error en [%s, V%d]: valor no numérico o infinito.",
                        elementos[i].etiqueta, j + 1);
                return 0;
            }
        }
    }

    // Calcular medias por columna
    double *medias = (double *)calloc((size_t)num_vars, sizeof(double));
    double *cov = (double *)calloc((size_t)num_vars * (size_t)num_vars, sizeof(double));
    double *inv_cov = (double *)calloc((size_t)num_vars * (size_t)num_vars, sizeof(double));
    if (!medias || !cov || !inv_cov) {
        free(medias); free(cov); free(inv_cov);
        strcpy(reporte_validacion, "Error de memoria al reservar matrices.");
        return 0;
    }

    for (int j = 0; j < num_vars; j++) {
        double suma = 0.0;
        for (int i = 0; i < num_elementos; i++) {
            suma += elementos[i].datos[j];
        }
        medias[j] = suma / (double)num_elementos;
    }

    // Calcular matriz de covarianza muestral (denominador n - 1)
    double denom = (num_elementos > 1) ? (double)(num_elementos - 1) : 1.0;
    for (int a = 0; a < num_vars; a++) {
        for (int b = a; b < num_vars; b++) {
            double acum = 0.0;
            for (int i = 0; i < num_elementos; i++) {
                double da = elementos[i].datos[a] - medias[a];
                double db = elementos[i].datos[b] - medias[b];
                acum += da * db;
            }
            double c_val = acum / denom;
            cov[a * num_vars + b] = c_val;
            cov[b * num_vars + a] = c_val;
        }
    }

    // Pequeña regularización diagonal si la matriz resulta singular por colinealidad exacta
    int invertible = invertir_matriz_gauss_jordan(num_vars, cov, inv_cov);
    int regularizada = 0;
    if (!invertible) {
        for (int a = 0; a < num_vars; a++) {
            cov[a * num_vars + a] += 1e-6;
        }
        invertible = invertir_matriz_gauss_jordan(num_vars, cov, inv_cov);
        regularizada = 1;
    }

    if (!invertible) {
        free(medias); free(cov); free(inv_cov);
        strcpy(reporte_validacion, "Error: La matriz de covarianza es singular y no pudo invertirse.");
        return 0;
    }

    // Calcular distancias de Mahalanobis entre pares (i, j)
    double *diff = (double *)malloc((size_t)num_vars * sizeof(double));
    double *tmp_vec = (double *)malloc((size_t)num_vars * sizeof(double));
    if (!diff || !tmp_vec) {
        free(diff); free(tmp_vec);
        free(medias); free(cov); free(inv_cov);
        strcpy(reporte_validacion, "Error de memoria en cálculo de distancias.");
        return 0;
    }

    for (int i = 0; i < num_elementos; i++) {
        for (int j = 0; j < num_elementos; j++) {
            if (i == j) {
                dist_matrix[i * num_elementos + j] = 0.0;
                continue;
            }

            for (int k = 0; k < num_vars; k++) {
                diff[k] = elementos[i].datos[k] - elementos[j].datos[k];
            }

            // tmp_vec = diff^T * inv_cov
            for (int c = 0; c < num_vars; c++) {
                double acc = 0.0;
                for (int r = 0; r < num_vars; r++) {
                    acc += diff[r] * inv_cov[r * num_vars + c];
                }
                tmp_vec[c] = acc;
            }

            // forma cuadrática = tmp_vec * diff
            double quad = 0.0;
            for (int c = 0; c < num_vars; c++) {
                quad += tmp_vec[c] * diff[c];
            }

            double d = (quad > 0.0) ? sqrt(quad) : 0.0;
            dist_matrix[i * num_elementos + j] = d;
        }
    }

    sprintf(reporte_validacion,
            "Mahalanobis (C) completado: %d elementos x %d variables. Covarianza invertida con Gauss-Jordan%s.",
            num_elementos, num_vars,
            regularizada ? " (con ajuste 1e-6 en diagonal por colinealidad)" : "");

    free(diff);
    free(tmp_vec);
    free(medias);
    free(cov);
    free(inv_cov);
    return 1;
}