/*
 * 測試 middleware 自動登入流程：
 * 1) 直接 GET /HN/api/form-basic/<form_uid>/
 * 2) middleware 讀取 META 帳密登入後回 302 到同一路徑
 * 3) 帶著 session cookie 再次 GET，取得 JSON
 *
 * 使用方式（Node.js 18+）：
 * node src/hazard_notify/tests/test_form_basic_payload_api_middleware_login.js
 */

const BASE_URL = "https://cmservice.sinotech.com.tw";
const FORM_UID = "bf516018-426a-4fae-85d6-5a498d5bb75b";
const API_TOKEN = "90f86588-8656-43fa-b2ed-39655d3755bb";
const USERNAME = "360paltfom";
const PASSWORD = "testapi0211";

function getCookieHeaderFromSetCookie(setCookieRaw) {
  if (!setCookieRaw) return "";
  const cookieParts = setCookieRaw.split(/,(?=[^;]+=[^;]+)/g);
  const pairs = [];
  for (const part of cookieParts) {
    const first = part.split(";")[0].trim();
    if (first.includes("=")) pairs.push(first);
  }
  return pairs.join("; ");
}

async function main() {
  const apiUrl = `${BASE_URL}/HN/api/form-basic/${FORM_UID}/`;

  try {
    // 第一次：觸發 middleware 以 META 帳密登入，預期 302
    const first = await fetch(apiUrl, {
      method: "GET",
      redirect: "manual",
      headers: {
        Authorization: `Token ${API_TOKEN}`,
        Accept: "application/json",
        "X-Platform-Username": USERNAME,
        "X-Platform-Password": PASSWORD,
      },
    });

    const location = first.headers.get("location");
    const cookieHeader = getCookieHeaderFromSetCookie(first.headers.get("set-cookie"));

    console.log("First status:", first.status);
    console.log("First location:", location || "(none)");
    console.log("First set-cookie exists:", cookieHeader ? "yes" : "no");

    if (!location) {
      const bodyText = await first.text();
      console.log("First response (first 400 chars):");
      console.log(bodyText.slice(0, 400));
      return;
    }

    // 第二次：帶 session cookie 取資料，預期 JSON
    const second = await fetch(`${BASE_URL}${location}`, {
      method: "GET",
      redirect: "manual",
      headers: {
        Authorization: `Token ${API_TOKEN}`,
        Accept: "application/json",
        Cookie: cookieHeader,
      },
    });

    const contentType = second.headers.get("content-type") || "";
    console.log("Second status:", second.status);
    console.log("Second content-type:", contentType);

    if (contentType.includes("application/json")) {
      const data = await second.json();
      console.log("Second JSON:");
      console.log(JSON.stringify(data, null, 2));
    } else {
      const text = await second.text();
      console.log("Second response (first 400 chars):");
      console.log(text.slice(0, 400));
    }
  } catch (error) {
    console.error("Request failed:", error);
  }
}

main();
