//
// Created by alisL on 23/11/2026.
//
#include "binary_core.h"
#include <stdio.h>
#include <string.h>

int ejecutar_calculo_binario(
    ElementoBinario *elementos,
    int num_elementos,
    int num_vars,
    const char *metrica,
    double dist_matrix[MAX_ELEMENTS][MAX_ELEMENTS],
    char *reporte_validacion
) {
    if (num_elementos < 2) {
        strcpy(reporte_validacion, "Error: Se requieren al menos 2 elementos válidos tras la limpieza.");
        return 0;
    }

    // Validación estricta de dominio binario {0, 1} y consistencia dimensional
    for (int i = 0; i < num_elementos; i++) {
        if (elementos[i].num_columnas != num_vars) {
            sprintf(reporte_validacion, "Error en fila %d (%s): Longitud inconsistente (%d vs %d).",
                    i + 1, elementos[i].etiqueta, elementos[i].num_columnas, num_vars);
            return 0;
        }
        for (int k = 0; k < num_vars; k++) {
            int v = elementos[i].datos[k];
            if (v != 0 && v != 1) {
                sprintf(reporte_validacion, "Error en [%s, V%d]: Valor '%d' no es estrictamente binario (0 o 1).",
                        elementos[i].etiqueta, k + 1, v);
                return 0;
            }
        }
    }

    // Cálculo de estados a, b, c, d (Lógica original preservada)
    for (int i = 0; i < num_elementos; i++) {
        for (int j = 0; j < num_elementos; j++) {
            if (i == j) {
                dist_matrix[i][j] = 0.0;
                continue;
            }

            int a = 0, b = 0, c = 0, d = 0;
            for (int k = 0; k < num_vars; k++) {
                int val1 = elementos[i].datos[k];
                int val2 = elementos[j].datos[k];

                if (val1 == 1 && val2 == 1) a++;
                else if (val1 == 0 && val2 == 1) b++;
                else if (val1 == 1 && val2 == 0) c++;
                else if (val1 == 0 && val2 == 0) d++;
            }

            double sim = 0.0;
            if (strcmp(metrica, "SOKAL") == 0) {
                double total = (double)(a + b + c + d);
                sim = (total > 0.0) ? (double)(a + d) / total : 0.0;
            } else {
                // JACCARD por defecto
                double denom = (double)(a + b + c);
                sim = (denom > 0.0) ? (double)a / denom : 1.0; // Si ambos son todo ceros, distancia = 0
            }

            // Convertimos similitud [0,1] a disimilitud/distancia [0,1] para clustering jerárquico
            dist_matrix[i][j] = 1.0 - sim;
        }
    }

    sprintf(reporte_validacion,
            "Validación C-Binario exitosa: %d elementos x %d variables verificadas en dominio {0,1}. "
            "Similitud %s transformada a distancia (D = 1 - S).",
            num_elementos, num_vars, metrica);
    return 1;
}