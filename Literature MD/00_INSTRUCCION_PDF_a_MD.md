# INSTRUCCIÓN PERMANENTE · CONVERSIÓN PDF → MARKDOWN ULTRAFIEL

Proyecto BIA RAT (Impedancímetro BIS-CV) · versión 1.0 · 2026-10-06

Ubicación: `BIA RAT/Literature_MD/00_INSTRUCCION_PDF_a_MD.txt`

Uso: en cada llamada el agente recibe solo "Lee completo `C:\Users\edgar\Desktop\BIA RAT\Literature_MD\00_INSTRUCCION_PDF_a_MD.txt` y ejecútalo."

> Este archivo contiene la instrucción v1.0 completa, convertida a Markdown sin cambiar su contenido (secciones 0 a 14), y al final el **Anexo A** con las prácticas que se aplicaron en las conversiones para llegar a la máxima fidelidad. El anexo no forma parte de la v1.0.

---

## PROTOCOLO DE ARRANQUE (léelo primero, en CADA llamada)

1. Lee este archivo COMPLETO. Cada llamada empieza desde cero: no confíes en lo que creas recordar.
2. En esta llamada conviertes EXACTAMENTE UN PDF: el que indique el comando `next`. Ni uno más.
3. Lo que ya está hecho y lo que falta lo dice SOLO `00_CHECKPOINT.csv`, que se maneja con la herramienta `_tools/pdf2md_tools.py`.
4. Sigue el FLUJO (sección 4) paso por paso. Al cerrar ese PDF con `done`, entrega el reporte (sección 13) y DETENTE.
5. No pidas confirmación al usuario. Si algo te bloquea, regístralo con `done <ID> REVISAR` o `done <ID> ERROR` y detente.

---

## 1. OBJETIVO

Producir, para cada PDF de `BIA RAT/Literature`, un Markdown ULTRAFIEL: un gemelo digital del documento.

"Ultrafiel" significa:

- Mismo contenido: cada palabra, número, símbolo, ecuación, tabla, figura, leyenda, nota al pie, referencia, apéndice y cualquier otro elemento impreso.
- Mismo orden de lectura y misma jerarquía (títulos, secciones, subsecciones, listas).
- Mismas marcas tipográficas con significado: cursiva, negrita, subíndice, superíndice.
- Cero resumen, cero paráfrasis, cero traducción, cero "mejoras", cero corrección del autor (sus erratas se quedan), cero texto inventado.
- Lo que no es texto (gráficas, fotos, esquemas) se conserva como imagen de máxima calidad, enlazada en su lugar.
- Lo único que agrega el convertidor va en el front matter YAML o en comentarios `<!-- NOTA-CONV: ... -->`.

---

## 2. REGLAS INVIOLABLES

- **R1** Un solo PDF por llamada. Aunque te sobre tiempo o contexto, al cerrar el documento te detienes.
- **R2** Los PDF son de solo lectura. NUNCA borres, muevas, renombres, sobrescribas ni modifiques nada fuera de `Literature_MD/`. No toques `Literature/`, `Checkpoints/`, `BIMMS/`, `Claude outputs/` ni los catálogos.
- **R3** Dentro de `Literature_MD/` solo escribes: la carpeta del documento en curso (su .md y su `img/`), `_trabajo/<ID>/` y, a través de la herramienta, `00_CHECKPOINT.csv` y `00_BITACORA.md`. No borres nada, tampoco ahí.
- **R4** El checkpoint se modifica SOLO con la herramienta (`sync`, `lock`, `done`, `unlock`). A mano únicamente si la herramienta no puede ejecutarse (sección 12).
- **R5** No inventes. Lo ilegible se marca `[ilegible]`; una lectura dudosa se marca `[?]` justo después de la palabra o cifra. Nunca completes cifras, símbolos o palabras que no ves.
- **R6** No omitas. Todo lo impreso va en el .md (los encabezados y pies de página van en el marcador de su página).
- **R7** Idioma original. No traduzcas nada: ni títulos, ni leyendas, ni tablas.
- **R8** Lo impreso manda sobre la capa de texto. Si la capa de texto y la imagen difieren, transcribe lo que se ve impreso (confírmalo con zoom de 300 a 400 dpi); si la diferencia importa, explícala en `<!-- NOTA-CONV: ... -->`.
- **R9** Nunca declares COMPLETO sin: (a) haber visto TODAS las páginas como imagen, (b) QC automático PASS, o AVISO con cada aviso justificado en `--notas`, (c) la verificación visual final de la sección 9.
- **R10** Si se te acaba el contexto o el tiempo, guarda lo hecho y registra avance PARCIAL (sección 11). Nunca dejes un .md a medias sin registrar hasta qué página está verificado.
- **R11** Sin emojis y sin explicaciones dentro del .md fuera de NOTA-CONV y del YAML.

---

## 3. RUTAS Y ENTORNO

RAÍZ = la carpeta "BIA RAT" (carpeta padre de `Literature_MD`).

| Elemento | Ruta |
|---|---|
| En Windows del usuario | `C:\Users\edgar\Desktop\BIA RAT` |
| En Cowork (shell del equipo) | `$HOME/mnt/BIA RAT` |
| PDFs fuente (solo lectura) | `RAÍZ/Literature/<pilar>/<ID>.pdf` |
| Salida | `RAÍZ/Literature_MD/<pilar>/<ID>/<ID>.md` y `RAÍZ/Literature_MD/<pilar>/<ID>/img/` |
| Checkpoint (cola) | `RAÍZ/Literature_MD/00_CHECKPOINT.csv` |
| Bitácora | `RAÍZ/Literature_MD/00_BITACORA.md` |
| Herramienta | `RAÍZ/Literature_MD/_tools/pdf2md_tools.py` |
| Material de trabajo | `RAÍZ/Literature_MD/_trabajo/<ID>/` (desechable; el usuario lo puede borrar al terminar la cola) |
| EJEMPLO DE REFERENCIA | `RAÍZ/Literature_MD/02_BIS_Models/Ayllon2009_ColeParameterEstimation/Ayllon2009_ColeParameterEstimation.md`<br>Léelo completo antes de escribir: es el estándar de formato que debes igualar. |

En este archivo, `T <comando>` significa ejecutar la herramienta con su ruta completa (no depende de la carpeta actual):

```text
Cowork (shell del equipo):   python3 "$HOME/mnt/BIA RAT/Literature_MD/_tools/pdf2md_tools.py" <comando>
Windows (PowerShell o cmd):  python "C:\Users\edgar\Desktop\BIA RAT\Literature_MD\_tools\pdf2md_tools.py" <comando>
                             ("py" también sirve. NO uses "python3": en este Windows abre la Microsoft Store.
                             En PowerShell 5.1 no encadenes con &&; usa ; o una llamada por comando.)
Otro:                        cualquier shell con Python 3.9 o superior y la ruta completa al script.
```

La herramienta instala PyMuPDF por su cuenta si falta (`pip --user`); la primera vez puede tardar un minuto. `grid` usa Pillow.

Da a cada llamada de shell un tiempo límite amplio (prep de un bloque largo puede tardar más de 1 minuto).

Comandos: `sync` · `next` · `status` · `lock` · `unlock` · `prep` · `grid` · `crop` · `native` · `qc` · `done` (`T <comando> -h` muestra la ayuda).

**Cómo VER las páginas (obligatorio, R9):**

- Si puedes abrir imágenes del disco (Read, view_image, read_file o equivalente): abre `RAÍZ/Literature_MD/_trabajo/<ID>/pag/pNNN.jpg`. Si no tienes ninguna forma de ver imágenes, no puedes cumplir R9: registra `T done <ID> REVISAR --notas "el agente no puede ver imágenes"` y detente.
- En Cowork: sube las imágenes al contenedor con `device_stage_files` usando la ruta de Windows (`<trabajo_windows>\pag\pNNN.jpg`, es decir `C:\Users\edgar\Desktop\BIA RAT\Literature_MD\_trabajo\<ID>\pag\pNNN.jpg`; hasta 50 por llamada) y ábrelas con Read. Igual para `zoom\` y `grid\`. Alternativa: sube el PDF y léelo con Read usando el parámetro `pages`.
- Zoom de una región: `T crop <ID> <pág> x0 y0 x1 y1 <nombre> --dpi 300 --inspeccion` → `_trabajo/<ID>/zoom/<nombre>.png`. Las coordenadas son fracciones de 0 a 1 de la página (x hacia la derecha, y hacia abajo, origen arriba a la izquierda).
- Para ubicar coordenadas: `T grid <ID> <pág>` → `_trabajo/<ID>/grid/pNNN.png` con cuadrícula cada 0.05.

**Cómo ESCRIBIR el .md:**

- UTF-8 sin BOM, saltos de línea LF, una línea en blanco entre bloques.
- Escribe por partes, página por página, agregando al final del archivo. Nunca mandes el documento entero en un solo bloque gigante. Si tienes herramienta nativa para crear y editar archivos, úsala.
- En un shell bash (Cowork), con heredoc entre comillas y un delimitador único (las líneas del contenido van sin sangría; el primer bloque usa `>` y los siguientes `>>`):

  ```bash
  cat >> "<ruta del .md>" <<'__FIN_MD_7Q__'
  <contenido de la página>
  __FIN_MD_7Q__
  ```

- En PowerShell no uses `Set-Content`, `Add-Content`, `Out-File` ni `>` (cambian la codificación): usa tu herramienta nativa o Python.
- Para correcciones puntuales usa un reemplazo exacto (Python leer-modificar-escribir, sed o tu herramienta de edición), nunca reescribas de memoria.

---

## 4. FLUJO DE CADA LLAMADA (en este orden, sin saltarte pasos)

- **P0** Lee este archivo completo y las últimas 5 filas de `00_BITACORA.md`.
- **P1** `T sync`
  Agrega PDFs nuevos a la cola, detecta PDFs que cambiaron y recalcula el orden (lote 1 artículos, 2 normas y guías, 3 hojas de datos, 4 libros; dentro de cada lote, por número Ref. del catálogo).
- **P2** `T next`
  - `"accion": "REANUDAR"` → continúa ese documento (está EN_PROCESO).
  - `"accion": "INICIAR"` → ese es tu documento.
  - `"accion": "COLA_TERMINADA"` → reporta "Cola terminada", lista los REVISAR y detente.

  Anota: id, pdf, md, paginas, texto (si | ocr | no), tipo, paginas_esta_llamada y, si usas `device_stage_files`, trabajo_windows y pdf_windows (rutas de Windows ya armadas).
- **P3** `T lock <ID> --agente "<tu modelo o nombre de agente>"`
  Si responde que ya hay otro documento EN_PROCESO, ese es el tuyo: vuelve a P2.
- **P4** `T prep <ID>` (agrega `--ocr` si texto = no; en documentos largos prep toma solo el bloque que toca)
  Crea en `_trabajo/<ID>/`: `RESUMEN.txt`, `manifest.json`, `pag/` (páginas a 140 dpi), `txt/` (capa de texto por página), `draft/` (borrador con cursivas, negritas, sub y superíndices; "§" marca posibles títulos), `emb/` (imágenes incrustadas a resolución original) y `ocr/`. El borrador es solo ayuda: NUNCA lo copies sin verificarlo contra la imagen.
- **P5** Lee `RESUMEN.txt` y `manifest.json`. Lee el ejemplo de referencia. Mira TODAS las páginas del rango como imagen antes de escribir.
- **P6** Transcribe página por página (secciones 5 a 8). Por cada página: mira la imagen, toma los caracteres exactos de `txt/`, usa `draft/` como guía de estilos, haz zoom donde haya ecuaciones, tablas, símbolos o letra pequeña, y escribe el segmento de esa página con su marcador.
- **P7** Figuras y tablas (sección 7): extrae o recorta cada imagen, revísala, colócala en su lugar y transcribe leyenda y texto interno.
- **P8** `T qc <ID>` (en documentos largos: `T qc <ID> --paginas a-b` del bloque)
  Corrige TODAS las FALLAS y resuelve cada AVISO (corrigiendo o justificando). Repite qc hasta PASS; máximo 3 vueltas.
- **P9** Verificación visual final (sección 9), página por página, contra la imagen. Si corriges algo, repite `T qc <ID>`.
- **P10** Completa en el YAML `conversion.verificacion` y `conversion.qc` con el resultado final. Cambiar solo el YAML no obliga a repetir qc; cualquier cambio en el cuerpo sí (done compara el cuerpo con el del último qc y rechaza si cambió).
- **P11** Cierra con UNA de estas opciones:

  ```text
  T done <ID> COMPLETO [--notas "<justificación de cada AVISO, si hubo>"]
  T done <ID> PARCIAL --paginas-hechas N --notas "<qué falta exactamente>"
  T done <ID> REVISAR --notas "<qué no se pudo resolver y en qué páginas>"
  T done <ID> ERROR --notas "<causa: cifrado, dañado, ilegible…>"
  ```

- **P12** `T status`, entrega el reporte (sección 13) y DETENTE. No abras el siguiente PDF.

---

## 5. FORMATO DEL ARCHIVO .md

### 5.1 Front matter YAML

Al inicio, entre dos líneas `---`. Los campos con (\*) son obligatorios y el QC los revisa.

```text
---
titulo: "<título exacto>"                                    (*)
autores: ["<Autor 1>", "<Autor 2>"]                          (*) en el orden impreso; ["(sin autor)"] si no hay
fuente: "<revista o congreso, volumen, número, año, tal como está impreso>"
paginas_impresas: "<folios, p. ej. 3779-3782>"
anio: <año>
doi: "<DOI>"
doi_origen: "<'impreso en el PDF' o 'catálogo del proyecto'>"
idioma: "<en | es | de | …>"
clave: "<clave del catálogo, p. ej. Ayllon2009>"
ref_canon: <Ref. del checkpoint, si existe>
tipo: "<articulo | preprint | patente | norma | guia | datasheet | libro>"
fuente_pdf: "<columna pdf del checkpoint>"                   (*)
paginas_pdf: <total de páginas del PDF>                      (*)
sha12_pdf: "<columna sha12 del checkpoint>"                  (*)
capa_texto: "<si | ocr | no>"
ocr_confianza: "<alta | media | baja>"                       solo en escaneados
conversion:                                                  (*)
  fecha: "<AAAA-MM-DD>"
  agente: "<modelo o agente>"
  metodo: "<p. ej. capa de texto + verificación visual página por página + zoom en ecuaciones y tablas>"
  herramienta: "pdf2md_tools <versión>"
  instruccion: "00_INSTRUCCION_PDF_a_MD.txt v1.0"
  verificacion: "<páginas revisadas contra imagen y dónde hubo zoom>"
  qc: "<veredicto y métricas del último qc>"
notas_fidelidad:
  - "<decisiones que el lector debe conocer: imágenes nativas, discrepancias capa/imagen, elementos lado a lado, rotaciones…>"
---
```

Los metadatos no impresos se toman de `RAÍZ/Literature/catalogo_literatura.csv` indicando su origen. Si no existen, el campo se omite.

### 5.2 Cuerpo, en el orden del documento

- a) Marcador de la página 1.
- b) Bloque de título: título (`#`), autores con sus marcas de afiliación (`<sup>1</sup>`, \*, †), afiliaciones, correspondencia y correos, fechas (Received, Accepted, Published), datos editoriales, el resumen con su etiqueta original (Abstract, Resumen, Summary) y las palabras clave (Keywords, Index Terms). Todo tal cual y en el orden impreso.
- c) El cuerpo con sus secciones.
- d) Agradecimientos, financiamiento, conflictos de interés, contribuciones, disponibilidad de datos, apéndices, material suplementario incluido en el PDF, biografías y referencias: todo lo que esté en el PDF, en su orden.

No agregues índice, resúmenes, títulos inventados ni texto de cierre.

### 5.3 Marcadores de página

OBLIGATORIOS: uno por cada página física del PDF, en orden, sin duplicados.

```text
<!-- página N | impresa: X | encabezado: … | pie: … -->
```

- N es la página física del PDF (1 a paginas_pdf). "impresa" es el folio impreso, si existe.
- encabezado y pie: texto de encabezados, pies, folios, sellos de descarga, marcas de agua y avisos de licencia o copyright de esa página (varias líneas separadas con " / "). Omite el campo que no exista.
- Si la página empieza con un bloque nuevo, el marcador va solo en su línea, con una línea en blanco antes y después.
- Si el salto cae a mitad de párrafo u oración, el marcador va EN LÍNEA, exactamente en la frontera de palabras, sin partir el párrafo: `…To be able to estimate accurately the full Cole <!-- página 4 | impresa: 3782 --> equation from only…`
- Si una tabla cruza la página, el marcador de la página siguiente va inmediatamente después de la tabla, con `<!-- NOTA-CONV: la Tabla N continúa de la página X a la Y -->`.
- Página en blanco: lleva su marcador seguido de `<!-- NOTA-CONV: página en blanco -->`.

---

## 6. TÉCNICAS DE FIDELIDAD DEL TEXTO

- **6.1 Doble canal.** Si capa_texto = si, los caracteres salen de `txt/` (se copian, no se reescriben) y la estructura, el orden y los estilos salen de la imagen. Si es ocr o no, la imagen manda en todo y `txt/` y `ocr/` solo apoyan.
- **6.2 Orden de lectura.** Columnas de izquierda a derecha y de arriba abajo; los elementos a todo lo ancho (título, resumen, figuras o tablas anchas) en la posición vertical donde aparecen. Confirma siempre el orden en la imagen.
- **6.3 Párrafos.** Un párrafo del original es un párrafo del .md: una sola línea lógica, separado por una línea en blanco. Une las líneas; no conserves los saltos de línea internos. Si un párrafo continúa en otra columna o página, sigue siendo uno solo. La sangría del original indica párrafo nuevo; su ausencia indica continuación.
- **6.4 Guiones de fin de línea.** Quita el guion de partición ("impe-/dance" → "impedance"). Conserva los guiones reales ("multi-frequency", "wrist-to-ankle", "Cole-Cole", rangos como "1430-53", "analysis--part"). Si dudas, busca la palabra en el resto del documento. `manifest.json` trae "guiones_ambiguos": revísalos uno por uno contra la imagen.
- **6.5 Caracteres.** Unicode real: µ Ω ° ± × ÷ ≈ ≤ ≥ ∞ ∑ √ ∂ ∀ α…ω ′ ″ ‘ ’ “ ” é ñ ü, el signo menos (U+2212), la raya media (U+2013) y la raya larga (U+2014) tal como estén impresos. Nunca los cambies por ASCII ("ohm", "u", "+/-", "<="). Las ligaduras se escriben como letras (ﬁ → fi). Colapsa los espacios múltiples en uno. Escapa lo que Markdown interpretaría: `\*` y `\_` literales, `\#` al inicio de línea, `\|` dentro de tablas, `\$` para dinero, `&lt;` cuando un "<" vaya seguido de letra.
- **6.6 Estilos con significado:** cursiva `*…*`, negrita `**…**`, ambas `***…***`, subíndice `<sub>…</sub>`, superíndice `<sup>…</sup>` (unidades, fórmulas químicas como `H<sub>2</sub>O`, llamadas a nota, citas en superíndice). Conserva los estilos aunque parezcan errores del autor (una conjunción en cursiva se queda en cursiva). No agregues estilos que no existen. Versalitas: escribe las letras como se leen (mayúsculas). Letra capital (drop cap): únela a su palabra ("D"+"URING" → "DURING").
- **6.7 Matemáticas dentro del texto:** variables, símbolos y expresiones con subíndices, superíndices o letras griegas usadas como variables van en LaTeX en línea: `$R_0$`, `$R_\infty$`, `$f_C$`, `$|Z(\omega)|$`, `$\alpha \le 1$`. Números y unidades sueltos van como texto ("750 Ω", "3.55e-6"). Lo que está fuera de la expresión se respeta tal cual (`$R_\infty$= 560`).
- **6.8 Títulos.** Texto y numeración exactos ("II. METHODS", "2.1 Subjects", "A. Cole Equation"). Niveles: documento `#`, sección `##`, subsección `###`, sub-subsección `####`. No inventes ni quites numeración; no conviertas en título lo que no lo es. El estilo propio del título (versalitas, cursiva del encabezado) no se reproduce.
- **6.9 Listas.** Conserva viñetas, numeración y su estilo ("1)", "(a)", "i.") y el anidamiento. Las enumeraciones dentro de un párrafo se quedan dentro del párrafo.
- **6.10 Citas en el texto** exactamente como están: [12], [7, 8], (Smith et al 1998), `<sup>12</sup>`. No las conviertas en enlaces.
- **6.11 Notas al pie:** en el punto de llamada `[^n]` (numeración secuencial en todo el documento); la definición `[^n]: texto completo` va al final del segmento de esa página, antes del marcador siguiente. Si el original usa \*, †, ‡, ese símbolo es el primer carácter del texto de la nota.
- **6.12 Referencias bibliográficas:** todas, completas, en su orden, con su etiqueta original ([1], "1.", "Autor (Año)"), una por párrafo, con su puntuación, mayúsculas, cursivas, DOI y URL tal cual. No reformatees ni "corrijas" ninguna.
- **6.13 Elementos especiales:** recuadros, cuadros de texto, epígrafes, notas del editor, erratas, avisos de copyright dentro del cuerpo (van en el cuerpo). Algoritmos, código y pseudocódigo en bloque ` ``` ` con el texto exacto.
- **6.14 Preprints y manuscritos de autor:** omite los números de línea del margen y las marcas "Author Manuscript" o "NIH-PA Author Manuscript"; regístralos una vez en notas_fidelidad y en el marcador de la página 1.
- **6.15 Escaneados** (capa_texto ocr o no): transcribe desde la imagen con zoom de 300 dpi o más; la capa OCR es solo apoyo. Usa `[ilegible]` y `[?]`. Nunca adivines números. Agrega ocr_confianza al YAML y explica en notas_fidelidad.
- **6.16 Páginas rotadas o tablas apaisadas:** transcríbelas en el orden natural de lectura e indica la rotación en NOTA-CONV.

---

## 7. ECUACIONES, TABLAS Y FIGURAS

### 7.1 Ecuaciones en display

Cada ecuación aislada del original es un bloque así (los `$$` en líneas propias):

```text
$$
<LaTeX> \tag{<número exacto: 3, 3a, A.1, S2…>}
$$
```

- Transcribe desde la imagen con zoom de 300 a 400 dpi. La capa de texto de las ecuaciones sale desordenada: no la copies.
- Reproduce lo impreso símbolo por símbolo: sub y superíndices, barras, primas, paréntesis, fracciones, límites de sumas e integrales, fuentes (`\mathrm`, `\mathbf`, `\mathcal`). No simplifiques, no reordenes y no corrijas incoherencias del original (si una ecuación imprime R∞ sin subíndice, se escribe `R\infty`).
- Varias líneas con un solo número: `\begin{gathered}…\end{gathered}` o `\begin{aligned}…\end{aligned}` con un solo `\tag`. Ecuaciones lado a lado con números distintos: bloques consecutivos en orden de lectura y una nota en notas_fidelidad.
- Ecuación sin número: igual, sin `\tag`.
- Solo LaTeX compatible con MathJax y KaTeX: sin `\newcommand`, sin paquetes, sin `\label`. Entornos permitidos: aligned, gathered, cases, matrix, pmatrix, bmatrix, vmatrix, array.
- El texto entre ecuaciones ("where", "and") va como párrafo normal.

### 7.2 Tablas

- Etiqueta y título como están impresos y donde están (arriba o abajo): por ejemplo "TABLE I" en su línea y el título en el párrafo siguiente, o "Table 2. Body composition…". La línea de la etiqueta empieza con la etiqueta (el QC la busca).
- Tabla simple: tabla Markdown (GFM) con TODAS las celdas exactas (números, unidades, ±, signos, marcas de nota a, b, \*, †). Celda vacía es celda vacía.
- Celdas combinadas, encabezados de varios niveles o subtablas: tabla HTML (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` con `rowspan` y `colspan`). No aplanes la estructura.
- Las notas al pie de la tabla van en párrafos inmediatamente debajo, en su orden.
- SIEMPRE, debajo de cada tabla, su respaldo visual (recorte con título y notas: `T crop <ID> <pág> x0 y0 x1 y1 tabNN --dpi 300`):

  ```text
  <details><summary>Imagen original</summary>

  ![TABLE I](img/tab01.png)

  </details>
  ```

- Tablas que son imagen (escaneadas): transcríbelas celda por celda desde el zoom y conserva el recorte igual.
- Verifica cada número contra el zoom. Un dígito mal es un error de fidelidad.

### 7.3 Figuras

Una figura del original es un bloque en su posición:

```text
![Fig. 1](img/fig01.png)

<leyenda exactamente como está impresa, empezando con su etiqueta original: "Fig. 1.Curve fitting…", "Figure 2: …">

<!-- texto en la figura: títulos de paneles · etiquetas de ejes con unidades · leyendas · anotaciones y rótulos -->
```

- Cómo obtener la imagen (elige la de mayor fidelidad):
  - a) Si la figura completa es UNA imagen incrustada (en `manifest.json`, "imagenes": su caja cubre la figura con todos sus rótulos), usa la imagen nativa: `T native <ID> <xref> figNN` (píxeles originales, sin re-muestreo).
  - b) Si es vectorial, tiene rótulos como texto o se compone de varias piezas, recórtala de la página: `T crop <ID> <pág> x0 y0 x1 y1 figNN --dpi 300` (usa 600 si hay letra muy pequeña o trazos finos).

  Parte de "propuestas_recorte" del manifest y afina con `T grid`. El recorte incluye toda la figura (paneles, ejes, rótulos, leyenda interna) y NO incluye la leyenda impresa (esa se transcribe). ABRE cada imagen generada y revisa que no falte ni sobre nada.
- Nombres: `fig01.png`, `fig02.png`…; `tab01.png`…; subfiguras que el original separa: `fig03a.png`, `fig03b.png`. Otros gráficos con contenido (fotos de biografías, esquemas sin número): `img_pNNN_k.png`. No guardes logotipos ni adornos de la revista.
- La leyenda va sin negritas añadidas; si la etiqueta del original es negrita, entonces sí.
- El comentario "texto en la figura" transcribe títulos de paneles, ejes con unidades, leyendas y rótulos (los valores de las marcas de los ejes solo si tienen información propia). Si la figura no tiene texto, omite el comentario.
- Una figura de página completa también va en su lugar del flujo.

### 7.4 Flotantes

Nunca partas un párrafo para meter una figura o tabla. Si una figura o tabla está al pie o al inicio de la página, o el párrafo cruza el salto de página, colócala al terminar ese párrafo, en su orden físico, con `<!-- NOTA-CONV: Fig. N impresa en la página X -->`.

---

## 8. TIPOS ESPECIALES DE DOCUMENTO

- **8.1 Documentos largos** (más de 40 páginas): se trabajan por bloques de hasta 25 páginas por llamada (next y prep te dan el rango; puedes ajustarlo ±5 páginas con `prep --paginas a-b` para cortar en un límite de sección). Escribe en el mismo .md, agregando al final. Antes de empezar un bloque lee el final del .md para continuar sin duplicar ni perder texto (un párrafo puede venir partido del bloque anterior: termínalo en línea). Al cerrar cada bloque: `T qc <ID> --paginas a-b` y `T done <ID> PARCIAL --paginas-hechas b`. En el último bloque: `T qc <ID>` (completo) y `T done <ID> COMPLETO`.
- **8.2 Libros** (tipo libro): un archivo por capítulo dentro de la carpeta del documento, `capNN_<titulo-corto>.md`, cada uno con YAML y marcadores de página; `<ID>.md` es el índice: YAML del libro, páginas preliminares transcritas (portadilla, créditos, prefacio, contenido) y la lista de enlaces a los capítulos. Un bloque de páginas por llamada.
- **8.3 Hojas de datos** (datasheet): las tablas de especificaciones son críticas (cada valor, condición, unidad, min, typ, max y nota). Diagramas de pines, de bloques y de tiempos, y curvas típicas, son figuras (300 a 600 dpi). Mapas de registros como tablas. Incluye información de pedido, historial de revisiones y avisos legales.
- **8.4 Patentes:** portada con todos sus campos y códigos INID ((21), (22), (51)…), resumen, hojas de dibujos (cada FIG. como figura; si una hoja trae varias FIG., una imagen por FIG.), descripción con sus párrafos numerados [0001] tal cual y reivindicaciones completas con su numeración.
- **8.5 Normas y guías** (NOM, guías): numeración exacta de capítulos, incisos y apartados (5.1.2.3), tablas y anexos completos, y los datos de publicación oficial (DOF, fecha) en el bloque de título.
- **8.6 Material suplementario** incluido en el PDF: completo, después del cuerpo, con sus títulos originales.

---

## 9. VERIFICACIÓN VISUAL FINAL (obligatoria antes de cerrar)

Para CADA página, con la imagen abierta y el segmento del .md entre su marcador y el siguiente, comprueba:

- [ ] Están todos los bloques de la página y en el orden correcto (columna izquierda, luego derecha).
- [ ] Ninguna oración o línea omitida, repetida o mal unida en el cambio de columna o de página.
- [ ] Títulos con su numeración exacta y su nivel.
- [ ] Cursivas, negritas, subíndices y superíndices donde están en el original.
- [ ] Cada ecuación, símbolo por símbolo contra el zoom, con su número.
- [ ] Cada tabla, celda por celda contra el zoom (números, signos, unidades, notas).
- [ ] Cada figura: imagen correcta, completa y legible; leyenda exacta; texto interno transcrito.
- [ ] Notas al pie y sus llamadas.
- [ ] Encabezado y pie registrados en el marcador de la página.
- [ ] Ningún resto del borrador ("§", "BORRADOR AUTOMÁTICO", estilos rotos como `** **`).

Anota en `conversion.verificacion` las páginas revisadas y dónde hiciste zoom.

---

## 10. QC AUTOMÁTICO: QUÉ MIDE Y CÓMO DECIDIR

`T qc <ID>` compara el .md con el PDF, imprime el veredicto (PASS, AVISO = WARN, FALLA = FAIL) y guarda `_trabajo/<ID>/qc.json`.

- **cobertura:** fracción del texto en prosa del PDF que está en el .md. Digitales: PASS desde 0.985; AVISO entre 0.96 y 0.985; FALLA bajo 0.96. Escaneados: PASS desde 0.90; AVISO desde 0.80.
- **precisión:** fracción del texto del .md (sin ecuaciones en display ni "texto en la figura") que existe en el PDF. Mismos umbrales.
- **pasajes faltantes** (texto del PDF ausente en el .md) y **pasajes añadidos** (texto del .md que no existe en el PDF): con 8 o más palabras reales son FALLA.
- **números del .md que no están en el PDF:** FALLA en digitales (casi siempre es un dígito mal copiado); números del PDF ausentes en el .md: AVISO.
- También revisa: marcadores de página faltantes o duplicados, imágenes rotas, figuras o tablas del PDF sin leyenda en el .md, leyendas sin imagen, números de ecuación sin `\tag`, YAML incompleto o que no coincide con el checkpoint (fuente_pdf, paginas_pdf, sha12_pdf), `$` desbalanceados, tablas con columnas inconsistentes y marcadores prohibidos (TODO, [falta], [pendiente], lorem…).
- Con `--paginas a-b` solo evalúa ese bloque (con una página de contexto a cada lado para flotantes y párrafos partidos).

Reglas:

- Toda FALLA se corrige. Todo AVISO se corrige o se justifica en `--notas` al cerrar (ejemplo: "AVISO ec. 12: falso positivo, '(12)' es una cita a la ecuación dentro del texto").
- El QC no lo ve todo (no detecta un subíndice omitido ni un signo cambiado): por eso la sección 9 es obligatoria.
- Si tras 3 vueltas sigue en FALLA por algo que no puedes resolver (ilegible, PDF defectuoso): done REVISAR con el detalle.
- done COMPLETO se rechaza si: el último qc es FALLA, o AVISO sin `--notas`; ese qc no cubre el documento completo; el cuerpo del .md cambió después de ese qc; o faltan `conversion.verificacion` o `conversion.qc` en el YAML. Usa `--forzar` solo ante un falso positivo comprobado, y explícalo en `--notas`.

---

## 11. REANUDACIÓN, BLOQUEOS Y CONTEXTO

- Si next devuelve REANUDAR: abre el .md existente, ubica el último marcador de página escrito y lee la bitácora. Si paginas_hechas es 0 pero el .md tiene contenido, revisa ese contenido contra las imágenes antes de continuar.
- Si te quedas sin contexto o sin tiempo a mitad de un documento: termina la página en curso, verifícala, corre `T qc <ID> --paginas 1-N` y registra `T done <ID> PARCIAL --paginas-hechas N` con una nota precisa ("falta desde la página N+1; la Tabla 3 empezó en la página N, rehacerla completa").
- Un EN_PROCESO abandonado (más de 12 h sin avance en la bitácora) se reanuda igual. Solo si es imposible continuarlo: `T unlock <ID> --motivo "<razón>"`.
- Nunca abras un segundo documento para aprovechar la llamada.

---

## 12. SI ALGO FALLA

- No se puede escribir el CSV: probablemente está abierto en Excel. Dilo en el reporte y detente.
- PyMuPDF no se instala: usa poppler si existe (en Cowork sí está instalado):

  ```text
  página a imagen:   pdftoppm -f N -l N -r 140 -jpeg "<pdf>" "_trabajo/<ID>/pag/pNNN"
  recorte:           pdftoppm -f N -l N -r 300 -x X -y Y -W W -H H -png -singlefile "<pdf>" "<salida sin .png>"
                     (X, Y, W, H en píxeles a 300 dpi)
  imágenes nativas:  pdfimages -png -f N -l N "<pdf>" "_trabajo/<ID>/emb/pNNN"
  ```

  sync, next, lock, qc y done funcionan sin PyMuPDF.
- La herramienta no corre en absoluto: trabaja con las mismas reglas y actualiza a mano SOLO la fila del documento en `00_CHECKPOINT.csv` (UTF-8 con BOM, separador coma, comillas dobles en campos con comas), cambiando únicamente estado, paginas_hechas, inicio, fin, agente, qc y notas; agrega una fila a `00_BITACORA.md`. Explícalo en el reporte.
- PDF cifrado, dañado o vacío: `T done <ID> ERROR --notas "<causa>"`.

---

## 13. REPORTE FINAL (lo último que escribes en la llamada)

Formato fijo, en español:

```text
Documento: <ID> (orden <n> de <total>, Ref. <ref>)
Estado: COMPLETO | PARCIAL (páginas <a>-<b> de <N>) | REVISAR | ERROR
Salida: Literature_MD/<pilar>/<ID>/<ID>.md + <k> imágenes
QC: <veredicto> · cobertura <x> · precisión <y> · figuras <f/F> · tablas <t/T> · ecuaciones <e/E>
Verificación visual: <páginas revisadas; zooms>
Observaciones: <decisiones relevantes, avisos justificados, [?] e [ilegible] con su página>
Siguiente en la cola: <ID que da T next> · Progreso: <primera línea de T status>
```

---

## 14. CHECKLIST ANTES DE done

- [ ] Un solo PDF en esta llamada.
- [ ] Nada tocado fuera de Literature_MD.
- [ ] YAML completo.
- [ ] Un marcador por página, en orden.
- [ ] Todas las páginas vistas como imagen.
- [ ] Figuras con imagen revisada, leyenda y texto interno.
- [ ] Tablas celda por celda + recorte.
- [ ] Ecuaciones con `\tag` exacto, verificadas con zoom.
- [ ] Referencias completas.
- [ ] qc PASS, o AVISOS justificados.
- [ ] done ejecutado (checkpoint y bitácora).
- [ ] Reporte entregado. Fin de la llamada.

---

## ANEXO A. PRÁCTICAS APLICADAS PARA LLEGAR A LA MÁXIMA FIDELIDAD

Estas prácticas se usaron en las conversiones de la cola, por encima de lo que pide la v1.0. No sustituyen ninguna regla; las refuerzan.

### A.1 Organización del trabajo

- A petición del usuario se trabajó por tandas de 5 documentos, pero siempre uno a la vez: `lock` → conversión → `qc` → `done` antes de abrir el siguiente. Nunca hubo dos documentos EN_PROCESO.
- `lock`, `prep`, `crop`, `native`, `qc`, `done` y `status` se ejecutan en el equipo del usuario. La lectura, la redacción y la verificación se hacen en el espacio de trabajo del agente con una copia del PDF.
- El PDF se copia al espacio de trabajo y se comprueba su sha12 contra el checkpoint antes de empezar.

### A.2 Lectura de las páginas

- Cada página se mira completa a unos 1500 px de lado mayor. En escaneados se usa la imagen incrustada a su resolución original, no un re-muestreo.
- Zoom por regiones de 3x a 24x en ecuaciones, tablas, leyendas, notas al pie, rótulos de figuras, referencias y cualquier letra pequeña. Cada región de letra pequeña se lee al menos una vez con zoom.
- Para ubicar regiones se usan las cajas de palabra de la capa de texto (coordenadas exactas) en lugar de estimarlas a ojo.
- Para delimitar figuras y tablas antes de recortar se mide el perfil de tinta por renglón (bandas) en coordenadas de página. Si la página es una sola imagen desplazada o escalada, las coordenadas de la imagen no son las de la página: se mide sobre la página renderizada.
- Glifos dudosos (l, 1, I; 0 y o; R1 y Rl; ε₀ y εₒ): se miden los componentes conexos sobre la imagen nativa y se comparan con glifos seguros de la misma línea (alto, ancho, área, remates). Se decide por forma y métricas y se documenta en notas_fidelidad. Si no se puede decidir, `[?]`.
- Lo que el original imprime raro (erratas, nombres mal escritos, comillas desparejadas, encabezados repetidos en una tabla) se conserva y se lista en notas_fidelidad, con una NOTA-CONV si afecta la lectura.

### A.3 Redacción

- Un borrador por columna desde la capa de texto (con guiones unidos y los dudosos marcados) sirve solo para no teclear desde cero. Cada párrafo se confirma contra la imagen, palabra por palabra, antes de pasar al MD.
- El MD se arma con un script de construcción por documento: YAML aparte y cuerpo desde piezas verificadas (tablas desde listas de valores, referencias desde una lista, marcadores generados por función con folio, encabezado de página par e impar y pie o sello de descarga). Así cualquier corrección es un reemplazo exacto y nunca una reescritura de memoria.
- Párrafo partido entre columnas o páginas: el marcador va en línea en la frontera de palabras; si la palabra está partida entre páginas, el marcador va después de la palabra completa y se anota.
- Se verifica la sangría para decidir si el texto de la columna o página siguiente es párrafo nuevo o continuación.
- Guiones: cada caso de "guiones_ambiguos" se revisa en la imagen. Partición de sílaba se une; compuesto real se conserva; los dudosos se resuelven por el uso de la misma palabra en el documento y se anotan.
- Notas al pie: la definición va después del párrafo en el que termina la columna o la página donde la nota está impresa, con `<!-- NOTA-CONV: nota al pie impresa en la página X -->`.
- Fechas de recepción y aceptación, avisos de copyright de columna y datos de correspondencia van en el cuerpo, con NOTA-CONV si están fuera de su orden de lectura.
- Versalitas en mayúsculas también en autores de referencias y en etiquetas de tablas y figuras.
- Todo signo `<` del texto, de tablas y de notas se escribe `&lt;` (en LaTeX, `\lt`), porque el QC borra lo que parece etiqueta HTML aunque cruce líneas.

### A.4 Ecuaciones

- Todas las expresiones del MD (display y en línea) se validan con KaTeX antes de entregar; la meta es cero errores.
- Si el original imprime las letras de una ecuación en redonda, se usa `\mathrm` (KaTeX lo propaga dentro de raíces y subíndices).
- La etiqueta de `\tag` es la impresa: `\tag{Eq. 1}` si el original dice "(Eq. 1)".
- Las incoherencias del original (paréntesis sin cerrar, subíndices distintos para lo mismo) se conservan y se anotan.

### A.5 Figuras y tablas

- Recortes con `T crop … --dpi 400` (600 si hace falta). Figuras que son una imagen incrustada completa: `T native` con su xref.
- Todos los recortes se revisan juntos en una hoja de contactos y, si falta algo (por ejemplo, notas al pie de una tabla), se recorta de nuevo con un nombre `_v2 --inspeccion` y se copia encima del original, porque no se puede borrar.
- En páginas rotadas, las fracciones de `crop` siguen el rectángulo ya rotado de la página.
- Tablas con encabezado de dos niveles, filas de grupo o columnas combinadas: HTML con `rowspan` y `colspan`. Cada celda se verifica contra el zoom. Las tablas apaisadas se reconstruyen por posición de las palabras y se verifican celda por celda.
- Símbolos de leyenda sin equivalente exacto (cuadritos con relleno, patrones): carácter Unicode más parecido y una NOTA-CONV que explica qué representa cada uno.
- El comentario "texto en la figura" incluye rótulos de paneles, ejes con unidades, leyendas internas, anotaciones y escalas; lo ilegible se marca `[ilegible]`.

### A.6 Verificación antes del QC

- Comparación por página del MD contra la capa de texto (diferencias palabra a palabra) para detectar omisiones, duplicados y uniones mal hechas.
- El MD se renderiza (pandoc a HTML y captura con navegador) y se revisan tablas, notas al pie, listas numeradas, imágenes enlazadas y marcadores.
- Revisión de restos del borrador, estilos rotos y escapes.

### A.7 Lectura del QC y falsos positivos

- El QC descarta los renglones de 3 caracteres o menos y los que son casi solo letras sueltas. Con capas OCR de una palabra por renglón desaparecen "the", "of", "and" y aparecen decenas de "pasajes faltantes" falsos.
- `<sup>` y `<sub>` se quitan sin espacio: `0.6–0.8<sup>4</sup>` se lee "0.84" y `153.8<sup>b</sup>` se parte en "153". Los corchetes que el OCR lee como 1 ("[10]" como "101") generan números "faltantes".
- Para cada FALLA se replica localmente el cálculo de pasajes del QC (5-gramas) y se comprueba, palabra por palabra y en orden, que cada pasaje "faltante" está en el MD. Lo mismo con los números avisados, contra la imagen.
- Solo si todo lo reportado es falso positivo comprobado se cierra con `--forzar`, con `--notas` detalladas y con el mismo detalle en `conversion.qc`. Si hay un error real, se corrige y se repite `qc`.
- `conversion.verificacion` y `conversion.qc` se llenan después del último `qc` (cambiar solo el YAML no invalida el qc).

### A.8 Entrega y control

- El MD se escribe en el espacio de trabajo y se envía a su carpeta en el equipo; cada envío usa una subcarpeta nueva de versión y se comprueba el md5 en el equipo antes de `qc` y de `done`.
- Nunca se borra nada. Si una imagen debe reemplazarse, se genera la versión `_v2` y se copia encima.
- Si el checkpoint dice que la capa es digital pero en realidad es OCR (por ejemplo, Acrobat Capture), el YAML registra `capa_texto: "ocr"` y explica la discrepancia.
- Al final de cada documento se entrega el reporte de la sección 13 y se consulta `T status`.
