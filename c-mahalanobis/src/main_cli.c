//
// Created by alisL on 23/11/2026.
//
#include "mahalanobis_core.h"
#include <stdio.h>
#include <stdlib.h>

static void imprimir_json_escape(const char *str) {
    putchar('"');
    for (const char *p = str; *p; p++) {
        if (*p == '"' || *p == '\\') {
            putchar('\\');
        }
        putchar(*p);
    }
    putchar('"');
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("{\"ok\": false, \"error\": \"Falta la ruta del archivo de entrada.\"}\n");
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        printf("{\"ok\": false, \"error\": \"No se pudo abrir el archivo de entrada.\"}\n");
        return 1;
    }

    int n_elem = 0, n_vars = 0;
    if (fscanf(f, "%d %d", &n_elem, &n_vars) != 2 || n_elem < 2 || n_vars < 1) {
        fclose(f);
        printf("{\"ok\": false, \"error\": \"Dimensiones invalidas en archivo de entrada.\"}\n");
        return 1;
    }

    ElementoNumerico *elementos = (ElementoNumerico *)calloc((size_t)n_elem, sizeof(ElementoNumerico));
    if (!elementos) {
        fclose(f);
        printf("{\"ok\": false, \"error\": \"Sin memoria para elementos.\"}\n");
        return 1;
    }

    for (int i = 0; i < n_elem; i++) {
        if (fscanf(f, "%63s", elementos[i].etiqueta) != 1) {
            free(elementos);
            fclose(f);
            printf("{\"ok\": false, \"error\": \"Error leyendo etiqueta en fila %d.\"}\n", i + 1);
            return 1;
        }
        elementos[i].num_columnas = n_vars;
        for (int j = 0; j < n_vars; j++) {
            if (fscanf(f, "%lf", &elementos[i].datos[j]) != 1) {
                free(elementos);
                fclose(f);
                printf("{\"ok\": false, \"error\": \"Error leyendo valor en fila %d, col %d.\"}\n", i + 1, j + 1);
                return 1;
            }
        }
    }
    fclose(f);

    double *dist_matrix = (double *)calloc((size_t)n_elem * (size_t)n_elem, sizeof(double));
    char reporte[512] = {0};

    if (!dist_matrix || !ejecutar_calculo_mahalanobis(elementos, n_elem, n_vars, dist_matrix, reporte)) {
        printf("{\"ok\": false, \"error\": ");
        imprimir_json_escape(reporte[0] ? reporte : "Error en cálculo de Mahalanobis.");
        printf("}\n");
        free(dist_matrix);
        free(elementos);
        return 1;
    }

    printf("{\"ok\": true, \"report\": ");
    imprimir_json_escape(reporte);
    printf(", \"distance_matrix\": [");
    for (int i = 0; i < n_elem; i++) {
        printf("[");
        for (int j = 0; j < n_elem; j++) {
            printf("%.6f%s", dist_matrix[i * n_elem + j], (j < n_elem - 1) ? "," : "");
        }
        printf("]%s", (i < n_elem - 1) ? "," : "");
    }
    printf("]}\n");

    free(dist_matrix);
    free(elementos);
    return 0;
}