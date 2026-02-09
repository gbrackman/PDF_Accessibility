package com.example;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.Parameterized;
import org.junit.runners.Parameterized.Parameters;

import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import static org.junit.Assert.*;

/**
 * Parameterized unit tests for PDF Merger output path construction.
 *
 * Feature: folder-upload-support, Property 4: PDF Merger output path construction
 * **Validates: Requirements 3.1, 3.2, 3.3**
 *
 * Property 4: For any folder prefix (including empty string) and list of chunk keys,
 * the PDF Merger Lambda SHALL construct the output key as
 * temp/{folder_prefix}{baseFileName}/merged_{baseFileName}
 * and include this path in its return string.
 */
@RunWith(Parameterized.class)
public class PdfMergerPathConstructionTest {

    private final String testName;
    private final String folderPrefix;
    private final List<String> chunkKeys;
    private final String expectedOutputKey;
    private final String expectedBaseFileName;

    public PdfMergerPathConstructionTest(String testName, String folderPrefix,
                                          List<String> chunkKeys, String expectedOutputKey,
                                          String expectedBaseFileName) {
        this.testName = testName;
        this.folderPrefix = folderPrefix;
        this.chunkKeys = chunkKeys;
        this.expectedOutputKey = expectedOutputKey;
        this.expectedBaseFileName = expectedBaseFileName;
    }

    @Parameters(name = "{0}")
    public static Collection<Object[]> data() {
        return Arrays.asList(new Object[][] {
            // Requirement 3.3: Empty prefix (backward compatibility)
            {
                "Empty prefix - single chunk",
                "",
                Collections.singletonList("temp/myfile/myfile_chunk_1.pdf"),
                "temp/myfile/merged_myfile.pdf",
                "myfile.pdf"
            },
            // Requirement 3.3: Empty prefix with multiple chunks
            {
                "Empty prefix - multiple chunks",
                "",
                Arrays.asList("temp/report/report_chunk_1.pdf", "temp/report/report_chunk_2.pdf"),
                "temp/report/merged_report.pdf",
                "report.pdf"
            },
            // Requirement 3.1: Single-level folder prefix
            {
                "Single folder prefix",
                "folder1/",
                Collections.singletonList("temp/folder1/myfile/myfile_chunk_1.pdf"),
                "temp/folder1/myfile/merged_myfile.pdf",
                "myfile.pdf"
            },
            // Requirement 3.1: Two-level nested folder prefix
            {
                "Two-level nested folder prefix",
                "folder1/folder2/",
                Collections.singletonList("temp/folder1/folder2/myfile/myfile_chunk_1.pdf"),
                "temp/folder1/folder2/myfile/merged_myfile.pdf",
                "myfile.pdf"
            },
            // Requirement 3.1: Deeply nested folder prefix
            {
                "Deeply nested folder prefix (3 levels)",
                "a/b/c/",
                Collections.singletonList("temp/a/b/c/document/document_chunk_1.pdf"),
                "temp/a/b/c/document/merged_document.pdf",
                "document.pdf"
            },
            // Requirement 3.2: Verify folder prefix appears in return string
            {
                "Folder prefix with hyphenated filename",
                "projects/2024/",
                Collections.singletonList("temp/projects/2024/my-report/my-report_chunk_1.pdf"),
                "temp/projects/2024/my-report/merged_my-report.pdf",
                "my-report.pdf"
            },
            // Null folder prefix treated as empty (backward compatibility)
            {
                "Null folder prefix treated as empty",
                null,
                Collections.singletonList("temp/myfile/myfile_chunk_1.pdf"),
                "temp/myfile/merged_myfile.pdf",
                "myfile.pdf"
            },
            // Filename with underscores (not chunk pattern)
            {
                "Filename with underscores",
                "docs/",
                Collections.singletonList("temp/docs/my_special_file/my_special_file_chunk_1.pdf"),
                "temp/docs/my_special_file/merged_my_special_file.pdf",
                "my_special_file.pdf"
            }
        });
    }

    /**
     * Test that constructOutputPath produces the correct output key.
     * Validates Requirement 3.1: merged PDF written to temp/{folder_prefix}{file_base_name}/merged_{file_base_name}.pdf
     */
    @Test
    public void testOutputKeyConstruction() {
        MergerPathResult result = App.constructOutputPath(folderPrefix, chunkKeys);
        assertEquals("Output key mismatch for: " + testName, expectedOutputKey, result.outputKey);
    }

    /**
     * Test that constructOutputPath extracts the correct base file name.
     * Validates Requirement 3.1: correct base file name extraction from chunk keys
     */
    @Test
    public void testBaseFileNameExtraction() {
        MergerPathResult result = App.constructOutputPath(folderPrefix, chunkKeys);
        assertEquals("Base file name mismatch for: " + testName, expectedBaseFileName, result.baseFileName);
    }

    /**
     * Test that the return string includes the merged file key (output key).
     * Validates Requirement 3.2: return string includes folder prefix in merged file key
     */
    @Test
    public void testReturnStringContainsOutputKey() {
        MergerPathResult result = App.constructOutputPath(folderPrefix, chunkKeys);
        String returnString = App.constructReturnString("test-bucket", result.outputKey, result.baseFileName);

        assertTrue("Return string should contain the output key for: " + testName,
                   returnString.contains(result.outputKey));
        assertTrue("Return string should contain 'Merged File Key:' for: " + testName,
                   returnString.contains("Merged File Key: " + result.outputKey));
        assertTrue("Return string should contain 'Merged File Name:' for: " + testName,
                   returnString.contains("Merged File Name: " + result.baseFileName));
        assertTrue("Return string should contain bucket name for: " + testName,
                   returnString.contains("Bucket: test-bucket"));
    }
}
