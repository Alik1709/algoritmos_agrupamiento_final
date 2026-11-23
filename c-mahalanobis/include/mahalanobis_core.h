//
// Created by alisL on 23/11/2026.
//

#ifndef MAHALANOBIS_CORE_H
#define MAHALANOBIS_CORE_H

#define MAX_MAHA_ELEMENTS 300
#define MAX_MAHA_VARS 40

typedef struct {
    char etiqueta[64];
    double datos[MAX_MAHA_VARS];
    int num_columnas;
} ElementoNumerico;

/* Operaciones matriciales desde cero */
int invertir_matriz_gauss_jordan(int n, const double *A, double *invA);

/* Cálculo de distancia de Mahalanobis con validación */
int ejecutar_calculo_mahalanobis(
    const ElementoNumerico *elementos,
    int num_elementos,
    int num_vars,
    double *dist_matrix,
    char *reporte_validacion
);

#endif