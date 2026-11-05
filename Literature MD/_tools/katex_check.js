// Edgar Danyael Arellano Hernandez
// 220448792
const katex = require("katex");
let inbound = "";
process.stdin.on("data", (chunk) => (inbound += chunk)).on("end", () => {
  const verdicts = [];
  for (const item of JSON.parse(inbound || "[]")) {
    try {
      katex.renderToString(item.tex, { displayMode: !!item.display, throwOnError: true, strict: "ignore" });
    } catch (err) {
      verdicts.push({ tex: String(item.tex).slice(0, 160), error: String(err.message).slice(0, 220) });
    }
  }
  process.stdout.write(JSON.stringify(verdicts));
});
