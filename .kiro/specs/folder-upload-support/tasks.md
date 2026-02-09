# Implementation Plan: Folder Upload Support

## Overview

Propagate a `folder_prefix` string through the entire PDF remediation pipeline. The change touches 8 existing files (Python, Java, JavaScript) and creates 1 new documentation file. Each component's path construction logic is updated to prepend the folder prefix, with empty string preserving backward compatibility.

## Tasks

- [x] 1. Update pdf-splitter-lambda to extract folder prefix and propagate it
  - [x] 1.1 Modify `lambda/pdf-splitter-lambda/main.py` to extract `folder_prefix` from the S3 key
    - In `split_pdf_into_pages`, change `file_basename` extraction to handle nested paths: use `pdf_file_key[len("pdf/"):]` then split off filename
    - Extract `folder_prefix` as the path between `pdf/` and the filename (empty string if flat)
    - Update chunk S3 key to `temp/{folder_prefix}{file_basename}/{file_basename}_chunk_N.pdf`
    - Include `folder_prefix` in each chunk dict
    - In `lambda_handler`, extract `folder_prefix` and include it at the top level of the Step Functions input: `{"chunks": [...], "s3_bucket": ..., "folder_prefix": ...}`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x]* 1.2 Write property tests for folder prefix extraction and chunk path construction
    - Set up `pytest` and `hypothesis` in `lambda/pdf-splitter-lambda/`
    - Create `lambda/pdf-splitter-lambda/test_folder_prefix.py`
    - **Property 1: Folder prefix extraction and chunk path construction**
    - **Validates: Requirements 1.1, 1.2, 1.4, 7.1, 7.2**

- [x] 2. Update Adobe Autotag ECS container for folder-aware paths
  - [x] 2.1 Modify `adobe-autotag-container/adobe_autotag_processor.py` to use `FOLDER_PREFIX` env var
    - Read `FOLDER_PREFIX` from environment (default to empty string)
    - Replace hardcoded `s3_file_key.split('/')[1]` and `s3_file_key.split('/')[2]` with folder-prefix-aware extraction
    - Update `download_file_from_s3` calls to use `temp/{folder_prefix}{file_base_name}/{file_key}`
    - Update `save_to_s3` to use `temp/{folder_prefix}{file_basename}/output_autotag/COMPLIANT_{file_key}`
    - Update all other S3 paths in `main()` and helper functions that reference `temp/{file_base_name}/...`
    - _Requirements: 2.2, 2.4_
  - [x]* 2.2 Write property tests for Adobe Autotag path construction
    - Create `adobe-autotag-container/test_folder_prefix.py`
    - **Property 2: Adobe Autotag path construction**
    - **Validates: Requirements 2.2, 2.4**

- [x] 3. Update Alt Text Generator ECS container for folder-aware paths
  - [x] 3.1 Modify `alt-text-generator-container/alt_text_generator.js` to use `FOLDER_PREFIX` env var
    - Read `FOLDER_PREFIX` from environment (default to empty string)
    - Replace hardcoded `S3_FILE_KEY.split("/")[1]` with folder-prefix-aware extraction
    - Update all S3 path constructions in `startProcess()` and `modifyPDF()` to use `temp/${folderPrefix}${filebasename}/...`
    - _Requirements: 2.3, 2.5_
  - [x]* 3.2 Write unit tests for Alt Text Generator path construction
    - Create `alt-text-generator-container/test_folder_prefix.js`
    - Test with empty prefix, single folder, nested folders
    - **Property 3: Alt Text Generator path construction**
    - **Validates: Requirements 2.3, 2.5**

- [x] 4. Update PDF Merger Lambda for folder-aware paths
  - [x] 4.1 Modify `lambda/pdf-merger-lambda/PDFMergerLambda/src/main/java/com/example/App.java` to accept and use `folderPrefix`
    - Extract `folderPrefix` from the input map (default to empty string)
    - Update `outputKey` construction to `temp/{folderPrefix}{baseFileName}/merged_{baseFileName}`
    - Update the return string to include the folder-aware merged file key
    - _Requirements: 3.1, 3.2, 3.3_
  - [x]* 4.2 Write unit tests for PDF Merger path construction
    - Create test class or add parameterized tests for path construction with various folder depths
    - **Property 4: PDF Merger output path construction**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 5. Checkpoint - Verify core pipeline components
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Update Title Generator Lambda for folder-aware result paths
  - [x] 6.1 Modify `lambda/title-generator-lambda/title_generator.py` to extract folder prefix from merged file key
    - Update `parse_payload` or `save_to_s3` to extract folder prefix from the merged file key
    - Update `save_path` to `result/{folder_prefix}COMPLIANT_{file_key}`
    - _Requirements: 4.1, 4.2_
  - [ ]* 6.2 Write property tests for Title Generator path construction
    - Create `lambda/title-generator-lambda/test_folder_prefix.py`
    - **Property 5: Title Generator result path construction**
    - **Validates: Requirements 4.1, 4.2**

- [x] 7. Update Pre-Remediation Accessibility Checker for folder-aware paths
  - [x] 7.1 Modify `lambda/pre-remediation-accessibility-checker/main.py` to use folder prefix
    - Extract `folder_prefix` from the event payload (default to empty string)
    - Update `download_file_from_s3` to download from `pdf/{folder_prefix}{filename}`
    - Update `save_to_s3` to save report to `temp/{folder_prefix}{basename}/accessability-report/...`
    - _Requirements: 5.1, 5.2, 5.4_
  - [ ]* 7.2 Write property tests for Pre-Remediation Checker path construction
    - Create `lambda/pre-remediation-accessibility-checker/test_folder_prefix.py`
    - **Property 6: Pre-Remediation Checker path construction**
    - **Validates: Requirements 5.1, 5.2, 5.4**

- [x] 8. Update Post-Remediation Accessibility Checker for folder-aware paths
  - [x] 8.1 Modify `lambda/post-remediation-accessibility-checker/main.py` to extract folder prefix from save_path
    - Extract folder prefix from `save_path` (everything between `result/` and `COMPLIANT_`)
    - Update `save_to_s3` to save report to `temp/{folder_prefix}{basename}/accessability-report/...`
    - _Requirements: 5.3, 5.5_
  - [ ]* 8.2 Write property tests for Post-Remediation Checker path construction
    - Create `lambda/post-remediation-accessibility-checker/test_folder_prefix.py`
    - **Property 7: Post-Remediation Checker path construction**
    - **Validates: Requirements 5.3, 5.5**

- [x] 9. Update CDK Stack to pass folder prefix through Step Functions
  - [x] 9.1 Modify `app.py` to pass `FOLDER_PREFIX` env var to ECS tasks and `folderPrefix` to merger lambda
    - Add `FOLDER_PREFIX` environment variable to `adobe_autotag_task` container overrides, sourced from `$.folder_prefix`
    - Add `FOLDER_PREFIX` environment variable to `alt_text_generation_task` container overrides, sourced from the ECS task output chain (same pattern as existing env vars)
    - Update `pdf_merger_lambda_task` payload to include `"folderPrefix.$": "$.folder_prefix"`
    - The pre-remediation checker already receives the full state machine input via `payload=sfn.TaskInput.from_json_path_at("$")`, so `folder_prefix` flows through automatically
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Create FEATURE-CHANGES.md documentation
  - [x] 10.1 Create `FEATURE-CHANGES.md` at the project root
    - Document all files modified and the nature of each change
    - Document the folder prefix propagation approach
    - Include before/after path examples
    - _Requirements: 8.1_

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use pytest + hypothesis for Python, example-based tests for Java and JavaScript
- The CDK changes (task 9) should be done after all component changes to ensure consistency
