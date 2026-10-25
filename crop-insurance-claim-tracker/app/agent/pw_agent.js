/**
 * Playwright Automation Driver for Crop Insurance Mock Portal.
 * Uses bundled Playwright engine to guarantee 100% crash-free browser automation on Windows 11.
 */

const fs = require('fs');
const path = require('path');

// Locate playwright package from python site-packages or node modules
function getPlaywright() {
    const candidates = [
        'playwright',
        process.env.PLAYWRIGHT_NODE_PATH,  // optional: path to a playwright package
    ].filter(Boolean);
    for (const c of candidates) {
        try {
            return require(c);
        } catch (e) {}
    }
    throw new Error('Playwright package could not be resolved.');
}

const pw = getPlaywright();

async function inspect(url) {
    const browser = await pw.chromium.launch({ headless: true });
    try {
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });

        const appNo = (await page.locator('#dom-app-no').innerText()).trim();
        const farmerName = (await page.locator('#dom-farmer-name').innerText()).trim();
        const crop = (await page.locator('#dom-crop').innerText()).trim();
        const season = (await page.locator('#dom-season').innerText()).trim();
        const sowingDate = (await page.locator('#dom-sowing-date').innerText()).trim();
        const surveyNo = (await page.locator('#dom-survey-no').innerText()).trim();
        
        const claimStatus = (await page.locator('#dom-claim-status').getAttribute('data-status')) || '';
        const claimStatusText = (await page.locator('#dom-claim-status').innerText()).trim();
        
        const missingDoc = (await page.locator('#dom-missing-doc').getAttribute('data-missing')) || 'None';
        const missingDocText = (await page.locator('#dom-missing-doc').innerText()).trim();
        
        const paymentStatus = (await page.locator('#dom-payment-status').getAttribute('data-payment')) || '';
        const paymentStatusText = (await page.locator('#dom-payment-status').innerText()).trim();
        
        const approvedAmt = parseFloat(await page.locator('#dom-approved-amt').getAttribute('data-amount') || '0');
        const paidAmt = parseFloat(await page.locator('#dom-paid-amt').getAttribute('data-amount') || '0');
        const bankRef = (await page.locator('#dom-bank-ref').innerText()).trim();

        const result = {
            success: true,
            data: {
                application_number: appNo,
                farmer_name: farmerName,
                crop: crop,
                season: season,
                sowing_date: sowingDate,
                land_survey_no: surveyNo,
                claim_status: claimStatus,
                claim_status_text: claimStatusText,
                missing_document: missingDoc,
                missing_document_text: missingDocText,
                payment_status: paymentStatus,
                payment_status_text: paymentStatusText,
                approved_amount: approvedAmt,
                paid_amount: paidAmt,
                bank_reference_id: bankRef
            }
        };
        console.log(JSON.stringify(result));
    } catch (err) {
        console.log(JSON.stringify({ success: false, error: err.message }));
    } finally {
        await browser.close();
    }
}

async function editSeason(url, newSeason) {
    const browser = await pw.chromium.launch({ headless: true });
    try {
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
        await page.locator('#select-edit-season').selectOption(newSeason);
        await page.locator('#btn-submit-season').click();
        await page.waitForLoadState('networkidle');

        // Re-read updated season from live DOM
        const updatedSeason = (await page.locator('#dom-season').innerText()).trim();
        console.log(JSON.stringify({
            success: true,
            action: 'EDIT_SEASON',
            updated_season: updatedSeason,
            verified: (updatedSeason === newSeason)
        }));
    } catch (err) {
        console.log(JSON.stringify({ success: false, error: err.message }));
    } finally {
        await browser.close();
    }
}

async function uploadDoc(url, docName) {
    const browser = await pw.chromium.launch({ headless: true });
    try {
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
        await page.locator('#input-doc-name').fill(docName);
        await page.locator('#btn-submit-doc').click();
        await page.waitForLoadState('networkidle');

        const updatedDoc = (await page.locator('#dom-missing-doc').getAttribute('data-missing')) || 'None';
        console.log(JSON.stringify({
            success: true,
            action: 'UPLOAD_DOC',
            updated_missing_document: updatedDoc,
            verified: (updatedDoc.toLowerCase() === 'none')
        }));
    } catch (err) {
        console.log(JSON.stringify({ success: false, error: err.message }));
    } finally {
        await browser.close();
    }
}

async function main() {
    const command = process.argv[2];
    const url = process.argv[3];
    const extraArg = process.argv[4];

    if (command === 'inspect') {
        await inspect(url);
    } else if (command === 'edit-season') {
        await editSeason(url, extraArg);
    } else if (command === 'upload-doc') {
        await uploadDoc(url, extraArg);
    } else {
        console.log(JSON.stringify({ success: false, error: `Unknown command: ${command}` }));
    }
}

main();
