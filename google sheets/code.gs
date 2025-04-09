const API_URL = "your-ngrok-url";
const MAX_RUNTIME_MS = 300000; // 5 min
const BATCH_SIZE = 3;

/********************
 * UI FUNCTIONS *
 ********************/

/**
 * Creates custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("LeadGen AI")
    .addItem("Show Outreach Sidebar", "showOutreachSidebar")
    .addToUi();
}

/**
 * Shows the outreach sidebar
 */
function showOutreachSidebar() {
  const html = HtmlService.createHtmlOutputFromFile("Sidebar")
    .setTitle("Generate Outreach Messages")
    .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Gets available template options from server
 */
function getTemplateOptions() {
  try {
    const response = UrlFetchApp.fetch(`${API_URL}/template-options`, {
      method: "get",
      muteHttpExceptions: true,
    });

    if (response.getResponseCode() === 200) {
      return JSON.parse(response.getContentText());
    }
    return [
      "Cold Email (Professional)",
      "LinkedIn Connection (Friendly)",
      "Follow-up (Direct)",
    ];
  } catch (e) {
    return [
      "Cold Email (Professional)",
      "LinkedIn Connection (Friendly)",
      "Follow-up (Direct)",
    ];
  }
}

/**
 * Generate outreach message using API (for sidebar)
 */
function generateOutreachMessage(template, product, companyData) {
  try {
    const payload = JSON.stringify({
      url: companyData.url || "",
      template_key: template,
      product: product,
      company_data: companyData,
    });

    const response = UrlFetchApp.fetch(`${API_URL}/generate-outreach`, {
      method: "post",
      contentType: "application/json",
      payload: payload,
      muteHttpExceptions: true,
    });

    const code = response.getResponseCode();
    const content = response.getContentText();

    if (code !== 200) {
      return { error: `API returned ${code}: ${content}` };
    }

    return JSON.parse(content);
  } catch (err) {
    return { error: err.message };
  }
}

/**
 * Gets data from the active selection
 */
function getSelectedData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();
  const data = range.getValues();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  // Find which column contains URLs (if any)
  let urlColumn = -1;
  headers.forEach((header, index) => {
    if (header.toString().toLowerCase().includes("url")) {
      urlColumn = index;
    }
  });

  // If we found a URL column and the selected cell is in that column
  if (
    urlColumn >= 0 &&
    range.getColumn() <= urlColumn + 1 &&
    range.getColumn() + range.getWidth() > urlColumn + 1
  ) {
    const url = data[0][urlColumn - range.getColumn() + 1];

    // Find the row with this URL in the sheet
    const urlValues = sheet
      .getRange(1, urlColumn + 1, sheet.getLastRow(), 1)
      .getValues();
    let rowIndex = -1;
    for (let i = 0; i < urlValues.length; i++) {
      if (urlValues[i][0] === url) {
        rowIndex = i;
        break;
      }
    }

    if (rowIndex >= 0) {
      const rowData = sheet
        .getRange(rowIndex + 1, 1, 1, headers.length)
        .getValues()[0];
      const companyData = {};

      headers.forEach((header, index) => {
        if (header) {
          companyData[header.toString().toLowerCase()] = rowData[index];
        }
      });

      companyData.url = url;
      return companyData;
    }
  }

  return null;
}

/********************
 * CUSTOM FUNCTIONS *
 ********************/

/**
 * Prepares cell data for API.
 */
function prepareInput(input) {
  if (!input) return [];
  if (typeof input === "string") return [input.trim()];
  if (!Array.isArray(input)) return [String(input)];

  if (typeof input === "object" && "getValues" in input) {
    input = input.getValues();
  }

  const flat = [];
  for (const row of input) {
    if (Array.isArray(row)) {
      for (const item of row) {
        if (item != null && item !== "") flat.push(String(item).trim());
      }
    } else if (row != null && row !== "") {
      flat.push(String(row).trim());
    }
  }
  return flat;
}

/**
 * Main extraction function for Google Sheets.
 * @param {Range} urlRange - Range of URLs.
 * @param {Range} fieldRange - Range of field headers.
 * @return {Array} - 2D array of results.
 * @customfunction
 */
function EXTRACT_DATA(urlRange, fieldRange) {
  const start = new Date();

  try {
    const urls = prepareInput(urlRange).filter((url) => url.startsWith("http"));
    const fields = prepareInput(fieldRange).map((f) => f.trim());

    if (!urls.length) return [["Error: No valid URLs"]];
    if (!fields.length) return [["Error: No valid fields"]];

    const results = [];
    for (let i = 0; i < urls.length; i += BATCH_SIZE) {
      const batch = urls.slice(i, i + BATCH_SIZE);
      const payload = JSON.stringify({ urls: batch, fields });

      const options = {
        method: "post",
        contentType: "application/json",
        payload: payload,
        muteHttpExceptions: true,
      };

      const response = UrlFetchApp.fetch(`${API_URL}/extract`, options);
      const code = response.getResponseCode();
      const content = response.getContentText();

      if (code !== 200) {
        results.push([`API Error (${code}): ${content}`]);
        continue;
      }

      const parsed = JSON.parse(content).data;

      for (const res of parsed) {
        const row = fields.map((f) => {
          const key = f.toLowerCase();
          return res[key] || res.error || "";
        });
        results.push(row);
      }
    }

    return results;
  } catch (err) {
    return [["Error: " + err.message]];
  }
}
/**
 * Health check - confirms server is live
 * @return {string}
 * @customfunction
 */
function API_HEALTH() {
  try {
    const res = UrlFetchApp.fetch(`${API_URL}/health`);
    const json = JSON.parse(res.getContentText());
    return `Status: ${json.status}, Timestamp: ${new Date(
      json.timestamp * 1000
    ).toLocaleString()}`;
  } catch (e) {
    return "Error: " + e.message;
  }
}
