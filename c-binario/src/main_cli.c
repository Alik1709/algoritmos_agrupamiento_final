//
// Created by alisL on 23/11/2026.
//
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "binary_core.h"

// Uso: ms_binary.exe <ruta_input.txt> <JACCARD|SOKAL>
int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("{\"ok\": false, \"error\": \"Argumentos insuficientes\"}\n");
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        printf("{\"ok\": false, \"error\": \"No se pudo abrir archivo de intercambio\"}\n");
        return 1;
    }

    int n_elem = 0, n_vars = 0;
    if (fscanf(f, "%d %d", &n_elem, &n_vars) != 2) {
        fclose(f);
        printf("{\"ok\": false, \"error\": \"Cabecera de dimensiones invalida\"}\n");
        return 1;
    }

    ElementoBinario elementos[MAX_ELEMENTS];
    for (int i = 0; i < n_elem; i++) {
        fscanf(f, "%63s", elementos[i].etiqueta);
        elementos[i].num_columnas = n_vars;
        for (int j = 0; j < n_vars; j++) {
            double tmp;
            if (fscanf(f, "%lf", &tmp) != 1 || (tmp != 0.0 && tmp != 1.0)) {
                fclose(f);
                printf("{\"ok\": false, \"error\": \"Valor no binario detectado en fila %d\"}\n", i + 1);
                return 1;
            }
            elementos[i].datos[j] = (int)tmp;
        }
    }
    fclose(f);

    static double dist_matrix[MAX_ELEMENTS][MAX_ELEMENTS];
    char reporte[512];

    if (!ejecutar_calculo_binario(elementos, n_elem, n_vars, argv[2], dist_matrix, reporte)) {
        printf("{\"ok\": false, \"error\": \"%s\"}\n", reporte);
        return 1;
    }

    // Emitir respuesta JSON pura
    printf("{\"ok\": true, \"report\": \"%s\", \"distance_matrix\": [", reporte);
    for (int i = 0; i < n_elem; i++) {
        printf("[");
        for (int j = 0; j < n_elem; j++) {
            printf("%.6f%s", dist_matrix[i][j], (j < n_elem - 1) ? "," : "");
        }
        printf("]%s", (i < n_elem - 1) ? "," : "");
    }
    printf("]}\n");

    return 0;
}