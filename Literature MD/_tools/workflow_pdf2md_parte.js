// Edgar Danyael Arellano Hernandez
// 220448792
export const meta = {
  name: 'pdf2md-parte',
  description: 'Convierte en secuencia PDFs a Markdown ultrafiel y verifica cada documento con revisores independientes, un escéptico y un corrector',
  whenToUse: 'Cola PDF→MD de Literature MD: conversión secuencial con lock único + verificación adversarial por documento',
  phases: [
    { title: 'Convertir', detail: 'un subagente por PDF, en orden, respetando el lock único' },
    { title: 'Verificar', detail: 'revisores por lente: texto por bloques de 5 páginas, tablas/ecuaciones/figuras, estructura' },
    { title: 'Refutar', detail: 'escéptico que intenta refutar cada hallazgo contra la imagen' },
    { title: 'Corregir', detail: 'aplica solo hallazgos confirmados, repite qc y done' },
    { title: 'Commit', detail: 'commit y push a la rama del PR' },
  ],
}

const ROOT = '/home/user/Claude-Cloud'
const TOOL = `python3 "${ROOT}/Literature MD/_tools/pdf2md_tools.py"`
const RULES = `${ROOT}/Literature MD/00_INSTRUCCION_PDF_a_MD.md`
const EXAMPLE = `${ROOT}/Literature MD/Parte_01/Bernardis1968_LeeIndex_CarcassFat/Bernardis1968_LeeIndex_CarcassFat.md`
const BRANCH = 'claude/dazzling-volta-higt4t'
const ATTRIB = 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_013Y2sjkbNEQjaUYVUiLKCQ7'

const paths = d => ({
  pdf: `${ROOT}/Literature/${d.pilar}/${d.id}.pdf`,
  md: `${ROOT}/Literature MD/${d.pilar}/${d.id}/${d.id}.md`,
  dir: `${ROOT}/Literature MD/${d.pilar}/${d.id}`,
  work: `${ROOT}/Literature MD/_trabajo/${d.id}`,
})
const short = d => d.id.split('_')[0]

const CONVERT = {
  type: 'object',
  properties: {
    estado: { type: 'string', enum: ['COMPLETO', 'PARCIAL', 'REVISAR', 'ERROR', 'NO_INICIADO'] },
    reporte: { type: 'string' },
    herramienta: { type: 'string' },
  },
  required: ['estado', 'reporte', 'herramienta'],
}
const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          page: { type: 'integer' },
          category: { type: 'string' },
          md_actual: { type: 'string' },
          impreso: { type: 'string' },
          evidencia: { type: 'string' },
          severidad: { type: 'string', enum: ['alta', 'media', 'baja'] },
        },
        required: ['page', 'category', 'md_actual', 'impreso', 'evidencia', 'severidad'],
      },
    },
    paginas_revisadas: { type: 'array', items: { type: 'integer' } },
    resumen: { type: 'string' },
  },
  required: ['findings', 'paginas_revisadas', 'resumen'],
}
const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer' },
          confirmado: { type: 'boolean' },
          md_actual_real: { type: 'string' },
          correccion_exacta: { type: 'string' },
          motivo: { type: 'string' },
        },
        required: ['index', 'confirmado', 'motivo'],
      },
    },
  },
  required: ['verdicts'],
}
const FIXED = {
  type: 'object',
  properties: {
    aplicadas: { type: 'integer' },
    descartadas: { type: 'integer' },
    qc: { type: 'string' },
    estado: { type: 'string' },
    notas: { type: 'string' },
  },
  required: ['aplicadas', 'descartadas', 'qc', 'estado', 'notas'],
}

const convertPrompt = d => {
  const p = paths(d)
  return `Lee completo \`${RULES}\` y ejecútalo. En esta llamada tu documento es **${d.id}** (pilar ${d.pilar}). Responde y reporta en español.

Adaptaciones de este entorno. Tienen prioridad sobre las rutas y menciones de Windows/Cowork de la instrucción; todo lo demás de la instrucción aplica tal cual:

1. RAÍZ = \`${ROOT}\`. Donde la instrucción dice \`Literature_MD\`, aquí es la carpeta \`Literature MD\` (con espacio). Los PDFs fuente (solo lectura) están en \`RAÍZ/Literature/<pilar>/<ID>.pdf\`. La salida va en \`RAÍZ/Literature MD/<pilar>/<ID>/<ID>.md\` + \`img/\`.
2. \`T <comando>\` = \`${TOOL} <comando>\` (versión \`pdf2md_tools 1.3-cloud\`). Tiene los mismos comandos de la instrucción, más \`find <ID> <pág> "texto"\`, que devuelve las cajas del texto en fracciones 0-1 y sirve para ubicar recortes con precisión. \`crop\` y \`native\` escriben en \`img/\` del documento; con \`--inspeccion\` escriben en \`_trabajo/<ID>/zoom/\`. Para sustituir una imagen ya existente en \`img/\` usa \`--reemplazar\`.
3. P2: ejecuta \`T next --pilar ${d.pilar}\`. Debe devolver \`${d.id}\`; si devuelve otro, no hagas nada más y devuelve estado NO_INICIADO explicando qué devolvió. P3: \`T lock ${d.id} --agente "Claude Code"\`. En el YAML, \`conversion.agente: "Claude Code"\`. No escribas nombres ni versiones de modelo en ningún archivo.
4. Para VER las páginas usa la herramienta Read sobre los archivos de imagen (\`${p.work}/pag/pNNN.jpg\`, \`zoom/*.png\`, \`grid/*.png\`). \`device_stage_files\` no existe aquí ni hace falta.
5. EJEMPLO DE REFERENCIA (sustituye a Ayllon2009, que no existe aquí): \`${EXAMPLE}\`. Léelo completo antes de escribir y abre también su \`img/tab01.png\`. Iguala su formato: marcadores, YAML, notas_fidelidad, tabla HTML con rowspan, notas de tabla, \`<details>\`, notas al pie y referencias.
6. No hay \`catalogo_literatura.csv\`: omite los campos que solo saldrían del catálogo (\`ref_canon\`, y \`doi\` si no está impreso en el PDF). \`capa_texto\` sale del checkpoint, salvo el caso del Anexo A.8.
7. En documentos con capa OCR, \`draft/\` viene sin estilos: las cursivas, negritas, sub y superíndices se toman de la imagen.
8. Dentro de tablas HTML el Markdown no se procesa: usa \`<em>\`, \`<strong>\`, \`<sup>\` y \`<sub>\`. Las expresiones \`$…$\` sí se permiten. Todo \`<\` literal se escribe \`&lt;\`.
9. El \`qc\` ordena la capa de texto por columnas cuando viene intercalada, normaliza acentos descompuestos, valida con KaTeX todas las expresiones (display y en línea), quita \`<sup>\`/\`<sub>\` sin espacio (igual que la capa de texto), trata el guion entre dígitos como separador e ignora el texto de \`<summary>\`. Para el render de A.6, si lo usas, tienes \`pandoc\` y Playwright con Chromium (\`require('playwright')\`).
10. Escribe SOLO en \`Literature MD/${d.pilar}/${d.id}/\`, en \`Literature MD/_trabajo/${d.id}/\` y, a través de la herramienta, en el checkpoint y la bitácora. No modifiques la herramienta, ni los ZIP, ni otros documentos. No ejecutes comandos de git (el orquestador hace commit y push). Si encuentras un fallo de la herramienta, rodéalo sin editarla y descríbelo en el reporte.
11. Después del cierre, un verificador independiente revisará tu trabajo página por página; no lo esperes ni lo menciones en el .md.
12. Devuelve: estado (COMPLETO, PARCIAL, REVISAR, ERROR, o NO_INICIADO si next no devolvió tu documento), reporte (el reporte completo de la sección 13 con su formato fijo) y herramienta (problemas de la herramienta, o "sin problemas").`
}

const commonVerifier = d => {
  const p = paths(d)
  return `Eres un VERIFICADOR INDEPENDIENTE de una conversión PDF→Markdown ultrafiel ya cerrada. Responde en español.
Documento: ${d.id} · PDF: ${p.pdf} · MD: ${p.md} · imágenes del .md: ${p.dir}/img/ · capa de texto: ${d.texto} · páginas del PDF: ${d.paginas}
Reglas: lee primero, completas, las secciones 1, 2 y 5 a 9 y el Anexo A de ${RULES}. Definen qué es correcto: por ejemplo, versalitas en mayúsculas, guiones de partición unidos, erratas del autor conservadas, encabezados y pies dentro del marcador de página, notas al pie con [^n], NOTA-CONV para flotantes. Lo que la instrucción ordena NO es error.
Herramientas: las páginas a 140 dpi están en ${p.work}/pag/pNNN.jpg (míralas con Read). Para zoom: \`${TOOL} crop ${d.id} <pág> x0 y0 x1 y1 <nombre> --dpi 300 --inspeccion\` (fracciones 0-1; la imagen queda en ${p.work}/zoom/<nombre>.png; usa nombres que empiecen con el prefijo indicado abajo). \`${TOOL} find ${d.id} <pág> "texto"\` da las cajas de un texto; \`${TOOL} grid ${d.id} <pág>\` da la página con cuadrícula. La capa de texto (${p.work}/txt/pNNN.txt) ayuda a ubicar diferencias, pero manda lo impreso (R8). Si una imagen de página no existe, haz un recorte de la página completa (0 0 1 1) a 140 dpi con --inspeccion.
Prohibido: editar o crear archivos fuera de ${p.work}/zoom/ y ${p.work}/grid/; ejecutar \`qc\`, \`done\`, \`lock\`, \`unlock\`, \`prep\`, \`sync\` o git.
Reporta SOLO discrepancias reales que hayas confirmado con zoom, nada de preferencias. Para cada hallazgo:
- page: la página física.
- category.
- md_actual: fragmento EXACTO copiado del .md, lo bastante largo para ser único (compruébalo con \`grep -cF\`).
- impreso: el texto con que debe sustituirse md_actual, del mismo alcance y con el formato Markdown correcto según la instrucción.
- evidencia: el recorte usado y lo que se ve.
- severidad: alta si cambia contenido o cifras; media si afecta un estilo con significado, un símbolo o la estructura; baja si es un detalle menor.
Si no encuentras nada, devuelve findings vacío. En paginas_revisadas pon las páginas que revisaste completas, y en resumen describe qué revisaste y con qué zoom.`
}

const textLens = (d, a, b) => `${commonVerifier(d)}

TU LENTE: TEXTO de las páginas ${a} a ${b}. Prefijo de recortes: ver_txt_${a}_
Para cada página del rango, abre la imagen completa y luego revisa con zoom de 300 a 400 dpi TODA región de texto, renglón por renglón y columna por columna. Compara el segmento del .md entre su marcador \`<!-- página N\` y el siguiente contra lo impreso.
Busca:
- palabras, cifras o signos omitidos, añadidos o cambiados;
- el orden de bloques y columnas;
- párrafos mal unidos o mal partidos (la sangría indica párrafo nuevo);
- guiones de fin de línea mal resueltos;
- cursivas, negritas, subíndices y superíndices que falten o sobren;
- caracteres Unicode equivocados (comillas, rayas, signo menos, µ, ±, ·, °, ligaduras);
- llamadas y definiciones de notas al pie;
- encabezado, pie y folio del marcador;
- títulos (texto, numeración y nivel);
- leyendas de figuras y tablas como texto.

Fuera de tu lente quedan las celdas de las tablas, las ecuaciones en display y las imágenes de figura: los revisa otro verificador.`

const objectLens = d => `${commonVerifier(d)}

TU LENTE: TABLAS, ECUACIONES y FIGURAS de todo el documento (páginas 1 a ${d.paginas}). Prefijo de recortes: ver_obj_
- Tablas:
  - cada celda contra zoom de 400 a 600 dpi (números, signos, unidades, ±, marcas de nota a, b, *, †);
  - la estructura: encabezados de varios niveles, rowspan y colspan, filas de grupo;
  - la etiqueta y el título exactos, y las notas de la tabla justo debajo;
  - el recorte \`<details>\` completo (con título y notas) y legible.
- Ecuaciones:
  - cada ecuación en display y cada expresión en línea, símbolo por símbolo, contra zoom de 400 a 600 dpi;
  - sub y superíndices, primas, barras, paréntesis, fracciones, límites y fuentes (\\mathrm, \\mathbf…);
  - el número exacto en \\tag.
- Figuras:
  - abre cada imagen de img/ con Read y compárala con la página;
  - debe estar completa (ejes, rótulos, paneles, leyendas internas, escalas), sin la leyenda impresa, bien orientada y legible;
  - la leyenda transcrita debe ser exacta;
  - el comentario "texto en la figura" debe ser correcto y completo;
  - revisa la posición en el flujo y la NOTA-CONV de los flotantes.
- Comprueba que no falte en el .md ninguna figura ni tabla del PDF.

En un hallazgo de imagen (recorte incompleto o sobrante) usa category "imagen", pon en md_actual el enlace de la imagen y en impreso el recorte correcto: página y fracciones x0 y0 x1 y1, verificadas con grid o find.`

const structureLens = d => `${commonVerifier(d)}

TU LENTE: ESTRUCTURA y FORMATO de todo el documento. Prefijo de recortes: ver_est_
- YAML:
  - los campos obligatorios de 5.1;
  - titulo y autores exactos y en orden;
  - fuente, anio y doi correctos (el doi solo si está impreso);
  - notas_fidelidad veraces: comprueba en la imagen cada cosa que afirman del original.
- Marcadores:
  - uno por página física, en orden;
  - el folio impreso correcto;
  - encabezado y pie completos (sellos de descarga, avisos de copyright o licencia, marcas de agua);
  - los marcadores en línea, justo en la frontera de palabras.
- Títulos: texto, numeración y nivel exactos, sin títulos inventados ni omitidos.
- Bloque de título: autores con sus marcas, afiliaciones, correspondencia, fechas, resumen y palabras clave, en el orden impreso.
- Notas al pie: [^n] secuenciales, la llamada en su punto, la definición en su sitio y el símbolo original al inicio si el original usa *, † o ‡.
- Referencias: todas, completas y en orden, con su etiqueta, puntuación, cursivas, negritas, DOI y URL tal cual; compáralas una por una con zoom.
- Markdown:
  - escapes (\\*, \\_, \\#, &lt;);
  - listas que pandoc convertiría por error;
  - \`<details>\`;
  - restos de borrador (§, ⟦-⟧, BORRADOR, ** **);
  - NOTA-CONV justificadas.
  Renderiza con \`pandoc "${paths(d).md}" -f markdown+tex_math_dollars --katex -s -o "${paths(d).work}/zoom/ver_render.html"\` y revisa el HTML para detectar listas, tablas o notas mal formadas.`

const skepticPrompt = (d, batch) => {
  const p = paths(d)
  return `Eres un ESCÉPTICO. Responde en español. Otros verificadores reportaron posibles discrepancias entre el Markdown ${p.md} y el PDF ${p.pdf} (documento ${d.id}, capa de texto ${d.texto}). Tu trabajo es intentar REFUTAR cada hallazgo mirando tú mismo lo impreso con zoom.
Herramientas:
- \`${TOOL} crop ${d.id} <pág> x0 y0 x1 y1 esc_<k> --dpi 400 --inspeccion\` (la imagen queda en ${p.work}/zoom/);
- \`${TOOL} find ${d.id} <pág> "texto"\` y \`${TOOL} grid ${d.id} <pág>\`;
- las páginas a 140 dpi están en ${p.work}/pag/.

Lee las secciones 5 a 7 y el Anexo A de ${RULES}. Lo que la instrucción ordena no es error: versalitas en mayúsculas, erratas del autor conservadas, guiones de partición unidos, encabezados dentro del marcador, entre otros.

Para cada hallazgo, identificado por su index:
- confirmado=true solo si compruebas en la imagen que el .md difiere de lo impreso Y que la corrección propuesta es la correcta según las reglas. Si dudas, confirmado=false.
- Si confirmas, pon en correccion_exacta el texto completo que debe sustituir a md_actual. Comprueba con \`grep -cF\` que md_actual aparece tal cual en el .md; si no aparece literal o no es único, pon en md_actual_real un fragmento exacto y único del .md y escribe correccion_exacta para ese fragmento.
- En motivo explica qué viste.

No edites archivos fuera de ${p.work}/zoom/ ni ejecutes qc, done, lock, prep ni git.

Hallazgos (JSON):
${JSON.stringify(batch, null, 1)}`
}

const fixPrompt = (d, fixes) => {
  const p = paths(d)
  return `Eres el CORRECTOR del documento ${d.id}. Responde en español. Aplica al .md ${p.md} SOLO las correcciones de abajo, que un escéptico independiente ya confirmó contra la imagen. Las reglas están en ${RULES}: secciones 3 (cómo escribir), 5 a 7, 9 y 10, y Anexo A.
1. Cada corrección es un reemplazo exacto de md_actual por correccion_exacta: lee el archivo, modifícalo y escríbelo (con Python o tu herramienta de edición). Si el fragmento no aparece literal o aparece varias veces, ubícalo con más contexto y corrige solo ese punto. Antes de aplicar, mira tú mismo la imagen (zoom con \`${TOOL} crop ${d.id} <pág> x0 y0 x1 y1 fix_<k> --dpi 400 --inspeccion\`); si la corrección resulta incorrecta, no la apliques y anótalo.
2. Si la corrección es de imagen, rehaz el recorte con \`${TOOL} crop ${d.id} <pág> x0 y0 x1 y1 <nombre> --dpi 400 --reemplazar\` (o \`native … --reemplazar\`) y abre el resultado para revisarlo.
3. Ejecuta \`${TOOL} qc ${d.id}\`. Corrige toda FALLA real y repite, como máximo 3 vueltas.
4. Actualiza el YAML:
   - en \`conversion.verificacion\`, agrega al final: "; verificación independiente posterior: <n> hallazgos confirmados y corregidos (<resumen breve por página>)";
   - en \`conversion.qc\`, pon el resultado del último qc: veredicto, métricas y la justificación de cada aviso.
5. Cierra con \`${TOOL} done ${d.id} COMPLETO --notas "<justificación de cada AVISO>; verificación independiente: <n> correcciones"\`. La nota anterior del documento está en la columna notas de \`${ROOT}/Literature MD/00_CHECKPOINT.csv\`; reutiliza sus justificaciones si siguen vigentes.
   - Si el qc queda en FALLA por un falso positivo comprobado (Anexo A.7), usa --forzar con la explicación.
   - Si no logras dejarlo bien, cierra con \`done ${d.id} REVISAR --notas "<qué falta>"\`.

No toques otros documentos, la herramienta ni git. Devuelve: aplicadas, descartadas, qc (veredicto y métricas finales), estado final y notas (qué corregiste y qué descartaste, con su motivo).

Correcciones (JSON):
${JSON.stringify(fixes, null, 1)}`
}

let gitQueue = Promise.resolve()
const commit = message => {
  const run = gitQueue.then(() => agent(`En ${ROOT} publica los cambios de "Literature MD" en la rama ${BRANCH}. Ejecuta estos pasos y nada más:
1. \`cd ${ROOT} && git add -A "Literature MD"\`
2. Si \`git diff --cached --quiet\` termina con código 0 (no hay cambios), detente y responde "sin cambios".
3. Haz commit con \`git commit -q -F -\`, pasando por stdin con un heredoc exactamente este mensaje:
${message}

${ATTRIB}
4. \`git push -q -u origin ${BRANCH}\`. Si falla por red, reintenta hasta 4 veces, esperando 2, 4, 8 y 16 s.
Si algún paso falla porque existe \`.git/index.lock\` (otra operación de git en curso), espera unos segundos y repite desde el paso 1, como máximo 5 veces. No ejecutes ningún otro comando de git: nada de reset, checkout, stash, rebase, pull, merge ni force. Responde solo con el hash corto del commit o con "sin cambios".`, { label: `commit:${message.slice(0, 40)}`, phase: 'Commit', model: 'haiku', effort: 'low' }))
  gitQueue = run.catch(() => null)
  return run
}

const pageChunks = (n, size) => {
  const out = []
  for (let a = 1; a <= n; a += size) out.push([a, Math.min(n, a + size - 1)])
  return out
}

const verifyChain = async d => {
  const lenses = pageChunks(d.paginas, 5).map(([a, b]) => ({ key: `texto p${a}-${b}`, prompt: textLens(d, a, b) }))
  lenses.push({ key: 'tablas-ecuaciones-figuras', prompt: objectLens(d) })
  lenses.push({ key: 'estructura', prompt: structureLens(d) })
  const reviews = (await parallel(lenses.map(l => () =>
    agent(l.prompt, { label: `verificar:${short(d)}:${l.key}`, phase: 'Verificar', schema: FINDINGS })))).filter(Boolean)
  const seen = new Set()
  const findings = []
  for (const r of reviews) {
    for (const f of r.findings) {
      const key = `${f.page}|${f.md_actual.trim()}`
      if (seen.has(key)) continue
      seen.add(key)
      findings.push({ index: findings.length, ...f })
    }
  }
  log(`${short(d)}: ${findings.length} hallazgos de ${reviews.length}/${lenses.length} revisores`)
  if (!findings.length) {
    return { id: d.id, revisores: reviews.length, hallazgos: 0, confirmados: 0, correccion: null }
  }
  const batches = []
  for (let i = 0; i < findings.length; i += 15) batches.push(findings.slice(i, i + 15))
  const verdicts = (await parallel(batches.map((batch, k) => () =>
    agent(skepticPrompt(d, batch), { label: `refutar:${short(d)}:${k + 1}`, phase: 'Refutar', schema: VERDICTS }))))
    .filter(Boolean).flatMap(v => v.verdicts)
  const confirmed = verdicts.filter(v => v.confirmado && findings[v.index]).map(v => {
    const f = findings[v.index]
    return { index: v.index, page: f.page, category: f.category, severidad: f.severidad,
      md_actual: v.md_actual_real || f.md_actual, correccion_exacta: v.correccion_exacta || f.impreso,
      evidencia_verificador: f.evidencia, motivo_esceptico: v.motivo }
  })
  log(`${short(d)}: ${confirmed.length}/${findings.length} hallazgos confirmados por el escéptico`)
  if (!confirmed.length) {
    return { id: d.id, revisores: reviews.length, hallazgos: findings.length, confirmados: 0, correccion: null }
  }
  const fix = await agent(fixPrompt(d, confirmed), { label: `corregir:${short(d)}`, phase: 'Corregir', schema: FIXED })
  await commit(`Corrige ${d.id} tras verificación independiente (${confirmed.length} hallazgos confirmados)`)
  return { id: d.id, revisores: reviews.length, hallazgos: findings.length, confirmados: confirmed.length, correccion: fix }
}

const verifyOnly = args.verifyOnly || []
const toConvert = args.convert || []
const chains = verifyOnly.map(d => verifyChain(d))
const conversions = {}

phase('Convertir')
for (const d of toConvert) {
  let rep = null
  for (let attempt = 1; attempt <= 4; attempt++) {
    rep = await agent(convertPrompt(d), { label: `convertir:${short(d)}${attempt > 1 ? ` #${attempt}` : ''}`, phase: 'Convertir', schema: CONVERT })
    if (!rep || rep.estado !== 'PARCIAL') break
    log(`${short(d)}: PARCIAL, continúa en una nueva llamada (${attempt + 1})`)
  }
  const state = rep ? rep.estado : 'SIN_RESPUESTA'
  conversions[d.id] = { estado: state, reporte: rep ? rep.reporte : '', herramienta: rep ? rep.herramienta : '' }
  log(`${short(d)}: conversión ${state}`)
  await commit(`Agrega ${d.id} (conversión ${state})`)
  if (state === 'NO_INICIADO' || state === 'SIN_RESPUESTA') {
    log(`Cola detenida en ${d.id}: ${state}`)
    break
  }
  if (state === 'COMPLETO') chains.push(verifyChain(d))
}

const verified = await Promise.all(chains)
await commit(`Actualiza checkpoint y bitácora tras la verificación (${verified.length} documentos)`)
return { conversiones: conversions, verificacion: verified }
