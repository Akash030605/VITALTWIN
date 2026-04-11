/**
 * parsePdf.js — Browser-side PDF text extractor using pdfjs-dist.
 * Runs entirely client-side. No server needed for PDF → text step.
 *
 * Usage:
 *   import { extractTextFromPdf } from "@/lib/parsePdf";
 *   const text = await extractTextFromPdf(file); // File object from <input type="file">
 */

/**
 * Extract all text content from a PDF File object.
 * Returns a concatenated string of all pages' text.
 *
 * @param {File} file - A PDF File object (from input[type=file])
 * @returns {Promise<string>} - Raw text extracted from all pages
 */
export async function extractTextFromPdf(file) {
  if (typeof window === "undefined") {
    throw new Error("PDF extraction must run in the browser.");
  }

  // Dynamically import pdfjs-dist to avoid SSR issues
  const pdfjsLib = await import("pdfjs-dist");

  // Use unpkg CDN for the worker — avoids Turbopack bundling issues with .mjs workers.
  // The CDN version must match the installed pdfjs-dist version.
  const pdfjsVersion = pdfjsLib.version || "4.10.38";
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsVersion}/build/pdf.worker.min.mjs`;

  // Convert File to ArrayBuffer
  const arrayBuffer = await file.arrayBuffer();

  // Load the PDF document
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

  const totalPages = pdf.numPages;
  const pageTexts = [];

  // Extract text from each page
  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const textContent = await page.getTextContent();

    // Join all text items on the page, preserving spacing
    const pageText = textContent.items
      .map((item) => ("str" in item ? item.str : ""))
      .join(" ");

    pageTexts.push(pageText);
  }

  // Join all pages with newlines, collapse excess whitespace
  return pageTexts.join("\n").replace(/\s{2,}/g, " ").trim();
}
