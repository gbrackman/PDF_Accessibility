# Feature: Folder Upload Support

## Summary

Added support for uploading folders of PDFs to the `pdf/` S3 prefix. The pipeline now extracts a **folder prefix** from the S3 key (the path between `pdf/` and the filename) and propagates it through every component. All intermediate and output files preserve the original folder structure. Uploading PDFs directly to `pdf/` (no folder) continues to work identically — the folder prefix is an empty string, so all paths collapse to the previous behavior.

## Folder Prefix Propagation Approach

1. The **pdf-splitter-lambda** extracts the folder prefix from the S3 event key and includes it in both the Step Functions input and each chunk object.
2. The **CDK stack** passes the folder prefix as a `FOLDER_PREFIX` environment variable to ECS tasks and as a `folderPrefix` field in the merger lambda payload.
3. Each downstream component reads the folder prefix and prepends it when constructing S3 paths.

## Path Examples

### Before (flat upload only)

| Stage | Path |
|---|---|
| Upload | `pdf/myfile.pdf` |
| Chunks | `temp/myfile/myfile_chunk_1.pdf` |
| Autotag output | `temp/myfile/output_autotag/COMPLIANT_myfile_chunk_1.pdf` |
| Alt text output | `temp/myfile/FINAL_myfile_chunk_1.pdf` |
| Merged | `temp/myfile/merged_myfile.pdf` |
| Final result | `result/COMPLIANT_myfile.pdf` |
| Accessibility reports | `temp/myfile/accessability-report/...` |

### After (nested folder upload)

| Stage | Path |
|---|---|
| Upload | `pdf/folder1/folder2/myfile.pdf` |
| Chunks | `temp/folder1/folder2/myfile/myfile_chunk_1.pdf` |
| Autotag output | `temp/folder1/folder2/myfile/output_autotag/COMPLIANT_myfile_chunk_1.pdf` |
| Alt text output | `temp/folder1/folder2/myfile/FINAL_myfile_chunk_1.pdf` |
| Merged | `temp/folder1/folder2/myfile/merged_myfile.pdf` |
| Final result | `result/folder1/folder2/COMPLIANT_myfile.pdf` |
| Accessibility reports | `temp/folder1/folder2/myfile/accessability-report/...` |

Flat uploads (`pdf/myfile.pdf`) produce an empty folder prefix, so paths are identical to the previous behavior.

## Files Modified

### `lambda/pdf-splitter-lambda/main.py`
- Extracts `folder_prefix` from the S3 key by removing the `pdf/` prefix and splitting off the filename.
- Constructs chunk S3 keys as `temp/{folder_prefix}{basename}/{basename}_chunk_N.pdf`.
- Includes `folder_prefix` in each chunk dict and at the top level of the Step Functions input.

### `adobe-autotag-container/adobe_autotag_processor.py`
- Reads `FOLDER_PREFIX` from environment variable (defaults to empty string).
- Strips `temp/` and the folder prefix from `S3_FILE_KEY` to extract `file_base_name` and `file_key`.
- All S3 download/upload paths use `temp/{folder_prefix}{file_base_name}/...`.
- `download_file_from_s3` and `save_to_s3` accept a `folder_prefix` parameter.

### `alt-text-generator-container/alt_text_generator.js`
- Reads `FOLDER_PREFIX` from environment variable (defaults to empty string).
- Extracts `filebasename` by stripping `temp/` + folder prefix from `S3_FILE_KEY`.
- All S3 path constructions in `startProcess()` and `modifyPDF()` use `temp/${folderPrefix}${filebasename}/...`.

### `lambda/pdf-merger-lambda/PDFMergerLambda/src/main/java/com/example/App.java`
- Reads `folderPrefix` from the input map (defaults to empty string).
- Added `constructOutputPath()` static method that builds `temp/{folderPrefix}{baseFileName}/merged_{baseFileName}`.
- Added `MergerPathResult` class to encapsulate path construction results.
- Return string includes the folder-aware merged file key.

### `lambda/title-generator-lambda/title_generator.py`
- Added `extract_folder_prefix()` function that parses the merged file key to extract the folder prefix.
- `save_to_s3` uses the extracted folder prefix to write to `result/{folder_prefix}COMPLIANT_{filename}`.

### `lambda/pre-remediation-accessibility-checker/main.py`
- Reads `folder_prefix` from the event payload (defaults to empty string).
- `download_file_from_s3` downloads from `pdf/{folder_prefix}{filename}`.
- `save_to_s3` writes the report to `temp/{folder_prefix}{basename}/accessability-report/...`.

### `lambda/post-remediation-accessibility-checker/main.py`
- Added `extract_folder_prefix()` function that extracts the folder prefix from the `save_path` (everything between `result/` and `COMPLIANT_`).
- `save_to_s3` accepts a `folder_prefix` parameter and writes the report to `temp/{folder_prefix}{basename}/accessability-report/...`.

### `app.py` (CDK Stack)
- Added `FOLDER_PREFIX` environment variable to the Adobe Autotag ECS task container overrides, sourced from `$.folder_prefix`.
- Added `FOLDER_PREFIX` environment variable to the Alt Text Generator ECS task container overrides, sourced from the preceding ECS task output chain.
- Updated the PDF Merger Lambda task payload to include `"folderPrefix.$": "$.folder_prefix"`.
- The pre-remediation checker receives `folder_prefix` automatically via `TaskInput.from_json_path_at("$")`.

## Test Files Created

| File | Framework | Coverage |
|---|---|---|
| `lambda/pdf-splitter-lambda/test_folder_prefix.py` | pytest + hypothesis | Folder prefix extraction, chunk path construction |
| `adobe-autotag-container/test_folder_prefix.py` | pytest + hypothesis | Adobe Autotag path construction |
| `alt-text-generator-container/test_folder_prefix.js` | Node.js (example-based) | Alt Text Generator path construction |
| `lambda/pdf-merger-lambda/.../PdfMergerPathConstructionTest.java` | JUnit (parameterized) | PDF Merger output path construction |
