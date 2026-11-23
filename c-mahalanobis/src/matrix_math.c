//
// Created by alisL on 23/11/2026.
//
#include "mahalanobis_core.h"
#include <math.h>
#include <stdlib.h>

int invertir_matriz_gauss_jordan(int n, const double *A, double *invA) {
    if (n <= 0 || !A || !invA) return 0;

    double *aug = (double *)malloc((size_t)n * (size_t)(2 * n) * sizeof(double));
    if (!aug) return 0;

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            aug[i * (2 * n) + j] = A[i * n + j];
            aug[i * (2 * n) + (n + j)] = (i == j) ? 1.0 : 0.0;
        }
    }

    for (int col = 0; col < n; col++) {
        int pivote = col;
        double max_val = fabs(aug[col * (2 * n) + col]);

        for (int fila = col + 1; fila < n; fila++) {
            double val = fabs(aug[fila * (2 * n) + col]);
            if (val > max_val) {
                max_val = val;
                pivote = fila;
            }
        }

        if (max_val < 1e-12) {
            free(aug);
            return 0; // Matriz singular o no invertible
        }

        if (pivote != col) {
            for (int k = 0; k < 2 * n; k++) {
                double tmp = aug[col * (2 * n) + k];
                aug[col * (2 * n) + k] = aug[pivote * (2 * n) + k];
                aug[pivote * (2 * n) + k] = tmp;
            }
        }

        double diag = aug[col * (2 * n) + col];
        for (int k = 0; k < 2 * n; k++) {
            aug[col * (2 * n) + k] /= diag;
        }

        for (int fila = 0; fila < n; fila++) {
            if (fila == col) continue;
            double factor = aug[fila * (2 * n) + col];
            for (int k = 0; k < 2 * n; k++) {
                aug[fila * (2 * n) + k] -= factor * aug[col * (2 * n) + k];
            }
        }
    }

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            invA[i * n + j] = aug[i * (2 * n) + (n + j)];
        }
    }

    free(aug);
    return 1;
}