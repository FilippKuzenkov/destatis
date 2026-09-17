// n8n Code node — parses the GENESIS employment index CSV (table 45212-0002)
// into rows, mirroring scripts/pull_employment.py's parse_rows().
// Input: the HTTP Request node's response (raw CSV in Object.Content).

const raw = $input.first().json.Object.Content;

const MONTH_NUMBER = {
  January: 1, February: 2, March: 3, April: 4,
  May: 5, June: 6, July: 7, August: 8,
  September: 9, October: 10, November: 11, December: 12,
};

const MISSING_VALUES = new Set(["-", "x"]);
const parseValue = (raw) => (MISSING_VALUES.has(raw) ? null : parseFloat(raw));

const rows = [];
for (const line of raw.split("\n")) {
  const fields = line.split(";");
  if (!fields[0].startsWith("WZ08-")) continue;
  if (fields.length !== 6) {
    throw new Error(`Expected 6 fields, got ${fields.length}: ${line}`);
  }
  const [wz08_code, description, yearStr, monthName, indexStr, changeStr] = fields;
  const period = `${yearStr}-${String(MONTH_NUMBER[monthName]).padStart(2, "0")}-01`;
  rows.push({
    json: {
      wz08_code,
      description,
      period,
      index_value: parseValue(indexStr),
      yoy_change_pct: parseValue(changeStr),
    },
  });
}

return rows;
