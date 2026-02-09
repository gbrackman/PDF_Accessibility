# Requirements Document

## Introduction

Add support for uploading folders containing multiple PDFs to the S3 bucket for batch accessibility remediation processing. When a user uploads a folder of PDFs to the `pdf/` prefix, each PDF should be processed through the existing remediation pipeline with output files preserving the original folder structure in both `temp/` and `result/` prefixes. PDFs uploaded directly to `pdf/` without a folder should continue to work exactly as they do today.

## Glossary

- **Pipeline**: The PDF accessibility remediation workflow consisting of the PDF Splitter Lambda, Step Functions state machine, Adobe Autotag ECS task, Alt Text Generator ECS task, PDF Merger Lambda, Title Generator Lambda, Pre-Remediation Checker, and Post-Remediation Checker.
- **Folder_Prefix**: The portion of the S3 key between the top-level prefix (`pdf/`, `temp/`, `result/`) and the filename. For example, in `pdf/folder1/folder2/myfile.pdf`, the Folder_Prefix is `folder1/folder2/`.
- **PDF_Splitter_Lambda**: The AWS Lambda function (`lambda/pdf-splitter-lambda/main.py`) that receives S3 upload events, splits PDFs into chunks, and starts Step Functions executions.
- **Adobe_Autotag_ECS**: The ECS Fargate task (`adobe-autotag-container/adobe_autotag_processor.py`) that auto-tags PDF chunks for accessibility using Adobe PDF Services.
- **Alt_Text_Generator_ECS**: The ECS Fargate task (`alt-text-generator-container/alt_text_generator.js`) that generates WCAG-compliant alt text for images in PDF chunks using AWS Bedrock.
- **PDF_Merger_Lambda**: The AWS Lambda function (`lambda/pdf-merger-lambda/.../App.java`) that merges processed PDF chunks back into a single PDF.
- **Title_Generator_Lambda**: The AWS Lambda function (`lambda/title-generator-lambda/title_generator.py`) that generates an accessible title for the merged PDF and saves it to the `result/` prefix.
- **Pre_Remediation_Checker**: The AWS Lambda function (`lambda/pre-remediation-accessibility-checker/main.py`) that runs an accessibility audit on the original PDF before remediation.
- **Post_Remediation_Checker**: The AWS Lambda function (`lambda/post-remediation-accessibility-checker/main.py`) that runs an accessibility audit on the remediated PDF after processing.
- **State_Machine**: The AWS Step Functions state machine defined in `app.py` that orchestrates the remediation pipeline.
- **CDK_Stack**: The AWS CDK infrastructure definition in `app.py` that provisions all AWS resources for the pipeline.

## Requirements

### Requirement 1: Extract and Propagate Folder Prefix

**User Story:** As a user, I want to upload PDFs inside folders to the `pdf/` prefix, so that the pipeline processes them while preserving the folder structure in output paths.

#### Acceptance Criteria

1. WHEN a PDF is uploaded to a nested path such as `pdf/folder1/folder2/myfile.pdf`, THE PDF_Splitter_Lambda SHALL extract the Folder_Prefix `folder1/folder2/` from the S3 key.
2. WHEN a PDF is uploaded directly to `pdf/myfile.pdf` with no folder, THE PDF_Splitter_Lambda SHALL extract an empty Folder_Prefix.
3. WHEN the PDF_Splitter_Lambda starts a Step Functions execution, THE PDF_Splitter_Lambda SHALL include the Folder_Prefix as a field in the state machine input alongside the existing `chunks` and `s3_bucket` fields.
4. WHEN the PDF_Splitter_Lambda uploads chunk files to S3, THE PDF_Splitter_Lambda SHALL write chunks to `temp/{folder_prefix}{file_basename}/{file_basename}_chunk_N.pdf`, where `{folder_prefix}` is the extracted Folder_Prefix.

### Requirement 2: Folder-Aware Chunk Processing in ECS Tasks

**User Story:** As a pipeline operator, I want the Adobe Autotag and Alt Text Generator ECS tasks to handle folder prefixes in S3 paths, so that intermediate artifacts are stored in the correct folder structure.

#### Acceptance Criteria

1. WHEN the State_Machine passes a chunk S3 key containing a Folder_Prefix to the Adobe_Autotag_ECS task, THE CDK_Stack SHALL pass the Folder_Prefix as an environment variable named `FOLDER_PREFIX` to the ECS container.
2. WHEN the Adobe_Autotag_ECS task processes a chunk, THE Adobe_Autotag_ECS task SHALL use the Folder_Prefix to construct download and upload paths under `temp/{folder_prefix}{file_base_name}/`.
3. WHEN the Alt_Text_Generator_ECS task processes a chunk, THE Alt_Text_Generator_ECS task SHALL use the Folder_Prefix to construct download and upload paths under `temp/{folder_prefix}{file_base_name}/`.
4. WHEN the Folder_Prefix is empty, THE Adobe_Autotag_ECS task SHALL produce paths identical to the current behavior (e.g., `temp/{file_base_name}/`).
5. WHEN the Folder_Prefix is empty, THE Alt_Text_Generator_ECS task SHALL produce paths identical to the current behavior (e.g., `temp/{file_base_name}/`).

### Requirement 3: Folder-Aware PDF Merging

**User Story:** As a pipeline operator, I want the PDF Merger Lambda to preserve folder structure in its output paths, so that merged PDFs are stored in the correct location.

#### Acceptance Criteria

1. WHEN the PDF_Merger_Lambda receives chunk keys containing a Folder_Prefix, THE PDF_Merger_Lambda SHALL write the merged PDF to `temp/{folder_prefix}{file_base_name}/merged_{file_base_name}.pdf`.
2. WHEN the PDF_Merger_Lambda returns its result string, THE PDF_Merger_Lambda SHALL include the Folder_Prefix in the merged file key so downstream lambdas can locate the file.
3. WHEN the Folder_Prefix is empty, THE PDF_Merger_Lambda SHALL produce output paths identical to the current behavior.

### Requirement 4: Folder-Aware Result Output

**User Story:** As a user, I want the final remediated PDF to be saved in a path that preserves the original folder structure, so that I can find my output files organized the same way as my input files.

#### Acceptance Criteria

1. WHEN the Title_Generator_Lambda saves the final remediated PDF, THE Title_Generator_Lambda SHALL write it to `result/{folder_prefix}COMPLIANT_{filename}`.
2. WHEN the Folder_Prefix is empty, THE Title_Generator_Lambda SHALL write to `result/COMPLIANT_{filename}`, identical to the current behavior.

### Requirement 5: Folder-Aware Accessibility Reports

**User Story:** As a pipeline operator, I want the pre-remediation and post-remediation accessibility checkers to use folder-aware paths, so that accessibility reports are stored alongside the correct intermediate artifacts.

#### Acceptance Criteria

1. WHEN the Pre_Remediation_Checker downloads the original PDF, THE Pre_Remediation_Checker SHALL use the full S3 key including the Folder_Prefix (e.g., `pdf/{folder_prefix}{filename}`).
2. WHEN the Pre_Remediation_Checker saves the accessibility report, THE Pre_Remediation_Checker SHALL write it to `temp/{folder_prefix}{file_base_name}/accessibility-report/{file_base_name}_accessibility_report_before_remidiation.json`.
3. WHEN the Post_Remediation_Checker saves the accessibility report, THE Post_Remediation_Checker SHALL write it to `temp/{folder_prefix}{file_base_name}/accessibility-report/{file_base_name}_accessibility_report_after_remidiation.json`.
4. WHEN the Folder_Prefix is empty, THE Pre_Remediation_Checker SHALL produce paths identical to the current behavior.
5. WHEN the Folder_Prefix is empty, THE Post_Remediation_Checker SHALL produce paths identical to the current behavior.

### Requirement 6: CDK Infrastructure Updates

**User Story:** As a developer, I want the Step Functions state machine to propagate the folder prefix to all pipeline components, so that each component can construct folder-aware paths.

#### Acceptance Criteria

1. WHEN the State_Machine passes data to the Adobe_Autotag_ECS task, THE CDK_Stack SHALL include a `FOLDER_PREFIX` environment variable sourced from the state machine input.
2. WHEN the State_Machine passes data to the Alt_Text_Generator_ECS task, THE CDK_Stack SHALL include a `FOLDER_PREFIX` environment variable sourced from the state machine input.
3. WHEN the State_Machine passes data to the Pre_Remediation_Checker, THE Pre_Remediation_Checker SHALL receive the Folder_Prefix through the state machine input payload.
4. WHEN the State_Machine passes data to the PDF_Merger_Lambda, THE PDF_Merger_Lambda SHALL receive the Folder_Prefix through the state machine input payload.

### Requirement 7: Backward Compatibility

**User Story:** As an existing user, I want PDFs uploaded directly to `pdf/` without a folder to continue working exactly as they do today, so that the new folder support does not break existing workflows.

#### Acceptance Criteria

1. WHEN a PDF is uploaded to `pdf/myfile.pdf`, THE Pipeline SHALL process it with an empty Folder_Prefix, producing output paths identical to the current behavior.
2. WHEN a PDF is uploaded to `pdf/myfile.pdf`, THE Pipeline SHALL write chunks to `temp/myfile/myfile_chunk_N.pdf`.
3. WHEN a PDF is uploaded to `pdf/myfile.pdf`, THE Pipeline SHALL write the final result to `result/COMPLIANT_myfile.pdf`.

### Requirement 8: Change Documentation

**User Story:** As a developer, I want all changes documented in a `FEATURE-CHANGES.md` file at the project root, so that the team can review what was modified and why.

#### Acceptance Criteria

1. THE Pipeline SHALL have a `FEATURE-CHANGES.md` file at the project root documenting all files modified, the nature of each change, and the folder prefix propagation approach.
