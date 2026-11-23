//
// Created by alisL on 23/11/2026.
//

#ifndef BINARY_CORE_H
#define BINARY_CORE_H

#define MAX_ELEMENTS 500
#define MAX_VARS 100

typedef struct {
    char etiqueta[64];
    int datos[MAX_VARS];
    int num_columnas;
} ElementoBinario;

int ejecutar_calculo_binario(
    ElementoBinario *elementos,
    int num_elementos,
    int num_vars,
    const char *metrica, // "JACCARD" o "SOKAL"
    double dist_matrix[MAX_ELEMENTS][MAX_ELEMENTS],
    char *reporte_validacion
);

#endif