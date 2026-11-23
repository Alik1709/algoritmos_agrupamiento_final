package com.sistemasinteligentes.gower.controller;

import com.sistemasinteligentes.gower.dto.DatasetDTO;
import com.sistemasinteligentes.gower.dto.GowerDistanceRequest;
import com.sistemasinteligentes.gower.service.DataCleaningValidationService;
import com.sistemasinteligentes.gower.service.FileReaderService;
import com.sistemasinteligentes.gower.service.GowerCalculatorService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/gower")
@CrossOrigin(origins = "*")
public class GowerController {

    private final FileReaderService fileReaderService;
    private final DataCleaningValidationService validationService;
    private final GowerCalculatorService calculatorService;

    public GowerController(
            FileReaderService fileReaderService,
            DataCleaningValidationService validationService,
            GowerCalculatorService calculatorService
    ) {
        this.fileReaderService = fileReaderService;
        this.validationService = validationService;
        this.calculatorService = calculatorService;
    }

    @PostMapping("/calculate")
    public ResponseEntity<?> processDataset(@RequestParam("file") MultipartFile file) throws Exception {
        var rawData = fileReaderService.read(file);
        DatasetDTO cleanedData = validationService.processAndValidate(rawData);

        Map<String, Object> calculo = calculatorService.buildDistanceMatrix(cleanedData);
        double[][] distanceMatrix = (double[][]) calculo.get("matrix");
        String bitacoraText = (String) calculo.get("log");

        return ResponseEntity.ok(Map.of(
                "summary", cleanedData.getSummary(),
                "matrix", distanceMatrix,
                "log", bitacoraText
        ));
    }

    @PostMapping("/distance")
    public ResponseEntity<?> calculateFromGateway(@RequestBody GowerDistanceRequest request) {
        DatasetDTO cleanedData = validationService.validateFromMatrix(request.getMatrix());
        Map<String, Object> calculo = calculatorService.buildDistanceMatrix(cleanedData);

        double[][] distanceMatrix = (double[][]) calculo.get("matrix");
        String bitacoraText = (String) calculo.get("log");

        return ResponseEntity.ok(Map.of(
                "ok", true,
                "distanceMatrix", distanceMatrix,
                "report", String.format(
                        "Gower (Java) validado y calculado: %d registros | p1(cuantitativa)=%d, p2(binaria)=%d, p3(cualitativa)=%d.",
                        cleanedData.getDataMatrix().size(),
                        cleanedData.getP1(),
                        cleanedData.getP2(),
                        cleanedData.getP3()
                ),
                "log", bitacoraText
        ));
    }
}