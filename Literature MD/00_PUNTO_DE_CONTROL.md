# Punto de control · sesión del 2026-11-05 (cierre 06:10)

Rama `claude/dazzling-volta-higt4t` · PR https://github.com/MFKazeBME/Claude-Cloud/pull/1 · herramienta `pdf2md_tools 1.3-cloud`

## Estado global

- Cola: 56 PDF (1787 páginas). COMPLETO 15 · PENDIENTE 41 · EN_PROCESO 0. Páginas convertidas: 147.
- Parte_01: 15 de 19 COMPLETO. Faltan Wang1999, Wiltschko2015, Zhang2000 y PercieDuSert2020.
- Parte_02 a Parte_11: sin iniciar.
- La fuente de verdad es `00_CHECKPOINT.csv`. El detalle de cada paso está en `00_BITACORA.md`.

## Parte_01 · detalle

| Orden | Documento | Conversión | QC final | Verificación independiente |
|---|---|---|---|---|
| 1 | Bernardis1968 | COMPLETO | AVISO justificado | completa: 0 hallazgos |
| 2 | Bertin1998 | COMPLETO | AVISO justificado | completa: 1 confirmado y corregido |
| 3 | Bland1986 | COMPLETO | AVISO justificado | completa: 2 confirmados y corregidos |
| 4 | Feely2000 | COMPLETO | PASS | completa: 0 hallazgos |
| 5 | Folch1957 | COMPLETO | FALLA forzada (falso positivo de la capa OCR) | completa: 1 confirmado y corregido |
| 6 | Gerbaix2010 | COMPLETO | PASS | completa: 1 confirmado y corregido |
| 7 | Jebb1996 | COMPLETO | AVISO justificado | completa: 1 confirmado y corregido |
| 8 | Judex2010 | COMPLETO | PASS | completa: 1 confirmado y corregido |
| 9 | Kunnecke2004 | COMPLETO | FALLA forzada (glifos de MathematicalPi en la capa) | completa: 0 hallazgos |
| 10 | Lee1929 | COMPLETO | AVISO justificado | completa: 4 confirmados y corregidos |
| 11 | Lin1989 | COMPLETO | FALLA forzada (capa OCR de ecuaciones) | completa: 9 confirmados y corregidos |
| 12 | Nixon2010 | COMPLETO | PASS | completa: 0 hallazgos |
| 13 | Novelli2007 | COMPLETO | FALLA forzada (fuentes de símbolos en la capa) | completa: 1 confirmado y corregido |
| 14 | Ronneberger2015 | COMPLETO | PASS | completa: 0 hallazgos |
| 15 | Taicher2003 | COMPLETO | PASS | INCOMPLETA: solo texto de las páginas 1-5 (0 hallazgos) |
| 16 | Wang1999 | PENDIENTE (interrumpida) | — | — |
| 17 | Wiltschko2015 | PENDIENTE | — | — |
| 18 | Zhang2000 | PENDIENTE | — | — |
| 19 | PercieDuSert2020 | PENDIENTE (lote 2, guía) | — | — |

Notas:

- Las cuatro FALLA forzadas tienen en la columna `notas` del checkpoint y en `conversion.qc` del YAML la réplica local que demuestra el falso positivo. Además, el verificador independiente revisó página por página cada uno de esos documentos.
- Wang1999 se interrumpió después de `prep`: no hay .md, solo recortes en `Parte_01/Wang1999_HydrationFatFreeMass/img/` (fig01-03, tab01-04). Se liberó con `unlock` y volvió a PENDIENTE. Quien lo retome debe revisar esos recortes contra la imagen antes de usarlos, y rehacer con `--reemplazar` los que no sirvan.

## Pendiente, en este orden

1. Terminar la verificación independiente de Taicher2003: texto de las páginas 6-13, tablas/ecuaciones/figuras y estructura.
2. Convertir y verificar Wang1999, Wiltschko2015 (29 pp.), Zhang2000 (22 pp.) y PercieDuSert2020.
3. Seguir con Parte_02 en adelante. Casos especiales:
   - Nath2019 viene partido en dos PDF (p01-10 y p11-23).
   - Wilson2025 (patente) no tiene capa de texto: `prep --ocr` necesita tesseract, que no está instalado en este entorno.
   - Documentos largos (más de 40 páginas) en bloques de 25: AD5940 (142), MAX30009 (97), NOM-062 (59), THS4631 (52), Ravi2024 (42).
   - Martinsen2023 (619 páginas) va como libro: un archivo por capítulo.
   - El AFE4300 es la hoja de datos abreviada (10 pp.).

## Cómo retomar

- Herramienta: `python3 "Literature MD/_tools/pdf2md_tools.py" <comando>`.
  - `sync` extrae los ZIP a `Literature/`, que no se versiona.
  - `next --pilar Parte_01` da el siguiente documento.
  - `status` muestra el progreso.
  - Requiere PyMuPDF y Pillow. Para KaTeX: `npm install` en `_tools/`.
- Flujo por documento: `lock` → `prep` → transcripción con verificación visual → `qc` → `done`, según `00_INSTRUCCION_PDF_a_MD.md`. El ejemplo de referencia es `Parte_01/Bernardis1968_LeeIndex_CarcassFat/`.
- Orquestación: `_tools/workflow_pdf2md_parte.js` es el workflow que se usó. Convierte en secuencia, con un solo documento EN_PROCESO, y verifica cada documento con revisores por lente, un escéptico y un corrector; hace commit y push tras cada paso.
  - Sus argumentos son `{"verifyOnly": [...], "convert": [...]}`, con elementos `{"id", "pilar", "paginas", "texto"}` tomados del checkpoint.
  - Para ejecutarlo, quita las dos primeras líneas de comentario: el script debe empezar con `export const meta`.
- Para retomar Parte_01: `verifyOnly` = Taicher2003 y `convert` = Wang1999, Wiltschko2015, Zhang2000 y PercieDuSert2020.
