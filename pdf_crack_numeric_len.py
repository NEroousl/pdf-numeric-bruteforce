#!/usr/bin/env python3
"""
pdf_crack_numeric_len.py

Interactive numeric brute-force for a PDF where you don't know the password length.
- First prompts you for the password character length (must be a positive integer).
- Tries all numeric passwords of that length in increasing order:
    e.g. length=4 -> 0000, 0001, ..., 9999
- Overwrites output.txt at start. Appends one line per attempt:
    attempt_number,password,RESULT,elapsed_seconds
- Stops on first successful open and logs the success.

You MUST be the lawful owner or have explicit authorization to test this file.
Usage:
    python pdf_crack_numeric_len.py /path/to/encrypted.pdf
"""

import sys
import time
from pathlib import Path

# Attempt imports in preference order
try:
    import pikepdf
    _BACKEND = "pikepdf"
except Exception:
    try:
        # modern package name is 'pypdf' (formerly PyPDF2)
        from pypdf import PdfReader  # try pypdf first
        _BACKEND = "pypdf"
    except Exception:
        try:
            from PyPDF2 import PdfReader  # fallback older name
            _BACKEND = "pypdf2"
        except Exception:
            _BACKEND = None

OUTPUT_FILE = "output.txt"

def try_open_with_pikepdf(pdf_path: str, password: str) -> bool:
    try:
        with pikepdf.open(pdf_path, password=password):
            return True
    except Exception:
        return False

def try_open_with_pypdf(pdf_path: str, password: str) -> bool:
    try:
        reader = PdfReader(pdf_path)
        # Many pypdf/PyPDF2 versions provide .decrypt() returning int or bool; handle both.
        try:
            dec = reader.decrypt(password)
            if isinstance(dec, int):
                return dec != 0
            if isinstance(dec, bool):
                if dec:
                    return True
            # If decrypt didn't clearly indicate success, try accessing first page
            try:
                _ = reader.pages[0]
                return True
            except Exception:
                return False
        except Exception:
            # Some versions raise on wrong password; try accessing a page to confirm
            try:
                _ = reader.pages[0]
                return True
            except Exception:
                return False
    except Exception:
        return False

def attempt_open(pdf_path: str, password: str) -> bool:
    if _BACKEND == "pikepdf":
        return try_open_with_pikepdf(pdf_path, password)
    elif _BACKEND in ("pypdf", "pypdf2"):
        return try_open_with_pypdf(pdf_path, password)
    else:
        raise RuntimeError("No supported PDF library found. Install 'pikepdf' or 'pypdf' (or 'PyPDF2').")

def prompt_length() -> int:
    """Ask the user for the numeric password length. Returns positive integer."""
    while True:
        try:
            s = input("Enter numeric password character length (positive integer): ").strip()
            length = int(s)
            if length <= 0:
                print("Please enter a positive integer greater than zero.")
                continue
            # Safety: warn if search space huge; require explicit confirmation to continue
            total = 10 ** length
            if total > 10_000_000:
                print(f"Warning: search space = {total:,} attempts (this may take a very long time).")
                confirm = input("Type YES to continue, anything else to re-enter length: ").strip()
                if confirm != "YES":
                    continue
            return length
        except ValueError:
            print("Invalid input. Enter a positive integer (e.g., 4).")

def main():
    if len(sys.argv) != 2:
        print("Usage: python pdf_crack_numeric_len.py /path/to/encrypted.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    pdf_file = Path(pdf_path)
    if not pdf_file.exists() or not pdf_file.is_file():
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    if _BACKEND is None:
        print("Error: no PDF library found. Install 'pikepdf' (recommended) or 'pypdf'/'PyPDF2'.")
        print("Install pikepdf: pip install pikepdf")
        print("Or install pypdf: pip install pypdf")
        sys.exit(1)
    else:
        print(f"Using backend: {_BACKEND}")

    # Ask user for the password character length
    length = prompt_length()
    max_attempts = 10 ** length

    # Overwrite output file at start
    start_time = time.time()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Brute-force started at {time.ctime(start_time)}\n")
        f.write(f"PDF: {pdf_path}\n")
        f.write(f"Password length: {length}\n")
        f.write("Attempt,Password,Result,ElapsedSeconds\n")

    attempt = 0
    found = False
    found_password = None

    try:
        for i in range(max_attempts):
            attempt += 1
            candidate = f"{i:0{length}d}"   # zero-padded numeric string of given length
            elapsed = time.time() - start_time

            try:
                ok = attempt_open(pdf_path, candidate)
            except Exception:
                ok = False

            result_str = "PASS" if ok else "FAIL"

            # Append attempt to output file
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{attempt},{candidate},{result_str},{elapsed:.3f}\n")

            # Print brief progress
            # Print every attempt; if too verbose, you can change to print only every N attempts
            print(f"[{attempt:,}] Trying {candidate} -> {result_str}")

            if ok:
                found = True
                found_password = candidate
                break
    except KeyboardInterrupt:
        print("\nInterrupted by user (KeyboardInterrupt). Stopping.")
    finally:
        total_elapsed = time.time() - start_time
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if found and found_password is not None:
                f.write(f"\nSUCCESS: Password found: {found_password}\n")
                f.write(f"Total attempts: {attempt}. Time elapsed: {total_elapsed:.3f}s\n")
            else:
                f.write(f"\nSTOPPED: Password not found (or process stopped). Attempts: {attempt}. Time elapsed: {total_elapsed:.3f}s\n")

        if found:
            print("\n=== PASSWORD FOUND ===")
            print(f"Password: {found_password}")
            print(f"Attempts: {attempt}. Total time: {total_elapsed:.3f}s")
        else:
            print("\nPassword not found in the tested numeric space (or process stopped).")
            print(f"Attempts: {attempt}. Total time: {total_elapsed:.3f}s")

if __name__ == "__main__":
    main()
