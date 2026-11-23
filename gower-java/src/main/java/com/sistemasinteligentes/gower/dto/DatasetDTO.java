package com.sistemasinteligentes.gower.dto;

import java.util.List;
import java.util.Map;

public class DatasetDTO {
    private int p1;
    private int p2;
    private int p3;
    private List<double[]> dataMatrix;
    private List<Integer> types;
    private List<Double> rangosGh;

    public DatasetDTO() {}

    public int getP1() { return p1; }
    public void setP1(int p1) { this.p1 = p1; }

    public int getP2() { return p2; }
    public void setP2(int p2) { this.p2 = p2; }

    public int getP3() { return p3; }
    public void setP3(int p3) { this.p3 = p3; }

    public List<double[]> getDataMatrix() { return dataMatrix; }
    public void setDataMatrix(List<double[]> dataMatrix) { this.dataMatrix = dataMatrix; }

    public List<Integer> getTypes() { return types; }
    public void setTypes(List<Integer> types) { this.types = types; }

    public List<Double> getRangosGh() { return rangosGh; }
    public void setRangosGh(List<Double> rangosGh) { this.rangosGh = rangosGh; }

    public Map<String, Integer> getSummary() {
        return Map.of(
                "p1", p1,
                "p2", p2,
                "p3", p3,
                "registros", dataMatrix != null ? dataMatrix.size() : 0
        );
    }
}