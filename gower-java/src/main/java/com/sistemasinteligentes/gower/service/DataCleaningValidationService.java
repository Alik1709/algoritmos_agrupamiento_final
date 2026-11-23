package com.sistemasinteligentes.gower.service;

import com.sistemasinteligentes.gower.dto.DatasetDTO;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class DataCleaningValidationService {

    public DatasetDTO processAndValidate(List<String[]> rawData) {
        return processInternal(rawData, true);
    }

    public DatasetDTO validateFromMatrix(List<List<Object>> matrix) {
        if (matrix == null || matrix.isEmpty()) {
            throw new IllegalStateException("La matriz recibida para Gower está vacía.");
        }

        List<String[]> converted = new ArrayList<>();
        for (List<Object> row : matrix) {
            if (row == null) continue;
            String[] arr = new String[row.size()];
            for (int c = 0; c < row.size(); c++) {
                Object cell = row.get(c);
                if (cell == null) {
                    arr[c] = "";
                } else if (cell instanceof String strVal) {
                    String trimmed = strVal.trim();
                    if (isNumeric(trimmed)) {
                        arr[c] = trimmed;
                    } else if (!trimmed.isEmpty()) {
                        // Convierte etiqueta categórica en código numérico entero estable
                        arr[c] = String.valueOf(Math.abs(trimmed.hashCode() % 10000) + 1);
                    } else {
                        arr[c] = "";
                    }
                } else {
                    arr[c] = String.valueOf(cell);
                }
            }
            converted.add(arr);
        }

        // false: el gateway ya separó los IDs en labels, no descartar columna 0 por secuencia numérica
        return processInternal(converted, false);
    }

    private DatasetDTO processInternal(List<String[]> rawData, boolean detectNumericIdCol) {
        if (rawData == null || rawData.isEmpty()) {
            throw new IllegalStateException("El archivo subido está vacío o no contiene datos legibles.");
        }

        int maxCols = 0;
        for (String[] row : rawData) {
            if (row.length > maxCols) maxCols = row.length;
        }

        int totalFilasRaw = rawData.size();

        List<Integer> validCols = new ArrayList<>();
        for (int c = 0; c < maxCols; c++) {
            int countValidos = 0;
            for (String[] row : rawData) {
                if (c < row.length && isNumeric(row[c].trim())) {
                    countValidos++;
                }
            }
            if (countValidos >= Math.max(2, totalFilasRaw * 0.3)) {
                validCols.add(c);
            }
        }

        if (validCols.isEmpty()) {
            throw new IllegalStateException("No se encontraron columnas numéricas válidas en el archivo.");
        }

        if (detectNumericIdCol && !validCols.isEmpty()) {
            boolean firstColIsId = true;
            int idCol = validCols.get(0);
            int expectedId = 1;
            for (String[] row : rawData) {
                if (idCol < row.length && isNumeric(row[idCol].trim())) {
                    double val = Double.parseDouble(row[idCol].trim());
                    if (val != expectedId) {
                        firstColIsId = false;
                        break;
                    }
                    expectedId++;
                }
            }
            if (firstColIsId && validCols.size() > 1) {
                validCols.remove(0);
            }
        }

        List<String[]> validRows = new ArrayList<>();
        for (String[] row : rawData) {
            int llenos = 0;
            for (int colIdx : validCols) {
                if (colIdx < row.length && isNumeric(row[colIdx].trim())) {
                    llenos++;
                }
            }
            if (llenos >= Math.ceil(validCols.size() * 0.5)) {
                validRows.add(row);
            }
        }

        if (validRows.size() < 2) {
            throw new IllegalStateException("El dataset limpio debe tener al menos 2 registros numéricos válidos para calcular distancias.");
        }

        List<Integer> colTypes = new ArrayList<>();
        Map<Integer, Double> colMeans = new HashMap<>();
        Map<Integer, Double> colModes = new HashMap<>();
        List<Double> rangosGh = new ArrayList<>();

        int p1 = 0, p2 = 0, p3 = 0;

        for (int i = 0; i < validCols.size(); i++) {
            int colIdx = validCols.get(i);
            List<Double> numerosColumna = new ArrayList<>();
            Set<Double> unicos = new HashSet<>();
            boolean tieneDecimales = false;
            double minVal = Double.MAX_VALUE;
            double maxVal = -Double.MAX_VALUE;

            for (String[] row : validRows) {
                if (colIdx < row.length && isNumeric(row[colIdx].trim())) {
                    double val = Double.parseDouble(row[colIdx].trim());
                    numerosColumna.add(val);
                    unicos.add(val);
                    if (val < minVal) minVal = val;
                    if (val > maxVal) maxVal = val;
                    if (val % 1 != 0) tieneDecimales = true;
                }
            }

            Map<Double, Integer> frec = new HashMap<>();
            double moda = numerosColumna.isEmpty() ? 0.0 : numerosColumna.get(0);
            int maxFrec = 0;
            for (double num : numerosColumna) {
                int count = frec.getOrDefault(num, 0) + 1;
                frec.put(num, count);
                if (count > maxFrec) {
                    maxFrec = count;
                    moda = num;
                }
            }
            colModes.put(i, moda);

            if (unicos.stream().allMatch(val -> val == 0.0 || val == 1.0) && unicos.size() <= 2) {
                p2++; // Binaria
                colTypes.add(2);
            } else if (tieneDecimales || unicos.size() > Math.max(4, validRows.size() * 0.3)) {
                double suma = 0;
                for (double num : numerosColumna) suma += num;
                double media = numerosColumna.isEmpty() ? 0.0 : suma / numerosColumna.size();
                colMeans.put(i, media);

                double rango = maxVal - minVal;
                if (rango == 0.0) {
                    throw new IllegalStateException(String.format("Varianza Cero en columna %d: Todos los valores son %.2f.", i + 1, minVal));
                }
                p1++; // Cuantitativa continua
                colTypes.add(1);
                rangosGh.add(rango);
            } else {
                p3++; // Cualitativa (código entero)
                colTypes.add(3);
            }
        }
        int tiposPresentes = (p1 > 0 ? 1 : 0) + (p2 > 0 ? 1 : 0) + (p3 > 0 ? 1 : 0);
        if (tiposPresentes < 2) {
            throw new IllegalStateException(String.format(
                    "Validación de Variables Mixtas Fallida: Gower requiere variables mixtas (al menos 2 tipos distintos). Detectadas -> p1(cuantitativas): %d, p2(binarias): %d, p3(cualitativas): %d.",
                    p1, p2, p3
            ));
        }

        List<double[]> cleanRows = new ArrayList<>();
        for (String[] row : validRows) {
            double[] parsedRow = new double[validCols.size()];
            for (int i = 0; i < validCols.size(); i++) {
                int colIdx = validCols.get(i);
                int colType = colTypes.get(i);

                if (colIdx < row.length && isNumeric(row[colIdx].trim())) {
                    parsedRow[i] = Double.parseDouble(row[colIdx].trim());
                } else {
                    if (colType == 1) {
                        parsedRow[i] = Math.round(colMeans.get(i) * 100.0) / 100.0;
                    } else {
                        parsedRow[i] = colModes.get(i);
                    }
                }
            }
            cleanRows.add(parsedRow);
        }

        DatasetDTO dataset = new DatasetDTO();
        dataset.setP1(p1);
        dataset.setP2(p2);
        dataset.setP3(p3);
        dataset.setTypes(colTypes);
        dataset.setRangosGh(rangosGh);
        dataset.setDataMatrix(cleanRows);

        return dataset;
    }

    private boolean isNumeric(String str) {
        if (str == null || str.trim().isEmpty()) return false;
        try {
            Double.parseDouble(str.trim());
            return true;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}