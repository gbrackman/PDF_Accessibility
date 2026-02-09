"""
Property-based tests for folder prefix extraction and chunk path construction.

Feature: folder-upload-support, Property 1: Folder prefix extraction and chunk path construction

**Validates: Requirements 1.1, 1.2, 1.4, 7.1, 7.2**

Uses pytest + hypothesis to verify that for any valid S3 key of the form
`pdf/{arbitrary_folders}/{filename}.pdf` (including zero folders), extracting
the folder prefix and file basename, then constructing the chunk path, produces
`temp/{folder_prefix}{basename}/{basename}_chunk_N.pdf` where `{folder_prefix}`
is the path between `pdf/` and the filename (with trailing slash if non-empty),
and `{basename}` is the filename without extension.
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Pure functions extracted from main.py for testability
# ---------------------------------------------------------------------------

def extract_folder_prefix(s3_key: str) -> str:
    """
    Extract the folder prefix from an S3 key that starts with 'pdf/'.

    For 'pdf/folder1/folder2/myfile.pdf' -> 'folder1/folder2/'
    For 'pdf/myfile.pdf' -> ''
    """
    relative_path = s3_key[len("pdf/"):]
    if '/' in relative_path:
        folder_prefix = relative_path.rsplit('/', 1)[0] + '/'
    else:
        folder_prefix = ""
    return folder_prefix


def extract_file_basename(s3_key: str) -> str:
    """
    Extract the file basename (without extension) from an S3 key that starts with 'pdf/'.

    For 'pdf/folder1/folder2/myfile.pdf' -> 'myfile'
    For 'pdf/myfile.pdf' -> 'myfile'
    """
    relative_path = s3_key[len("pdf/"):]
    file_basename = relative_path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    return file_basename


def construct_chunk_path(folder_prefix: str, file_basename: str, chunk_index: int) -> str:
    """
    Construct the S3 key for a chunk file.

    Returns: 'temp/{folder_prefix}{file_basename}/{file_basename}_chunk_{chunk_index}.pdf'
    """
    page_filename = f"{file_basename}_chunk_{chunk_index}.pdf"
    return f"temp/{folder_prefix}{file_basename}/{page_filename}"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Strategy for valid folder segment names: non-empty, no slashes, no dots at start,
# alphanumeric with hyphens and underscores (realistic S3 folder names)
folder_segment_st = st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9_\-]{0,19}", fullmatch=True)

# Strategy for valid PDF basenames: non-empty, no slashes, no dots (extension added separately)
pdf_basename_st = st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9_\- ]{0,29}", fullmatch=True)

# Strategy for folder structures: 0 to 5 levels deep
folder_path_st = st.lists(folder_segment_st, min_size=0, max_size=5).map(
    lambda parts: "/".join(parts) + "/" if parts else ""
)

# Strategy for chunk indices (1-based)
chunk_index_st = st.integers(min_value=1, max_value=1000)


def build_s3_key(folder_prefix: str, basename: str) -> str:
    """Helper to build a full S3 key from folder prefix and basename."""
    return f"pdf/{folder_prefix}{basename}.pdf"


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

class TestFolderPrefixExtraction:
    """
    Property 1: Folder prefix extraction and chunk path construction.

    **Validates: Requirements 1.1, 1.2, 1.4, 7.1, 7.2**
    """

    @given(folder_prefix=folder_path_st, basename=pdf_basename_st)
    @settings(max_examples=200)
    def test_folder_prefix_extraction_roundtrip(self, folder_prefix: str, basename: str):
        """
        For any valid S3 key pdf/{folders}/{filename}.pdf, extracting the folder
        prefix SHALL return the path between pdf/ and the filename, with a trailing
        slash if non-empty.

        **Validates: Requirements 1.1, 1.2**
        """
        s3_key = build_s3_key(folder_prefix, basename)
        extracted = extract_folder_prefix(s3_key)
        assert extracted == folder_prefix, (
            f"Expected folder_prefix '{folder_prefix}' but got '{extracted}' "
            f"for key '{s3_key}'"
        )

    @given(folder_prefix=folder_path_st, basename=pdf_basename_st)
    @settings(max_examples=200)
    def test_file_basename_extraction(self, folder_prefix: str, basename: str):
        """
        For any valid S3 key, extracting the file basename SHALL return the
        filename without extension.

        **Validates: Requirements 1.1, 1.2**
        """
        s3_key = build_s3_key(folder_prefix, basename)
        extracted = extract_file_basename(s3_key)
        assert extracted == basename, (
            f"Expected basename '{basename}' but got '{extracted}' "
            f"for key '{s3_key}'"
        )

    @given(
        folder_prefix=folder_path_st,
        basename=pdf_basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_chunk_path_construction(self, folder_prefix: str, basename: str, chunk_index: int):
        """
        For any valid folder prefix, basename, and chunk index, constructing the
        chunk path SHALL produce temp/{folder_prefix}{basename}/{basename}_chunk_N.pdf.

        **Validates: Requirements 1.4, 7.2**
        """
        chunk_path = construct_chunk_path(folder_prefix, basename, chunk_index)
        expected = f"temp/{folder_prefix}{basename}/{basename}_chunk_{chunk_index}.pdf"
        assert chunk_path == expected, (
            f"Expected '{expected}' but got '{chunk_path}'"
        )

    @given(
        folder_prefix=folder_path_st,
        basename=pdf_basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_end_to_end_extraction_and_construction(
        self, folder_prefix: str, basename: str, chunk_index: int
    ):
        """
        End-to-end property: for any valid S3 key, extracting the folder prefix
        and basename, then constructing the chunk path, SHALL produce the correct
        temp/{folder_prefix}{basename}/{basename}_chunk_N.pdf path.

        This is the full Property 1 from the design document.

        **Validates: Requirements 1.1, 1.2, 1.4, 7.1, 7.2**
        """
        s3_key = build_s3_key(folder_prefix, basename)

        # Extract
        extracted_prefix = extract_folder_prefix(s3_key)
        extracted_basename = extract_file_basename(s3_key)

        # Construct
        chunk_path = construct_chunk_path(extracted_prefix, extracted_basename, chunk_index)

        # Verify
        expected = f"temp/{folder_prefix}{basename}/{basename}_chunk_{chunk_index}.pdf"
        assert chunk_path == expected, (
            f"For S3 key '{s3_key}' with chunk_index={chunk_index}:\n"
            f"  Expected: '{expected}'\n"
            f"  Got:      '{chunk_path}'"
        )

    @given(basename=pdf_basename_st, chunk_index=chunk_index_st)
    @settings(max_examples=200)
    def test_backward_compatibility_no_folder(self, basename: str, chunk_index: int):
        """
        When a PDF is uploaded directly to pdf/{basename}.pdf (no folder),
        the folder prefix SHALL be empty and the chunk path SHALL be
        temp/{basename}/{basename}_chunk_N.pdf — identical to current behavior.

        **Validates: Requirements 7.1, 7.2**
        """
        s3_key = f"pdf/{basename}.pdf"

        extracted_prefix = extract_folder_prefix(s3_key)
        extracted_basename = extract_file_basename(s3_key)

        assert extracted_prefix == "", (
            f"Expected empty folder_prefix for flat key '{s3_key}', got '{extracted_prefix}'"
        )
        assert extracted_basename == basename, (
            f"Expected basename '{basename}', got '{extracted_basename}'"
        )

        chunk_path = construct_chunk_path(extracted_prefix, extracted_basename, chunk_index)
        expected = f"temp/{basename}/{basename}_chunk_{chunk_index}.pdf"
        assert chunk_path == expected, (
            f"Backward compatibility broken: expected '{expected}', got '{chunk_path}'"
        )

    @given(folder_prefix=folder_path_st, basename=pdf_basename_st)
    @settings(max_examples=200)
    def test_folder_prefix_trailing_slash_invariant(self, folder_prefix: str, basename: str):
        """
        The extracted folder prefix SHALL either be empty or end with a trailing slash.

        **Validates: Requirements 1.1, 1.2**
        """
        s3_key = build_s3_key(folder_prefix, basename)
        extracted = extract_folder_prefix(s3_key)
        assert extracted == "" or extracted.endswith("/"), (
            f"Folder prefix '{extracted}' is non-empty but doesn't end with '/'"
        )

    @given(folder_prefix=folder_path_st, basename=pdf_basename_st)
    @settings(max_examples=200)
    def test_chunk_path_starts_with_temp(self, folder_prefix: str, basename: str):
        """
        All constructed chunk paths SHALL start with 'temp/'.

        **Validates: Requirements 1.4**
        """
        chunk_path = construct_chunk_path(folder_prefix, basename, 1)
        assert chunk_path.startswith("temp/"), (
            f"Chunk path '{chunk_path}' does not start with 'temp/'"
        )

    @given(folder_prefix=folder_path_st, basename=pdf_basename_st)
    @settings(max_examples=200)
    def test_chunk_path_ends_with_pdf(self, folder_prefix: str, basename: str):
        """
        All constructed chunk paths SHALL end with '.pdf'.

        **Validates: Requirements 1.4**
        """
        chunk_path = construct_chunk_path(folder_prefix, basename, 1)
        assert chunk_path.endswith(".pdf"), (
            f"Chunk path '{chunk_path}' does not end with '.pdf'"
        )
