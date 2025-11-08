#!/usr/bin/env python3
"""
pdf_try_last4_variants.py

Brute-force the last-4-digit password variants for PDFs where the hint says:
"password = last 4 digits of account number".

Usage:
    python pdf_try_last4_variants.py /path/to/encrypted.pdf
or if you prefer a mask where the last 4 are wildcards:
    python pdf_try_last4_variants.py /path/to/encrypted.pdf '802603****'

The script will:
 - If a mask is provided with '*' characters, only iterate wildcard positions.
 - Otherwise, assume the unknown part is the last 4 digits and brute-force 0000..9999.
 - For each numeric candidate it tries a set of plausible encodings/variants:
     plain, reversed, UTF-16LE, UTF-16BE, reversed+UTF-16.
 - Prints and logs every attempt. Writes results to output.txt.
"""
import sys
import time
from pathlib import Path
import itertools

# Try pikepdf first, else pypdf (PyPDF2/pypdf)
try:
    import pikepdf
    BACKEND = "pikepdf"
except Exception:
    try:
        from PyPDF2 import PdfReader
        BACKEND = "pypdf"
    except Exception:
        BACKEND = None

OUTPUT_FILE = "output.txt"

def try_open_with_pikepdf(pdf_path: str, password) -> bool:
    # pikepdf.open accepts either str or bytes; try both
    try:
        # pikepdf will accept bytes or str
        with pikepdf.open(pdf_path, password=password):
            return True
    except Exception:
        return False

def try_open_with_pypdf(pdf_path: str, password) -> bool:
    # PyPDF2 expects a string; attempt decode bytes if needed.
    try:
        reader = PdfReader(pdf_path)
        # If password is bytes, try decoding using utf-8/utf-16le safely
        pwd = password
        if isinstance(password, (bytes, bytearray)):
            for enc in ("utf-8", "utf-16-le", "utf-16-be", "latin1"):
                try:
                    pwd = password.decode(enc)
                    break
                except Exception:
                    pwd = None
            if pwd is None:
                pwd = ""  # fallback
        # PdfReader.decrypt returns int in many versions (0 fail)
        try:
            dec = reader.decrypt(pwd)
            if isinstance(dec, int):
                return dec != 0
            # fallback: try reading pages to see if open succeeded
            try:
                _ = reader.pages[0]
                return True
            except Exception:
                return False
        except Exception:
            try:
                _ = reader.pages[0]
                return True
            except Exception:
                return False
    except Exception:
        return False

def attempt_open(pdf_path: str, password) -> bool:
    if BACKEND == "pikepdf":
        return try_open_with_pikepdf(pdf_path, password)
    elif BACKEND == "pypdf":
        return try_open_with_pypdf(pdf_path, password)
    else:
        raise RuntimeError("No PDF backend available. Install 'pikepdf' or 'pypdf' (PyPDF2).")

def generate_last4_from_mask(mask: str, wildcard='*'):
    # If mask contains wildcard positions, generate candidates replacing them.
    # If mask has exactly 4 wildcards at the end (or anywhere), we handle them.
    wc_positions = [i for i,ch in enumerate(mask) if ch == wildcard]
    if not wc_positions:
        # no wildcard: if mask length >= 4 assume last 4 unknown -> generate last4 0000..9999 appended?
        # Simpler: treat mask as full literal password only.
        yield mask
        return

    n = len(wc_positions)
    if n > 6:
        # safeguard -- but user asked last4 so n likely 4
        pass
    # iterate numeric values 0..10^n -1 in natural order
    total = 10 ** n
    for val in range(total):
        digits = str(val).zfill(n)
        s = list(mask)
        for pos, d in zip(wc_positions, digits):
            s[pos] = d
        yield ''.join(s)

def build_variants(candidate_str: str):
    """
    For a candidate string (e.g. "0123"), yield plausible variants to try:
      - plain ascii str
      - reversed string
      - UTF-16LE bytes of plain and reversed
      - UTF-16BE bytes of plain and reversed
    """
    s = candidate_str
    rev = s[::-1]
    variants = [
        s,
        rev,
        s.encode("utf-8"),
        rev.encode("utf-8"),
        s.encode("utf-16-le"),
        rev.encode("utf-16-le"),
        s.encode("utf-16-be"),
        rev.encode("utf-16-be"),
    ]
    # Deduplicate preserving order
    seen = set()
    out = []
    for v in variants:
        key = v if isinstance(v, str) else ("B", v)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out

def main():
    if len(sys.argv) not in (2,3):
        print("Usage:")
        print("  python pdf_try_last4_variants.py /path/to/encrypted.pdf")
        print("  python pdf_try_last4_variants.py /path/to/encrypted.pdf '802603****'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    mask = sys.argv[2] if len(sys.argv) == 3 else None

    pdf_file = Path(pdf_path)
    if not pdf_file.exists() or not pdf_file.is_file():
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    if BACKEND is None:
        print("Error: no PDF backend found. Install 'pikepdf' (recommended) or 'pypdf'.")
        sys.exit(1)
    else:
        print(f"Using backend: {BACKEND}")

    # If mask given, use it, otherwise assume last 4 digits unknown and iterate 0000..9999
    if mask:
        # make sure shell didn't expand wildcards (quote it in PowerShell)
        print(f"Mask provided: {mask}")
        gen = generate_last4_from_mask(mask, wildcard='*')
        # count = 10 ** mask.count('*') but we won't compute if huge
        total_expected = 10 ** mask.count('*') if mask.count('*')>0 else 1
    else:
        # default: brute-force 4 digits in last-4 position
        print("No mask provided — iterating last 4 digits 0000..9999")
        # produce masks of form '0000'..'9999' (plain last4 candidates)
        def plain_gen():
            for v in range(10000):
                yield str(v).zfill(4)
        gen = plain_gen()
        total_expected = 10000

    print(f"Total candidates (numeric) to try (approx): {total_expected:,}")
    start = time.time()
    attempt = 0
    found = False
    found_info = None

    # prepare output file (overwrite)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outf:
        outf.write(f"Start: {time.ctime(start)}\n")
        outf.write(f"PDF: {pdf_path}\n")
        outf.write(f"Mask: {mask}\n")
        outf.write("Attempt,PasswordVariant,Type,Result,ElapsedSeconds\n")

    # Iterate every numeric candidate in order
    for base_candidate in gen:
        attempt += 1
        elapsed = time.time() - start
        # choose the "core" digits to present in logs (if mask present, base_candidate is full password)
        core = base_candidate if mask else base_candidate
        # build plausible variants
        variants = build_variants(core)
        for var in variants:
            # For logging: determine type label
            typ = "str" if isinstance(var, str) else f"bytes({len(var)})"
            # try opening
            try:
                ok = attempt_open(str(pdf_file), var)
            except Exception:
                ok = False

            result = "PASS" if ok else "FAIL"
            # print every single attempt (very verbose)
            print(f"[{attempt:,}] Trying base={core} variant=({typ}) -> {result} (elapsed {elapsed:.3f}s)")

            # log attempt
            with open(OUTPUT_FILE, "a", encoding="utf-8") as outf:
                # for bytes variants write a hex snippet to be readable
                p_repr = var if isinstance(var, str) else "0x" + var.hex()[:40]
                outf.write(f"{attempt},{p_repr},{typ},{result},{elapsed:.3f}\n")

            if ok:
                found = True
                found_info = (core, var, typ, attempt, elapsed)
                break

        if found:
            break

    total_elapsed = time.time() - start
    with open(OUTPUT_FILE, "a", encoding="utf-8") as outf:
        if found:
            core, var, typ, at, el = found_info
            p_repr = var if isinstance(var, str) else "0x" + var.hex()
            outf.write(f"\nSUCCESS: base={core}, variant={p_repr}, type={typ}, attempt={at}, elapsed={el:.3f}s\n")
            outf.write(f"Total attempts: {attempt}. Total time: {total_elapsed:.3f}s\n")
        else:
            outf.write(f"\nCOMPLETE: password not found in tested variants.\n")
            outf.write(f"Total attempts: {attempt}. Total time: {total_elapsed:.3f}s\n")

    if found:
        core, var, typ, at, el = found_info
        p_repr = var if isinstance(var, str) else "0x" + var.hex()
        print("\n=== PASSWORD FOUND ===")
        print(f"Base digits: {core}")
        print(f"Successful variant: {p_repr} (type={typ})")
        print(f"Attempts: {at}. Time: {total_elapsed:.3f}s")
    else:
        print("\nSearch finished — no matching variant found in the tested space.")
        print(f"Total numeric candidates tried: {attempt}. Time: {total_elapsed:.3f}s")
        print("Check that the bank uses exactly the last 4 digits (no prefix/suffix/extra characters), and confirm account number length/format.")

if __name__ == "__main__":
    main()
