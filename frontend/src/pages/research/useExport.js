function download(filename, text, mime = 'application/json') {
  const blob = new Blob([text], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function useExport() {

  function exportJSON(data, filename = 'export.json') {
    download(filename, JSON.stringify(data, null, 2));
  }

  function exportCSV(rows, filename = 'export.csv') {
    if (!rows.length) return;
    const headers = Object.keys(rows[0]);
    const lines = [
      headers.join(','),
      ...rows.map(r =>
        headers.map(h => {
          const v = r[h];
          const s = v == null ? '' : String(v);
          return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
        }).join(',')
      ),
    ];
    download(filename, lines.join('\n'), 'text/csv');
  }

  function exportReport(markdown, filename = 'report.md') {
    download(filename, markdown, 'text/markdown');
  }

  return { exportJSON, exportCSV, exportReport };
}
