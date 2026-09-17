// n8n Code node — collapses the many parsed rows (one n8n item each) into a
// single item holding a `rows` array, so the following HTTP Request node
// sends one bulk Supabase upsert instead of one request per row.

return [{ json: { rows: $input.all().map(item => item.json) } }];
