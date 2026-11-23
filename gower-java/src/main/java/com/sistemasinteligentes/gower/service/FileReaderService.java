package com.sistemasinteligentes.gower.service;

import com.opencsv.CSVReader;
import org.apache.poi.ss.usermodel.*;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

@Service
public class FileReaderService {

    public List<String[]> read(MultipartFile file) throws Exception {
        String filename = Objects.requireNonNull(file.getOriginalFilename()).toLowerCase();
        if (filename.endsWith(".csv")) {
            return readCsv(file);
        } else if (filename.endsWith(".xlsx") || filename.endsWith(".xls")) {
            return readXlsx(file);
        } else {
            throw new IllegalArgumentException("Formato no soportado. Debe subir un archivo .csv o .xlsx");
        }
    }

    private List<String[]> readCsv(MultipartFile file) throws Exception {
        List<String[]> records = new ArrayList<>();
        try (InputStreamReader isr = new InputStreamReader(file.getInputStream());
             CSVReader reader = new CSVReader(isr)) {
            String[] line;
            while ((line = reader.readNext()) != null) {
                boolean tieneContenido = false;
                for (String cell : line) {
                    if (cell != null && !cell.trim().isEmpty()) {
                        tieneContenido = true;
                        break;
                    }
                }
                if (tieneContenido) {
                    records.add(line);
                }
            }
        }
        return records;
    }

    private List<String[]> readXlsx(MultipartFile file) throws Exception {
        List<String[]> records = new ArrayList<>();
        DataFormatter formatter = new DataFormatter();

        try (InputStream is = file.getInputStream();
             Workbook workbook = WorkbookFactory.create(is)) {

            Sheet sheet = workbook.getSheetAt(0);
            for (Row row : sheet) {
                int lastCellNum = row.getLastCellNum();
                if (lastCellNum <= 0) continue;

                boolean tieneContenido = false;
                String[] rowData = new String[lastCellNum];
                for (int c = 0; c < lastCellNum; c++) {
                    Cell cell = row.getCell(c, Row.MissingCellPolicy.CREATE_NULL_AS_BLANK);
                    String cellValue = formatter.formatCellValue(cell).trim();
                    rowData[c] = cellValue;
                    if (!cellValue.isEmpty()) {
                        tieneContenido = true;
                    }
                }
                if (tieneContenido) {
                    records.add(rowData);
                }
            }
        }
        return records;
    }
}