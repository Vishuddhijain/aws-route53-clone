import { expect, test } from "@playwright/test";

test("zone and record CRUD persists through refresh and logout/login", async ({ page }) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", error => pageErrors.push(error.stack || error.message));
  const domain = `demo-${Date.now()}.example.test`;
  await page.goto("/");
  await page.getByLabel("Email address").fill("intern@example.test");
  await page.getByLabel("Password").fill("route53-demo");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Amazon Route 53" })).toBeVisible();

  await page.locator(".sidebar .side-link").filter({ hasText: "Hosted zones" }).click();
  await page.getByRole("button", { name: "Create hosted zone" }).click();
  await page.getByLabel("Domain name *").fill(domain);
  await page.getByLabel("Comment").fill("E2E persistent zone");
  await page.getByRole("button", { name: "Create hosted zone" }).last().click();
  await expect(page.locator(".toast")).toHaveText("Hosted zone created");
  const zoneRow = page.getByRole("row").filter({ hasText: domain });
  await expect(zoneRow).toBeVisible();
  await expect(zoneRow).toContainText("Z");
  await expect(zoneRow).toContainText("Public hosted zone");
  await expect(zoneRow).not.toContainText("—");
  await zoneRow.getByTitle("Edit zone").click();
  await page.getByLabel("Comment").fill("E2E edited comment");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("row").filter({ hasText: "E2E edited comment" })).toBeVisible();
  await expect(page.getByRole("row").filter({ hasText: domain })).toContainText("E2E edited comment");
  await page.getByLabel("Search hosted zones").fill(domain);
  await expect(page.getByRole("row").filter({ hasText: domain })).toBeVisible();
  await page.getByLabel("Search hosted zones").fill("");
  const editedZoneRow = page.getByRole("row").filter({ hasText: domain });
  await editedZoneRow.getByTitle("Open zone").click();

  await expect(page.getByRole("heading", { name: domain })).toBeVisible();
  await expect(page.locator(".pill").filter({ hasText: /^NS$/ })).toBeVisible();
  await expect(page.locator(".pill").filter({ hasText: /^SOA$/ })).toBeVisible();
  await page.getByRole("button", { name: "Create record" }).click();
  await page.getByLabel("Record type *").selectOption("MX");
  await expect(page.getByLabel("Value *")).toHaveAttribute("placeholder", "10 mail.example.com.");
  await page.getByLabel("Record type *").selectOption("SRV");
  await expect(page.getByLabel("Value *")).toHaveAttribute("placeholder", "10 5 5060 sip.example.com.");
  await page.getByLabel("Record type *").selectOption("A");
  await page.getByLabel("Record name *").fill(`www.${domain}`);
  await page.getByLabel("Record type *").selectOption("A");
  await page.getByLabel("Value *").fill("192.0.2.30");
  await page.getByRole("button", { name: "Create record" }).last().click();
  await expect(page.locator(".toast")).toHaveText("DNS record created");
  const recordRow = page.getByRole("row").filter({ hasText: `www.${domain}` });
  await expect(recordRow).toContainText("192.0.2.30");

  await page.getByLabel("Search records").fill("192.0.2.30");
  await expect(recordRow).toBeVisible();
  await page.getByLabel("Filter by record type").selectOption("A");
  await page.reload();
  await expect(page.getByRole("row").filter({ hasText: `www.${domain}` })).toContainText("192.0.2.30");
  await expect(page.getByRole("button", { name: /Export JSON/ })).toBeVisible();
  const [bindDownload] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Export BIND" }).click()]);
  expect(bindDownload.suggestedFilename()).toBe(`${domain}.zone`);

  const aRow = page.getByRole("row").filter({ hasText: `www.${domain}` });
  await aRow.getByTitle("Edit record").click();
  await page.getByLabel("Value *").fill("192.0.2.31");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("row").filter({ hasText: `www.${domain}` })).toContainText("192.0.2.31");

  await page.getByTitle("Sign out").click();
  await page.getByLabel("Email address").fill("intern@example.test");
  await page.getByLabel("Password").fill("route53-demo");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.locator(".sidebar .side-link").filter({ hasText: "Hosted zones" }).click();
  await expect(page.getByRole("row").filter({ hasText: domain })).toBeVisible();
  await page.getByRole("row").filter({ hasText: domain }).getByTitle("Open zone").click();
  await expect(page.getByRole("row").filter({ hasText: `www.${domain}` })).toContainText("192.0.2.31");

  await page.getByRole("row").filter({ hasText: `www.${domain}` }).getByTitle("Delete record").click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("row").filter({ hasText: `www.${domain}` })).toHaveCount(0);

  await page.locator(".sidebar .side-link").filter({ hasText: "Hosted zones" }).click();
  const finalZoneRow = page.getByRole("row").filter({ hasText: domain });
  await finalZoneRow.getByTitle("Delete zone").click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("row").filter({ hasText: domain })).toHaveCount(0);

  for (const section of ["Traffic policies", "Health checks", "Resolver", "Profiles"]) {
    await page.locator(".sidebar .side-link").filter({ hasText: section }).click();
    await expect(page.getByRole("heading", { name: `${section} is coming soon` })).toBeVisible();
  }
  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
});
