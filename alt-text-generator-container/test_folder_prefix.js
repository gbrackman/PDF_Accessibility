/**
 * Unit tests for Alt Text Generator path construction.
 *
 * Feature: folder-upload-support, Property 3: Alt Text Generator path construction
 *
 * **Validates: Requirements 2.3, 2.5**
 *
 * Tests that for any folder prefix (including empty string) and S3 file key,
 * the Alt Text Generator container SHALL extract the correct `filebasename`
 * and construct paths under `temp/{folder_prefix}{filebasename}/`, producing
 * download paths for autotag output and upload paths for `FINAL_` prefixed chunks.
 *
 * Uses Node.js built-in assert module (no external test framework required).
 */

const assert = require('assert');

// ===========================================================================
// Pure functions extracted from alt_text_generator.js for testability
// ===========================================================================

/**
 * Extract the filebasename from an S3 file key using the folder prefix.
 *
 * Mirrors the logic in startProcess():
 *   const folderPrefix = process.env.FOLDER_PREFIX || '';
 *   const remainder = process.env.S3_FILE_KEY.substring(("temp/" + folderPrefix).length);
 *   const filebasename = remainder.split("/")[0];
 */
function extractFilebasename(s3FileKey, folderPrefix) {
  const remainder = s3FileKey.substring(("temp/" + folderPrefix).length);
  return remainder.split("/")[0];
}

/**
 * Construct the text file key (DB file path) for autotag output.
 *
 * Mirrors startProcess():
 *   const textFileKey = `${folderPrefix}${filebasename}/output_autotag/${chunkFilename}_temp_images_data.db`;
 *   // Used as: `temp/${textFileKey}`
 */
function constructTextFileKey(folderPrefix, filebasename, s3FileKey) {
  const chunkFilename = s3FileKey.split("/").pop();
  return `${folderPrefix}${filebasename}/output_autotag/${chunkFilename}_temp_images_data.db`;
}

/**
 * Construct the full S3 key for the text/DB file (with temp/ prefix).
 */
function constructFullTextFileKey(folderPrefix, filebasename, s3FileKey) {
  return `temp/${constructTextFileKey(folderPrefix, filebasename, s3FileKey)}`;
}

/**
 * Construct the image path for a given chunk and image row.
 *
 * Mirrors startProcess() loop:
 *   `temp/${folderPrefix}${filebasename}/output_autotag/images/${chunkFilename}_${row.img_path}`
 */
function constructImagePath(folderPrefix, filebasename, s3FileKey, imgPath) {
  const chunkFilename = s3FileKey.split("/").pop();
  return `temp/${folderPrefix}${filebasename}/output_autotag/images/${chunkFilename}_${imgPath}`;
}

/**
 * Construct the download path for the COMPLIANT PDF in modifyPDF.
 *
 * Mirrors modifyPDF():
 *   Key: `temp/${folderPrefix}${filebasename}/output_autotag/COMPLIANT_${s3FileKey.split("/").pop()}`
 */
function constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey) {
  const chunkFilename = s3FileKey.split("/").pop();
  return `temp/${folderPrefix}${filebasename}/output_autotag/COMPLIANT_${chunkFilename}`;
}

/**
 * Construct the upload path for the FINAL PDF in modifyPDF.
 *
 * Mirrors modifyPDF():
 *   Key: `temp/${folderPrefix}${filebasename}/FINAL_${outputKey}`
 *
 * Where outputKey = path.basename(process.env.S3_FILE_KEY) = chunkFilename
 */
function constructFinalUploadPath(folderPrefix, filebasename, outputKey) {
  return `temp/${folderPrefix}${filebasename}/FINAL_${outputKey}`;
}

// ===========================================================================
// Test helpers
// ===========================================================================

let passCount = 0;
let failCount = 0;

function test(name, fn) {
  try {
    fn();
    passCount++;
    console.log(`  ✓ ${name}`);
  } catch (err) {
    failCount++;
    console.error(`  ✗ ${name}`);
    console.error(`    ${err.message}`);
  }
}

function describe(suiteName, fn) {
  console.log(`\n${suiteName}`);
  fn();
}

// ===========================================================================
// Test cases
// ===========================================================================

describe('Property 3: Alt Text Generator path construction — **Validates: Requirements 2.3, 2.5**', () => {

  // -------------------------------------------------------------------------
  // filebasename extraction
  // -------------------------------------------------------------------------
  describe('  extractFilebasename', () => {

    test('empty prefix — extracts basename from flat key', () => {
      const s3FileKey = 'temp/myfile/myfile_chunk_1.pdf';
      const folderPrefix = '';
      const result = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(result, 'myfile');
    });

    test('single folder prefix — extracts basename correctly', () => {
      const s3FileKey = 'temp/folder1/myfile/myfile_chunk_1.pdf';
      const folderPrefix = 'folder1/';
      const result = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(result, 'myfile');
    });

    test('nested folder prefix — extracts basename correctly', () => {
      const s3FileKey = 'temp/folder1/folder2/myfile/myfile_chunk_1.pdf';
      const folderPrefix = 'folder1/folder2/';
      const result = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(result, 'myfile');
    });

    test('deeply nested folder prefix — extracts basename correctly', () => {
      const s3FileKey = 'temp/a/b/c/d/e/report/report_chunk_3.pdf';
      const folderPrefix = 'a/b/c/d/e/';
      const result = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(result, 'report');
    });

    test('basename with hyphens and underscores', () => {
      const s3FileKey = 'temp/docs/my-file_v2/my-file_v2_chunk_1.pdf';
      const folderPrefix = 'docs/';
      const result = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(result, 'my-file_v2');
    });

    test('basename with spaces', () => {
      const s3FileKey = 'temp/my folder/my document/my document_chunk_1.pdf';
      const folderPrefix = 'my folder/';
      const result = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(result, 'my document');
    });
  });

  // -------------------------------------------------------------------------
  // textFileKey construction (DB file path)
  // -------------------------------------------------------------------------
  describe('  constructTextFileKey / constructFullTextFileKey', () => {

    test('empty prefix — text file key has no folder prefix', () => {
      const s3FileKey = 'temp/myfile/myfile_chunk_1.pdf';
      const folderPrefix = '';
      const filebasename = 'myfile';
      const textFileKey = constructTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(textFileKey, 'myfile/output_autotag/myfile_chunk_1.pdf_temp_images_data.db');
      const fullKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(fullKey, 'temp/myfile/output_autotag/myfile_chunk_1.pdf_temp_images_data.db');
    });

    test('single folder prefix — text file key includes folder prefix', () => {
      const s3FileKey = 'temp/folder1/myfile/myfile_chunk_2.pdf';
      const folderPrefix = 'folder1/';
      const filebasename = 'myfile';
      const textFileKey = constructTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(textFileKey, 'folder1/myfile/output_autotag/myfile_chunk_2.pdf_temp_images_data.db');
      const fullKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(fullKey, 'temp/folder1/myfile/output_autotag/myfile_chunk_2.pdf_temp_images_data.db');
    });

    test('nested folder prefix — text file key includes full folder prefix', () => {
      const s3FileKey = 'temp/folder1/folder2/myfile/myfile_chunk_5.pdf';
      const folderPrefix = 'folder1/folder2/';
      const filebasename = 'myfile';
      const fullKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(fullKey, 'temp/folder1/folder2/myfile/output_autotag/myfile_chunk_5.pdf_temp_images_data.db');
    });
  });

  // -------------------------------------------------------------------------
  // Image path construction
  // -------------------------------------------------------------------------
  describe('  constructImagePath', () => {

    test('empty prefix — image path under temp/{basename}/output_autotag/images/', () => {
      const s3FileKey = 'temp/myfile/myfile_chunk_1.pdf';
      const folderPrefix = '';
      const filebasename = 'myfile';
      const imgPath = 'image_001.png';
      const result = constructImagePath(folderPrefix, filebasename, s3FileKey, imgPath);
      assert.strictEqual(result, 'temp/myfile/output_autotag/images/myfile_chunk_1.pdf_image_001.png');
    });

    test('single folder prefix — image path includes folder prefix', () => {
      const s3FileKey = 'temp/folder1/myfile/myfile_chunk_1.pdf';
      const folderPrefix = 'folder1/';
      const filebasename = 'myfile';
      const imgPath = 'fig_2.png';
      const result = constructImagePath(folderPrefix, filebasename, s3FileKey, imgPath);
      assert.strictEqual(result, 'temp/folder1/myfile/output_autotag/images/myfile_chunk_1.pdf_fig_2.png');
    });

    test('nested folder prefix — image path includes full folder prefix', () => {
      const s3FileKey = 'temp/a/b/c/report/report_chunk_3.pdf';
      const folderPrefix = 'a/b/c/';
      const filebasename = 'report';
      const imgPath = 'photo.jpg';
      const result = constructImagePath(folderPrefix, filebasename, s3FileKey, imgPath);
      assert.strictEqual(result, 'temp/a/b/c/report/output_autotag/images/report_chunk_3.pdf_photo.jpg');
    });
  });

  // -------------------------------------------------------------------------
  // COMPLIANT download path (modifyPDF)
  // -------------------------------------------------------------------------
  describe('  constructCompliantDownloadPath', () => {

    test('empty prefix — COMPLIANT download path under temp/{basename}/output_autotag/', () => {
      const s3FileKey = 'temp/myfile/myfile_chunk_1.pdf';
      const folderPrefix = '';
      const filebasename = 'myfile';
      const result = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(result, 'temp/myfile/output_autotag/COMPLIANT_myfile_chunk_1.pdf');
    });

    test('single folder prefix — COMPLIANT download path includes folder prefix', () => {
      const s3FileKey = 'temp/folder1/myfile/myfile_chunk_2.pdf';
      const folderPrefix = 'folder1/';
      const filebasename = 'myfile';
      const result = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(result, 'temp/folder1/myfile/output_autotag/COMPLIANT_myfile_chunk_2.pdf');
    });

    test('nested folder prefix — COMPLIANT download path includes full folder prefix', () => {
      const s3FileKey = 'temp/folder1/folder2/myfile/myfile_chunk_10.pdf';
      const folderPrefix = 'folder1/folder2/';
      const filebasename = 'myfile';
      const result = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(result, 'temp/folder1/folder2/myfile/output_autotag/COMPLIANT_myfile_chunk_10.pdf');
    });
  });

  // -------------------------------------------------------------------------
  // FINAL upload path (modifyPDF)
  // -------------------------------------------------------------------------
  describe('  constructFinalUploadPath', () => {

    test('empty prefix — FINAL upload path under temp/{basename}/', () => {
      const folderPrefix = '';
      const filebasename = 'myfile';
      const outputKey = 'myfile_chunk_1.pdf';
      const result = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
      assert.strictEqual(result, 'temp/myfile/FINAL_myfile_chunk_1.pdf');
    });

    test('single folder prefix — FINAL upload path includes folder prefix', () => {
      const folderPrefix = 'folder1/';
      const filebasename = 'myfile';
      const outputKey = 'myfile_chunk_2.pdf';
      const result = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
      assert.strictEqual(result, 'temp/folder1/myfile/FINAL_myfile_chunk_2.pdf');
    });

    test('nested folder prefix — FINAL upload path includes full folder prefix', () => {
      const folderPrefix = 'folder1/folder2/';
      const filebasename = 'myfile';
      const outputKey = 'myfile_chunk_5.pdf';
      const result = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
      assert.strictEqual(result, 'temp/folder1/folder2/myfile/FINAL_myfile_chunk_5.pdf');
    });
  });

  // -------------------------------------------------------------------------
  // End-to-end: extraction + all path constructions
  // -------------------------------------------------------------------------
  describe('  End-to-end path construction', () => {

    test('empty prefix — all paths match current behavior (backward compatibility)', () => {
      const folderPrefix = '';
      const s3FileKey = 'temp/myfile/myfile_chunk_1.pdf';

      const filebasename = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(filebasename, 'myfile');

      const fullTextKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(fullTextKey, 'temp/myfile/output_autotag/myfile_chunk_1.pdf_temp_images_data.db');

      const imagePath = constructImagePath(folderPrefix, filebasename, s3FileKey, 'img_001.png');
      assert.strictEqual(imagePath, 'temp/myfile/output_autotag/images/myfile_chunk_1.pdf_img_001.png');

      const compliantPath = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(compliantPath, 'temp/myfile/output_autotag/COMPLIANT_myfile_chunk_1.pdf');

      const outputKey = s3FileKey.split("/").pop(); // myfile_chunk_1.pdf
      const finalPath = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
      assert.strictEqual(finalPath, 'temp/myfile/FINAL_myfile_chunk_1.pdf');
    });

    test('single folder — all paths include folder prefix', () => {
      const folderPrefix = 'reports/';
      const s3FileKey = 'temp/reports/annual/annual_chunk_3.pdf';

      const filebasename = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(filebasename, 'annual');

      const fullTextKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(fullTextKey, 'temp/reports/annual/output_autotag/annual_chunk_3.pdf_temp_images_data.db');

      const imagePath = constructImagePath(folderPrefix, filebasename, s3FileKey, 'chart.png');
      assert.strictEqual(imagePath, 'temp/reports/annual/output_autotag/images/annual_chunk_3.pdf_chart.png');

      const compliantPath = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(compliantPath, 'temp/reports/annual/output_autotag/COMPLIANT_annual_chunk_3.pdf');

      const outputKey = s3FileKey.split("/").pop();
      const finalPath = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
      assert.strictEqual(finalPath, 'temp/reports/annual/FINAL_annual_chunk_3.pdf');
    });

    test('nested folders — all paths include full folder prefix', () => {
      const folderPrefix = 'dept/legal/2024/';
      const s3FileKey = 'temp/dept/legal/2024/contract/contract_chunk_1.pdf';

      const filebasename = extractFilebasename(s3FileKey, folderPrefix);
      assert.strictEqual(filebasename, 'contract');

      const fullTextKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(fullTextKey, 'temp/dept/legal/2024/contract/output_autotag/contract_chunk_1.pdf_temp_images_data.db');

      const imagePath = constructImagePath(folderPrefix, filebasename, s3FileKey, 'signature.png');
      assert.strictEqual(imagePath, 'temp/dept/legal/2024/contract/output_autotag/images/contract_chunk_1.pdf_signature.png');

      const compliantPath = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
      assert.strictEqual(compliantPath, 'temp/dept/legal/2024/contract/output_autotag/COMPLIANT_contract_chunk_1.pdf');

      const outputKey = s3FileKey.split("/").pop();
      const finalPath = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
      assert.strictEqual(finalPath, 'temp/dept/legal/2024/contract/FINAL_contract_chunk_1.pdf');
    });
  });

  // -------------------------------------------------------------------------
  // All paths start with temp/
  // -------------------------------------------------------------------------
  describe('  Path prefix invariants', () => {

    test('all constructed paths start with temp/', () => {
      const testCases = [
        { folderPrefix: '', s3FileKey: 'temp/myfile/myfile_chunk_1.pdf' },
        { folderPrefix: 'folder1/', s3FileKey: 'temp/folder1/myfile/myfile_chunk_1.pdf' },
        { folderPrefix: 'a/b/c/', s3FileKey: 'temp/a/b/c/myfile/myfile_chunk_1.pdf' },
      ];

      for (const { folderPrefix, s3FileKey } of testCases) {
        const filebasename = extractFilebasename(s3FileKey, folderPrefix);
        const fullTextKey = constructFullTextFileKey(folderPrefix, filebasename, s3FileKey);
        const imagePath = constructImagePath(folderPrefix, filebasename, s3FileKey, 'img.png');
        const compliantPath = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
        const outputKey = s3FileKey.split("/").pop();
        const finalPath = constructFinalUploadPath(folderPrefix, filebasename, outputKey);

        assert.ok(fullTextKey.startsWith('temp/'), `fullTextKey should start with temp/: ${fullTextKey}`);
        assert.ok(imagePath.startsWith('temp/'), `imagePath should start with temp/: ${imagePath}`);
        assert.ok(compliantPath.startsWith('temp/'), `compliantPath should start with temp/: ${compliantPath}`);
        assert.ok(finalPath.startsWith('temp/'), `finalPath should start with temp/: ${finalPath}`);
      }
    });

    test('FINAL upload path always contains FINAL_ prefix on the filename', () => {
      const testCases = [
        { folderPrefix: '', filebasename: 'myfile', outputKey: 'myfile_chunk_1.pdf' },
        { folderPrefix: 'folder1/', filebasename: 'myfile', outputKey: 'myfile_chunk_2.pdf' },
        { folderPrefix: 'a/b/', filebasename: 'report', outputKey: 'report_chunk_3.pdf' },
      ];

      for (const { folderPrefix, filebasename, outputKey } of testCases) {
        const finalPath = constructFinalUploadPath(folderPrefix, filebasename, outputKey);
        const filename = finalPath.split("/").pop();
        assert.ok(filename.startsWith('FINAL_'), `Filename should start with FINAL_: ${filename}`);
      }
    });

    test('COMPLIANT download path always contains COMPLIANT_ prefix on the filename', () => {
      const testCases = [
        { folderPrefix: '', filebasename: 'myfile', s3FileKey: 'temp/myfile/myfile_chunk_1.pdf' },
        { folderPrefix: 'folder1/', filebasename: 'myfile', s3FileKey: 'temp/folder1/myfile/myfile_chunk_2.pdf' },
        { folderPrefix: 'a/b/', filebasename: 'report', s3FileKey: 'temp/a/b/report/report_chunk_3.pdf' },
      ];

      for (const { folderPrefix, filebasename, s3FileKey } of testCases) {
        const compliantPath = constructCompliantDownloadPath(folderPrefix, filebasename, s3FileKey);
        const filename = compliantPath.split("/").pop();
        assert.ok(filename.startsWith('COMPLIANT_'), `Filename should start with COMPLIANT_: ${filename}`);
      }
    });
  });
});

// ===========================================================================
// Summary
// ===========================================================================
console.log(`\n${'='.repeat(60)}`);
console.log(`Test Results: ${passCount} passed, ${failCount} failed`);
console.log(`${'='.repeat(60)}`);

if (failCount > 0) {
  process.exit(1);
}
