// n8n Code node — parses the GENESIS retail turnover CSV (table 45212-0005)
// into long-format rows, mirroring scripts/pull_retail.py's parse_rows().
// Input: the HTTP Request node's response (raw CSV in Object.Content).

const raw = $input.first().json.Object.Content;

const MONTH_NUMBER = {
  January: 1, February: 2, March: 3, April: 4,
  May: 5, June: 6, July: 7, August: 8,
  September: 9, October: 10, November: 11, December: 12,
};

const VALUE_COLUMNS = [
  ["constant", "unadjusted"],
  ["constant", "calendar_adjusted"],
  ["constant", "calendar_seasonal_adjusted"],
  ["current", "unadjusted"],
  ["current", "calendar_adjusted"],
  ["current", "calendar_seasonal_adjusted"],
];

const rows = [];
for (const line of raw.split("\n")) {
  const fields = line.split(";");
  if (!fields[0].startsWith("WZ08-")) continue;
  const [wz08_code, description, yearStr, monthName, ...values] = fields;
  if (values.length !== VALUE_COLUMNS.length) {
    throw new Error(`Expected ${VALUE_COLUMNS.length} value columns, got ${values.length}: ${line}`);
  }
  const period = `${yearStr}-${String(MONTH_NUMBER[monthName]).padStart(2, "0")}-01`;
  VALUE_COLUMNS.forEach(([price_type, adjustment], i) => {
    const rawValue = values[i];
    rows.push({
      json: {
        wz08_code,
        description,
        period,
        price_type,
        adjustment,
        value: rawValue === "-" ? null : parseFloat(rawValue),
      },
    });
  });
}

return rows;
