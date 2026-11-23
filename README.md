# Algoritmos de Agrupamiento Multi-Motor

Plataforma de análisis ETL y agrupamiento jerárquico/distancias con arquitectura distribuida compuesta por:

- **Gateway Python (`gateway-python/`):** API con FastAPI / Uvicorn (puerto `8000`) encargada de la ingesta de archivos (`.csv`, `.txt`, `.xlsx`, `.data`, `.docx`), diagnóstico ETL, recomendación de motor y orquestación.
- **Microservicio Gower (`gower-java/`):** Servicio en Java / Spring Boot (puerto `8080`) para cálculo de distancia de Gower sobre variables mixtas.
- **Motor Binario en C (`c-binario/`):** Código fuente en C y `CMakeLists.txt` para similitud/distancia binaria.
- **Motor Mahalanobis en C (`c-mahalanobis/`):** Código fuente en C y `CMakeLists.txt` para distancia de Mahalanobis.
- **Frontend (`frontend/`):** Interfaz web (`index.html`, estilos y scripts) para carga de datos, validación ETL y visualización de resultados.

> **Nota sobre binarios (`.exe`):** Por políticas de correo y buenas prácticas de control de versiones, el repositorio incluye el código fuente y archivos de compilación, excluyendo ejecutables (`.exe`), carpetas de compilación (`build`, `target`, `cmake-build-*`) y entornos virtuales mediante `.gitignore`.

---

## Estructura del repositorio

```text
algoritmos_agrupamiento_final/
├── .gitignore
├── README.md
├── gateway-python/
├── gower-java/
├── c-binario/
├── c-mahalanobis/
└── frontend/