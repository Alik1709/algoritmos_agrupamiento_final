package com.sistemasinteligentes.gower.dto;
import java.util.List;

public class GowerDistanceRequest {
    private List<String> labels;
    private List<String> headers;
    private List<String> columnTypes;
    private List<List<Object>> matrix;

    public List<String> getLabels() { return labels; }
    public void setLabels(List<String> labels) { this.labels = labels; }

    public List<String> getHeaders() { return headers; }
    public void setHeaders(List<String> headers) { this.headers = headers; }

    public List<String> getColumnTypes() { return columnTypes; }
    public void setColumnTypes(List<String> columnTypes) { this.columnTypes = columnTypes; }

    public List<List<Object>> getMatrix() { return matrix; }
    public void setMatrix(List<List<Object>> matrix) { this.matrix = matrix; }
}
