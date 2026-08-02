// Document export (Feature 5). Client-side, dependency-free:
//  - Markdown: a lossless download of the raw source.
//  - PDF: render the already-sanitized preview HTML into a print window and
//    invoke the browser's print-to-PDF (matches the preview appearance without
//    pulling in a heavy PDF library).

function download(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function safeName(title: string): string {
  return (title.trim() || "document").replace(/[^\w.-]+/g, "-").replace(/^-+|-+$/g, "");
}

export function exportMarkdown(title: string, content: string): void {
  download(`${safeName(title)}.md`, new Blob([content], { type: "text/markdown" }));
}

export function exportPdf(title: string, previewHtml: string): void {
  const w = window.open("", "_blank", "width=820,height=1000");
  if (!w) return;
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
             color: #111; max-width: 720px; margin: 40px auto; padding: 0 24px 48px; line-height: 1.6; }
      pre { background: #f4f5f7; padding: 12px; border-radius: 8px; overflow-x: auto; }
      code { background: #f4f5f7; padding: 1px 5px; border-radius: 4px; }
      table { border-collapse: collapse; } td, th { border: 1px solid #ccc; padding: 4px 10px; }
      img, svg { max-width: 100%; height: auto; }
      @media print { @page { margin: 18mm; } }
    </style></head><body>${previewHtml}</body></html>`);
  w.document.close();
  // Give the new document a tick to lay out (images/svg) before printing.
  w.onload = () => { w.focus(); w.print(); };
  setTimeout(() => { try { w.focus(); w.print(); } catch { /* onload handled it */ } }, 400);
}
