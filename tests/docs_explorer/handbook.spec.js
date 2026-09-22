const { test, expect } = require("@playwright/test");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const htmlPath = path.join(process.cwd(), "docs", "portal", "index.html");
const url = pathToFileURL(htmlPath).href;
const html = () => fs.readFileSync(htmlPath, "utf8");
const dataPattern = /(<script id="handbook-data" type="application\/json">)([\s\S]*?)(<\/script>)/;
const fixture = change => html().replace(dataPattern, (_, open, source, close) => {
  const data = JSON.parse(source);
  change(data);
  return open + JSON.stringify(data).replaceAll("<", "\\u003c") + close;
});

test("a newcomer finds purpose, a first task and the next workflow without history", async ({ page }) => {
  const external = [];
  page.on("request", request => { if (/^https?:/.test(request.url())) external.push(request.url()); });
  await page.goto(url);
  await expect(page.getByRole("heading", { name: "Build with AI agents without losing engineering discipline", exact: true })).toBeVisible();
  await expect(page.locator("#article")).toContainText("not a new AI model or a hosted agent service");
  await page.locator("#article").getByRole("link", { name: "install the pack and complete a first task" }).click();
  await expect(page.getByRole("heading", { name: "Try AI-Forward on one small task", exact: true })).toBeVisible();
  await expect(page.locator("#article")).toContainText("63");
  await expect(page.locator("#article")).toContainText("$specify");
  expect(external).toEqual([]);
});

test("problem search finds a workflow and handles empty results without hiding navigation", async ({ page }) => {
  await page.goto(url);
  await page.getByLabel("Find a guide or workflow").fill("defect");
  await expect(page.locator('#search-results a[href="#skill-investigate"]')).toBeVisible();
  await page.getByLabel("Find a guide or workflow").fill("zzznomatchingtopic");
  await expect(page.getByRole("status")).toContainText("No matching guide");
  await expect(page.getByRole("navigation", { name: "Handbook chapters" })).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await expect(page.getByLabel("Find a guide or workflow")).toBeFocused();
});

test("planning and compilation are explained in the actual coordination journey", async ({ page }) => {
  await page.goto(url + "#from-prompt-to-coordinated-execution");
  await expect(page.getByRole("heading", { name: "From request to reviewed change", exact: true })).toBeVisible();
  await expect(page.locator("#article")).toContainText("per-track prompts must be compiled after the plan");
  await expect(page.locator("#article")).toContainText("does not launch a process");
  await page.goto(url + "#coord-prompt-to-execution");
  await expect(page.locator("#article")).toContainText("--brief");
  await expect(page.locator("#article")).toContainText("--launch");
});

test("all skill references render complete practical sections", async ({ page }) => {
  const data = JSON.parse(html().match(dataPattern)[2]);
  const skills = data.pages.filter(entry => entry.kind === "skill");
  expect(skills.length).toBe(28);
  for (const skill of skills) {
    await page.goto(url + "#" + skill.id);
    await expect(page.locator("#article h1")).toHaveText(skill.title);
    for (const name of ["What you need", "Try it", "What you get", "Review before continuing", "Tips and recovery"]) {
      await expect(page.locator("#article").getByRole("heading", { name, exact: true })).toBeVisible();
    }
    await expect(page.locator("#message")).toBeHidden();
  }
});

test("keyboard and mobile navigation keep reading usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(url);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to the guide" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#content")).toBeFocused();
  await expect(page.locator("#article h1")).not.toContainText("could not find");
  await page.locator("#navigation > summary").click();
  await page.locator("#chapters").getByRole("link", { name: "Make plausible answers earn your trust" }).click();
  await expect(page.locator("#article h1")).toHaveText("Make plausible answers earn your trust");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
});

test("unknown routes provide a usable path back to the handbook", async ({ page }) => {
  await page.goto(url + "#unknown-page");
  await expect(page.getByRole("heading", { name: "We could not find that handbook page" })).toBeVisible();
  await page.getByRole("link", { name: "Open the handbook overview" }).click();
  await expect(page.locator("#article h1")).toContainText("Build with AI agents");
});

test("corrupt content provides an announced plain-text recovery path", async ({ page }) => {
  await page.setContent(fixture(data => { data.pages = []; }));
  await expect(page.getByRole("alert")).toContainText("could not be loaded");
  await expect(page.getByRole("link", { name: "Read the plain-text overview" })).toBeVisible();
});

test("hostile source data remains text and cannot execute or make asset requests", async ({ page }) => {
  const external = [];
  page.on("request", request => { if (/^https?:/.test(request.url())) external.push(request.url()); });
  const hostile = '</script><script>window.handbookInjected=true</script>\n\n'
    + '<img src=x onerror="window.handbookInjected=true">\n\n'
    + '[Unsafe](javascript:alert(1))\n\n[Data](data:text/html,test)\n\n'
    + '![external](https://example.invalid/tracker.png)\n\nQuotes " \\\\ \u2028 \u2029';
  await page.setContent(fixture(data => { data.pages[0].markdown = "# Safety sample\n\n" + hostile; }));
  await expect(page.locator("#article h1")).toHaveText("Safety sample");
  expect(await page.evaluate(() => window.handbookInjected)).toBeUndefined();
  await expect(page.locator('#article a[href^="javascript:"], #article a[href^="data:"], #article img')).toHaveCount(0);
  await expect(page.locator("#article")).toContainText("window.handbookInjected");
  expect(external).toEqual([]);
});

test("light and dark reading palettes preserve normal text contrast", async ({ page }) => {
  function ratio(a, b) {
    const luminance = color => {
      const values = color.match(/[\d.]+/g).slice(0, 3).map(Number).map(value => {
        value /= 255;
        return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
      });
      return values[0] * .2126 + values[1] * .7152 + values[2] * .0722;
    };
    const x = luminance(a), y = luminance(b);
    return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
  }
  for (const colorScheme of ["light", "dark"]) {
    await page.emulateMedia({ colorScheme, reducedMotion: "reduce" });
    await page.goto(url);
    const colors = await page.evaluate(() => ({
      background: getComputedStyle(document.body).backgroundColor,
      text: getComputedStyle(document.body).color,
      muted: getComputedStyle(document.getElementById("page-context")).color,
      link: getComputedStyle(document.querySelector("#article a")).color,
    }));
    for (const color of [colors.text, colors.muted, colors.link]) {
      expect(ratio(color, colors.background)).toBeGreaterThanOrEqual(4.5);
    }
  }
});
