package com.sistemasinteligentes.gower.service;

import com.sistemasinteligentes.gower.dto.DatasetDTO;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class GowerCalculatorService {

    public Map<String, Object> buildDistanceMatrix(DatasetDTO dataset) {
        int n = dataset.getDataMatrix().size();
        double[][] distanceMatrix = new double[n][n];
        StringBuilder bitacoraTotal = new StringBuilder();

        for (int i = 0; i < n; i++) {
            for (int j = i; j < n; j++) {
                if (i == j) {
                    distanceMatrix[i][j] = 0.0;
                } else {
                    Object[] resultadoPaso = calculateGowerDistance(dataset, i, j);
                    double dist = (double) resultadoPaso[0];
                    String textoPaso = (String) resultadoPaso[1];

                    bitacoraTotal.append(textoPaso);

                    distanceMatrix[i][j] = dist;
                    distanceMatrix[j][i] = dist; // Simetría matricial d_ij = d_ji
                }
            }
        }

        Map<String, Object> response = new HashMap<>();
        response.put("matrix", distanceMatrix);
        response.put("log", bitacoraTotal.toString());
        return response;
    }

    private Object[] calculateGowerDistance(DatasetDTO data, int i, int j) {
        int p1 = data.getP1();
        int p2 = data.getP2();
        int p3 = data.getP3();
        List<Integer> types = data.getTypes();
        List<Double> rangosGh = data.getRangosGh();

        double[] row_i = data.getDataMatrix().get(i);
        double[] row_j = data.getDataMatrix().get(j);

        double sumQuant = 0.0;
        int a = 0;
        int d = 0;
        int alfa = 0;
        int ghIdx = 0;

        StringBuilder log = new StringBuilder();
        log.append(String.format("\n---> Analizando Par (X%d, X%d)\n", i + 1, j + 1));

        for (int c = 0; c < types.size(); c++) {
            int colType = types.get(c);
            double val_i = row_i[c];
            double val_j = row_j[c];

            if (colType == 1) { // Cuantitativa continua
                double G_h = rangosGh.get(ghIdx++);
                double operacion = (1.0 - (Math.abs(val_i - val_j) / G_h));
                sumQuant += operacion;
                log.append(String.format("   Col %d [Cuantitativa]: (1 - |%.2f - %.2f| / %.2f) = %.3f\n", c + 1, val_i, val_j, G_h, operacion));
            } else if (colType == 2) { // Binaria
                int b_i = (int) val_i;
                int b_j = (int) val_j;
                if (b_i == 1 && b_j == 1) {
                    a++;
                    log.append(String.format("   Col %d [Binaria]: Coincidencia (1,1) -> a=%d\n", c + 1, a));
                } else if (b_i == 0 && b_j == 0) {
                    d++;
                    log.append(String.format("   Col %d [Binaria]: Coincidencia (0,0) -> d=%d\n", c + 1, d));
                } else {
                    log.append(String.format("   Col %d [Binaria]: Diferentes (%d,%d) -> Sin coincidencia\n", c + 1, b_i, b_j));
                }
            } else if (colType == 3) { // Cualitativa (identificador entero)
                int q_i = (int) val_i;
                int q_j = (int) val_j;
                if (q_i == q_j) {
                    alfa++;
                    log.append(String.format("   Col %d [Cualitativa]: Coincidencia (%d=%d) -> alfa=%d\n", c + 1, q_i, q_j, alfa));
                } else {
                    log.append(String.format("   Col %d [Cualitativa]: Diferentes (%d!=%d)\n", c + 1, q_i, q_j));
                }
            }
        }

        double numerador = sumQuant + a + alfa;
        double denominador = (double) p1 + (p2 - d) + p3;
        double S_ij = denominador > 0 ? (numerador / denominador) : 0.0;
        double D_ij = Math.sqrt(1.0 - S_ij);

        log.append(String.format("   [Fórmula]: S_ij = (%.3f + %d + %d) / (%d + (%d - %d) + %d)\n", sumQuant, a, alfa, p1, p2, d, p3));
        log.append(String.format("   [Resultado]: S_ij = %.4f ---> d_ij = sqrt(1 - %.4f) = %.4f\n", S_ij, S_ij, D_ij));

        return new Object[]{D_ij, log.toString()};
    }
}