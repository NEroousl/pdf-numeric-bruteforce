#!/usr/bin/env python3
"""
pdf_crack_63.py

Brute-force a 4-digit numeric PDF password where the last two digits are known to be "63".
Tries passwords "0000".."9999" but only iterates the first two digits (00-99) and appends "63",
so the tested passwords are "0063","0163",...,"9963".

Requirements:
 - You must be the lawful owner of the PDF or have explicit authorization.
 - This script attempts to open the PDF and will stop on success.
 - Overwrites output.txt at start. Appends one line per attempt with format:
     attempt_number,password,RESULT,elapsed_seconds
   where RESULT is PASS or FAIL.

Usage:
    python pdf_crack_63.py /path/to/encrypted.pdf

The script will try pikepdf first (recommended). If pikepdf is not installed,
it will fall back to PyPDF2 (if available).
"""

import sys
import time
from pathlib import Path

# Try imports in order of preference
try:
    import pikepdf
    _BACKEND = 'pikepdf'
except Exception:
    try:
        from PyPDF2 import PdfReader, PdfWriter
        _BACKEND = 'pypdf2'
    except Exception:
        _BACKEND = None

OUTPUT_FILE = "output.txt"

def try_open_with_pikepdf(pdf_path: str, password: str) -> bool:
    """Return True if pikepdf can open the file with the password."""
    try:
        # pikepdf raises pikepdf._qpdf.PasswordError for wrong password
        with pikepdf.open(pdf_path, password=password):
            return True
    except Exception as e:
        # Wrong password or other error
        return False

def try_open_with_pypdf2(pdf_path: str, password: str) -> bool:
    """Return True if PyPDF2 can open the file with the password."""
    try:
        reader = PdfReader(pdf_path)
        # reader.decrypt returns 0/1/2 depending on success in some versions; other versions raise
        result = False
        try:
            # Newer PyPDF2 variants use .decrypt(password) and return int or raise
            dec = reader.decrypt(password)
            # decrypt may return 0 for fail, 1 or 2 for success (owner/user)
            if isinstance(dec, int):
                result = (dec != 0)
            else:
                # some versions return None but still set up to read pages if success; check page access
                try:
                    _ = reader.pages[0]
                    result = True
                except Exception:
                    result = False
        except Exception:
            # fallback: try to read a page directly (some versions need this to raise on wrong password)
            try:
                _ = reader.pages[0]
                result = True
            except Exception:
                result = False
        return result
    except Exception:
        return False

def attempt_open(pdf_path: str, password: str) -> bool:
    """Attempt to open PDF using available backend. Returns True on success."""
    if _BACKEND == 'pikepdf':
        return try_open_with_pikepdf(pdf_path, password)
    elif _BACKEND == 'pypdf2':
        return try_open_with_pypdf2(pdf_path, password)
    else:
        raise RuntimeError("No PDF library available. Install 'pikepdf' or 'PyPDF2' (pypdf).")

def main():
    if len(sys.argv) != 2:
        print("Usage: python pdf_crack_63.py /path/to/encrypted.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    pdf_file = Path(pdf_path)
    if not pdf_file.exists() or not pdf_file.is_file():
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    if _BACKEND is None:
        print("Error: no PDF libraries found. Install 'pikepdf' (recommended) or 'PyPDF2'.")
        print("Install pikepdf: pip install pikepdf")
        sys.exit(1)
    else:
        print(f"Using backend: {_BACKEND}")

    # Overwrite the output file at start
    start_time = time.time()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Brute-force started at {time.ctime(start_time)}\n")
        f.write(f"PDF: {pdf_path}\n")
        f.write("Attempt,Password,Result,ElapsedSeconds\n")

    attempt = 0
    found = False
    found_password = None

    # We know last two digits are "63". First two digits iterate 00..99
    for d1 in range(100):
        attempt += 1
        first_two = f"{d1:02d}"
        candidate = first_two + "63"
        elapsed = time.time() - start_time

        try:
            ok = attempt_open(pdf_path, candidate)
        except Exception as e:
            ok = False  # treat as failure for logging; don't crash

        result_str = "PASS" if ok else "FAIL"

        # Append to output file
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{attempt},{candidate},{result_str},{elapsed:.3f}\n")

        # Print brief progress to console
        print(f"[{attempt:03d}] Trying {candidate} -> {result_str}")

        if ok:
            found = True
            found_password = candidate
            break

    total_elapsed = time.time() - start_time
    # Final summary written to output file (overwrites nothing else)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        if found:
            f.write(f"\nSUCCESS: Password found: {found_password}\n")
            f.write(f"Total attempts: {attempt}. Time elapsed: {total_elapsed:.3f}s\n")
        else:
            f.write(f"\nFAILED: Password not found in search space (00-99 for first two digits)\n")
            f.write(f"Total attempts: {attempt}. Time elapsed: {total_elapsed:.3f}s\n")

    if found:
        print("\n=== PASSWORD FOUND ===")
        print(f"Password: {found_password}")
        print(f"Attempts: {attempt}. Total time: {total_elapsed:.3f}s")
    else:
        print("\nPassword not found in the tested search space.")
        print(f"Attempts: {attempt}. Total time: {total_elapsed:.3f}s")

if __name__ == "__main__":
    main()
