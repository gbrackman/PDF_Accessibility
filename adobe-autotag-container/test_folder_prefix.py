"""
Property-based tests for Adobe Autotag path construction.

Feature: folder-upload-support, Property 2: Adobe Autotag path construction

**Validates: Requirements 2.2, 2.4**

Uses pytest + hypothesis to verify that for any folder prefix (including empty
string) and S3 file key of the form `temp/{folder_prefix}{basename}/{chunk_filename}`,
the Adobe Autotag container SHALL extract the correct `file_base_name` and `file_key`,
and construct download paths as `temp/{folder_prefix}{file_base_name}/{file_key}` and
upload paths as `temp/{folder_prefix}{file_base_name}/output_autotag/COMPLIANT_{file_key}`.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Pure functions extracted from adobe_autotag_processor.py for testability
# ---------------------------------------------------------------------------

def extract_file_base_name_and_key(s3_file_key: str, folder_prefix: str) -> tuple:
    """
    Extract file_base_name and file_key from an S3 file key using the folder prefix.

    Mirrors the logic in adobe_autotag_processor.py main():
        remainder = s3_file_key[len("temp/") + len(folder_prefix):]
        parts = remainder.split('/')
        file_base_name = parts[0]
        file_key = parts[1]

    Args:
        s3_file_key: S3 key like 'temp/{folder_prefix}{basename}/{chunk_filename}'
        folder_prefix: The folder prefix (e.g., 'folder1/folder2/' or '')

    Returns:
        (file_base_name, file_key) tuple
    """
    remainder = s3_file_key[len("temp/") + len(folder_prefix):]
    parts = remainder.split('/')
    file_base_name = parts[0]
    file_key = parts[1]
    return file_base_name, file_key


def construct_download_path(folder_prefix: str, file_base_name: str, file_key: str) -> str:
    """
    Construct the S3 download path for a chunk file.

    Mirrors download_file_from_s3:
        s3.download_file(bucket_name, f"temp/{folder_prefix}{file_base_name}/{file_key}", local_path)

    Returns: 'temp/{folder_prefix}{file_base_name}/{file_key}'
    """
    return f"temp/{folder_prefix}{file_base_name}/{file_key}"


def construct_upload_path(folder_prefix: str, file_base_name: str, file_key: str) -> str:
    """
    Construct the S3 upload path for the autotagged PDF.

    Mirrors save_to_s3 called with folder_name="output_autotag":
        s3.upload_fileobj(data, bucket_name,
            f"temp/{folder_prefix}{file_basename}/{folder_name}/COMPLIANT_{file_key}")

    Returns: 'temp/{folder_prefix}{file_base_name}/output_autotag/COMPLIANT_{file_key}'
    """
    return f"temp/{folder_prefix}{file_base_name}/output_autotag/COMPLIANT_{file_key}"


def construct_s3_folder_autotag(folder_prefix: str, file_base_name: str) -> str:
    """
    Construct the S3 folder path for autotag output (images, DB, etc.).

    Mirrors main():
        s3_folder_autotag = f"temp/{folder_prefix}{file_base_name}/output_autotag"

    Returns: 'temp/{folder_prefix}{file_base_name}/output_autotag'
    """
    return f"temp/{folder_prefix}{file_base_name}/output_autotag"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Strategy for valid folder segment names: non-empty, alphanumeric with hyphens/underscores
folder_segment_st = st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9_\-]{0,19}", fullmatch=True)

# Strategy for folder structures: 0 to 5 levels deep
folder_prefix_st = st.lists(folder_segment_st, min_size=0, max_size=5).map(
    lambda parts: "/".join(parts) + "/" if parts else ""
)

# Strategy for valid basenames (file base names without extension)
basename_st = st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9_\- ]{0,29}", fullmatch=True)

# Strategy for chunk filenames (e.g., 'myfile_chunk_1.pdf')
chunk_index_st = st.integers(min_value=1, max_value=1000)


def build_chunk_filename(basename: str, chunk_index: int) -> str:
    """Helper to build a chunk filename from basename and index."""
    return f"{basename}_chunk_{chunk_index}.pdf"


def build_s3_file_key(folder_prefix: str, basename: str, chunk_filename: str) -> str:
    """Helper to build a full S3 file key for a chunk in temp/."""
    return f"temp/{folder_prefix}{basename}/{chunk_filename}"


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

class TestAdobeAutotagPathConstruction:
    """
    Property 2: Adobe Autotag path construction.

    **Validates: Requirements 2.2, 2.4**
    """

    @given(
        folder_prefix=folder_prefix_st,
        basename=basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_extraction_recovers_basename_and_chunk(
        self, folder_prefix: str, basename: str, chunk_index: int
    ):
        """
        For any folder prefix and S3 file key of the form
        temp/{folder_prefix}{basename}/{chunk_filename}, extracting file_base_name
        and file_key SHALL recover the original basename and chunk filename.

        **Validates: Requirements 2.2, 2.4**
        """
        chunk_filename = build_chunk_filename(basename, chunk_index)
        s3_file_key = build_s3_file_key(folder_prefix, basename, chunk_filename)

        file_base_name, file_key = extract_file_base_name_and_key(s3_file_key, folder_prefix)

        assert file_base_name == basename, (
            f"Expected file_base_name '{basename}' but got '{file_base_name}' "
            f"for key '{s3_file_key}' with folder_prefix '{folder_prefix}'"
        )
        assert file_key == chunk_filename, (
            f"Expected file_key '{chunk_filename}' but got '{file_key}' "
            f"for key '{s3_file_key}' with folder_prefix '{folder_prefix}'"
        )

    @given(
        folder_prefix=folder_prefix_st,
        basename=basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_download_path_construction(
        self, folder_prefix: str, basename: str, chunk_index: int
    ):
        """
        For any folder prefix, the download path SHALL be
        temp/{folder_prefix}{file_base_name}/{file_key}.

        **Validates: Requirements 2.2, 2.4**
        """
        chunk_filename = build_chunk_filename(basename, chunk_index)
        s3_file_key = build_s3_file_key(folder_prefix, basename, chunk_filename)

        file_base_name, file_key = extract_file_base_name_and_key(s3_file_key, folder_prefix)
        download_path = construct_download_path(folder_prefix, file_base_name, file_key)

        expected = f"temp/{folder_prefix}{basename}/{chunk_filename}"
        assert download_path == expected, (
            f"Expected download path '{expected}' but got '{download_path}'"
        )

    @given(
        folder_prefix=folder_prefix_st,
        basename=basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_upload_path_construction(
        self, folder_prefix: str, basename: str, chunk_index: int
    ):
        """
        For any folder prefix, the upload path SHALL be
        temp/{folder_prefix}{file_base_name}/output_autotag/COMPLIANT_{file_key}.

        **Validates: Requirements 2.2, 2.4**
        """
        chunk_filename = build_chunk_filename(basename, chunk_index)
        s3_file_key = build_s3_file_key(folder_prefix, basename, chunk_filename)

        file_base_name, file_key = extract_file_base_name_and_key(s3_file_key, folder_prefix)
        upload_path = construct_upload_path(folder_prefix, file_base_name, file_key)

        expected = f"temp/{folder_prefix}{basename}/output_autotag/COMPLIANT_{chunk_filename}"
        assert upload_path == expected, (
            f"Expected upload path '{expected}' but got '{upload_path}'"
        )

    @given(
        folder_prefix=folder_prefix_st,
        basename=basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_end_to_end_path_construction(
        self, folder_prefix: str, basename: str, chunk_index: int
    ):
        """
        End-to-end property: for any folder prefix (including empty string) and
        S3 file key of the form temp/{folder_prefix}{basename}/{chunk_filename},
        the Adobe Autotag container SHALL extract the correct file_base_name and
        file_key, and construct download paths as
        temp/{folder_prefix}{file_base_name}/{file_key} and upload paths as
        temp/{folder_prefix}{file_base_name}/output_autotag/COMPLIANT_{file_key}.

        This is the full Property 2 from the design document.

        **Validates: Requirements 2.2, 2.4**
        """
        chunk_filename = build_chunk_filename(basename, chunk_index)
        s3_file_key = build_s3_file_key(folder_prefix, basename, chunk_filename)

        # Extract (mirrors main() logic)
        file_base_name, file_key = extract_file_base_name_and_key(s3_file_key, folder_prefix)

        # Verify extraction
        assert file_base_name == basename
        assert file_key == chunk_filename

        # Construct and verify download path
        download_path = construct_download_path(folder_prefix, file_base_name, file_key)
        assert download_path == s3_file_key, (
            f"Download path '{download_path}' should reconstruct the original S3 key '{s3_file_key}'"
        )

        # Construct and verify upload path
        upload_path = construct_upload_path(folder_prefix, file_base_name, file_key)
        expected_upload = f"temp/{folder_prefix}{basename}/output_autotag/COMPLIANT_{chunk_filename}"
        assert upload_path == expected_upload

        # Construct and verify s3_folder_autotag
        folder_autotag = construct_s3_folder_autotag(folder_prefix, file_base_name)
        expected_folder = f"temp/{folder_prefix}{basename}/output_autotag"
        assert folder_autotag == expected_folder

    @given(basename=basename_st, chunk_index=chunk_index_st)
    @settings(max_examples=200)
    def test_backward_compatibility_empty_prefix(self, basename: str, chunk_index: int):
        """
        When the folder prefix is empty, all paths SHALL be identical to the
        current behavior (no folder prefix in paths).

        **Validates: Requirements 2.4**
        """
        folder_prefix = ""
        chunk_filename = build_chunk_filename(basename, chunk_index)
        s3_file_key = build_s3_file_key(folder_prefix, basename, chunk_filename)

        file_base_name, file_key = extract_file_base_name_and_key(s3_file_key, folder_prefix)

        # Download path should be temp/{basename}/{chunk} (no folder prefix)
        download_path = construct_download_path(folder_prefix, file_base_name, file_key)
        assert download_path == f"temp/{basename}/{chunk_filename}"

        # Upload path should be temp/{basename}/output_autotag/COMPLIANT_{chunk}
        upload_path = construct_upload_path(folder_prefix, file_base_name, file_key)
        assert upload_path == f"temp/{basename}/output_autotag/COMPLIANT_{chunk_filename}"

        # s3_folder_autotag should be temp/{basename}/output_autotag
        folder_autotag = construct_s3_folder_autotag(folder_prefix, file_base_name)
        assert folder_autotag == f"temp/{basename}/output_autotag"

    @given(
        folder_prefix=folder_prefix_st,
        basename=basename_st,
        chunk_index=chunk_index_st,
    )
    @settings(max_examples=200)
    def test_download_path_roundtrip(
        self, folder_prefix: str, basename: str, chunk_index: int
    ):
        """
        The download path constructed from extracted values SHALL equal the
        original S3 file key — demonstrating a roundtrip property.

        **Validates: Requirements 2.2, 2.4**
        """
        chunk_filename = build_chunk_filename(basename, chunk_index)
        s3_file_key = build_s3_file_key(folder_prefix, basename, chunk_filename)

        file_base_name, file_key = extract_file_base_name_and_key(s3_file_key, folder_prefix)
        reconstructed = construct_download_path(folder_prefix, file_base_name, file_key)

        assert reconstructed == s3_file_key, (
            f"Roundtrip failed: original '{s3_file_key}' != reconstructed '{reconstructed}'"
        )
