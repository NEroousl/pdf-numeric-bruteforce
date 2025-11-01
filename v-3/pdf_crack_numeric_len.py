#!/usr/bin/env python3
"""
pdf_crack_numeric_len.py

Beautified CLI for numeric PDF password brute-force with optional partial pattern.

Usage:
    python pdf_crack_numeric_len.py /path/to/encrypted.pdf

You MUST have authorization to test this file.
"""
import sys
import time
from pathlib import Path
from itertools import product

# Try PDF libraries
try:
    import pikepdf
    _BACKEND = "pikepdf"
except Exception:
    try:
        from pypdf import PdfReader
        _BACKEND = "pypdf"
    except Exception:
        try:
            from PyPDF2 import PdfReader
            _BACKEND = "pypdf2"
        except Exception:
            _BACKEND = None

OUTPUT_FILE = "output.txt"
PROGRESS_INTERVAL = 5000  # print progress every N attempts


# ANSI helpers (safe: fall back to no color if not supported)
def _supports_color():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

_COLOR = _supports_color()
def c(text, code):
    if not _COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

BOLD = (lambda s: c(s, "1")) if _COLOR else (lambda s: s)
RED = (lambda s: c(s, "31")) if _COLOR else (lambda s: s)
GREEN = (lambda s: c(s, "32")) if _COLOR else (lambda s: s)
YELLOW = (lambda s: c(s, "33")) if _COLOR else (lambda s: s)
CYAN = (lambda s: c(s, "36")) if _COLOR else (lambda s: s)


def try_open_with_pikepdf(pdf_path: str, password: str) -> bool:
    try:
        with pikepdf.open(pdf_path, password=password):
            return True
    except Exception:
        return False


def try_open_with_pypdf(pdf_path: str, password: str) -> bool:
    try:
        reader = PdfReader(pdf_path)
        try:
            dec = reader.decrypt(password)
            if isinstance(dec, int):
                return dec != 0
            if isinstance(dec, bool):
                return dec
            # fallback: try accessing a page
            _ = reader.pages[0]
            return True
        except Exception:
            return False
    except Exception:
        return False


def attempt_open(pdf_path: str, password: str) -> bool:
    if _BACKEND == "pikepdf":
        return try_open_with_pikepdf(pdf_path, password)
    if _BACKEND in ("pypdf", "pypdf2"):
        return try_open_with_pypdf(pdf_path, password)
    raise RuntimeError("No PDF library found. Install 'pikepdf' or 'pypdf'.")


def fmt(n: int) -> str:
    return f"{n:,}"


def human_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def print_banner(pdf_path: str):
    print(BOLD("=" * 60))
    print(BOLD("PDF NUMERIC BRUTE-FORCE (CLI)".center(60)))
    print(BOLD("=" * 60))
    print(f"Target: {CYAN(pdf_path)}")
    print(f"Backend: {YELLOW(_BACKEND) if _BACKEND else RED('none')}")
    print(BOLD("-" * 60))


def prompt_length() -> int:
    while True:
        s = input("Password length (positive integer): ").strip()
        try:
            length = int(s)
            if length <= 0:
                print(RED("Error: length must be > 0"))
                continue
        except ValueError:
            print(RED("Error: enter a positive integer"))
            continue

        total = 10 ** length
        if total > 10_000_000:
            print(YELLOW(f"Warning: full search space = {fmt(total)} attempts"))
            cinput = input("Proceed with this length? [Y/N]: ").strip().upper()
            if cinput != "Y":
                continue
        return length


def prompt_optional_pattern(length: int):
    prompt = f"Pattern (use '*' for unknowns). Enter to brute-force all {length} positions:\n"
    while True:
        pat = input(prompt).strip()
        if pat == "":
            pat = "*" * length
            print(CYAN("No pattern provided. Brute-forcing all positions."))
            return pat
        if len(pat) != length:
            print(RED("Error: pattern length mismatch"))
            print("  [1] Re-enter pattern   [2] Change length   [3] Exit")
            choice = input("Choose 1/2/3: ").strip()
            if choice == "1":
                continue
            if choice == "2":
                return None
            sys.exit(0)
        if any(not (ch.isdigit() or ch == "*") for ch in pat):
            print(RED("Error: use digits (0-9) and '*' only"))
            continue
        return pat


def highlight_pattern(pattern: str) -> str:
    # highlight '*' in yellow so pattern is easy to read
    if not _COLOR:
        return pattern
    out = []
    for ch in pattern:
        if ch == "*":
            out.append(YELLOW(ch))
        else:
            out.append(GREEN(ch))
    return "".join(out)


def build_candidate_from_pattern(pattern: str, replacement_digits: tuple, unknown_indices: list) -> str:
    s = list(pattern)
    for pos, digit in zip(unknown_indices, replacement_digits):
        s[pos] = digit
    return "".join(s)


def confirm_before_run(length: int, pattern: str, unknown_indices: list, remaining_space: int) -> bool:
    print(BOLD("-" * 60))
    print("Summary:")
    print(f"  Length: {fmt(length)}    Pattern: {highlight_pattern(pattern)}")
    print(f"  Unknown positions: {unknown_indices}")
    print(f"  Remaining attempts: {fmt(remaining_space)}")
    if remaining_space > 10_000_000:
        print(YELLOW("  Warning: remaining search space is very large — this may take a long time."))
    ans = input("Proceed? [Y/N]: ").strip().upper()
    return ans == "Y"


def main():
    if len(sys.argv) != 2:
        print("Usage: python pdf_crack_numeric_len.py /path/to/encrypted.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    pdf_file = Path(pdf_path)
    if not pdf_file.exists() or not pdf_file.is_file():
        print(RED("Error: file not found"))
        sys.exit(1)

    if _BACKEND is None:
        print(RED("Error: no PDF library found. Install 'pikepdf' or 'pypdf'"))
        sys.exit(1)

    print_banner(pdf_path)

    while True:
        length = prompt_length()
        pattern = prompt_optional_pattern(length)
        if pattern is None:
            continue

        unknown_indices = [i for i, ch in enumerate(pattern) if ch == "*"]
        unknown_count = len(unknown_indices)

        if unknown_count == 0:
            print(BOLD("Attempting single password: "), highlight_pattern(pattern))
            if input("Confirm and try this password? [Y/N]: ").strip().upper() == "Y":
                candidates_iter = [pattern]
                remaining_space = 1
                break
            else:
                continue

        remaining_space = 10 ** unknown_count
        if not confirm_before_run(length, pattern, unknown_indices, remaining_space):
            continue

        def candidate_generator():
            for digits in product("0123456789", repeat=unknown_count):
                yield build_candidate_from_pattern(pattern, digits, unknown_indices)

        candidates_iter = candidate_generator()
        break

    start_time = time.time()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Start: {time.ctime(start_time)}\nPDF: {pdf_path}\nLength: {length}\nPattern: {pattern}\n")
        f.write("Attempt,Password,Result,ElapsedSeconds\n")

    attempt = 0
    found = False
    found_password = None

    try:
        for candidate in candidates_iter:
            attempt += 1
            elapsed = time.time() - start_time
            try:
                ok = attempt_open(pdf_path, candidate)
            except Exception:
                ok = False

            result_str = "PASS" if ok else "FAIL"
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{attempt},{candidate},{result_str},{elapsed:.3f}\n")

            # Progress reporting (throttled)
            if attempt % PROGRESS_INTERVAL == 0 or ok:
                rate = attempt / max(1e-6, elapsed)
                remaining = (10 ** len(unknown_indices)) - attempt if len(unknown_indices) else 0
                # If pattern has unknowns, remaining must be computed differently:
                if len(unknown_indices):
                    total_space = 10 ** len(unknown_indices)
                    rem = total_space - attempt
                    eta = rem / rate if rate > 0 else float("inf")
                else:
                    rem = 0
                    eta = 0.0
                print(BOLD(f"[{fmt(attempt)}]") + f" {candidate} -> {result_str}  "
                      f"rate={fmt(int(rate))}/s  ETA={human_time(eta)}")

            if ok:
                found = True
                found_password = candidate
                break
    except KeyboardInterrupt:
        print(RED("\nInterrupted by user"))
    finally:
        total_elapsed = time.time() - start_time
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if found:
                f.write(f"SUCCESS,{found_password},{attempt},{total_elapsed:.3f}\n")
            else:
                f.write(f"STOPPED,{attempt},{total_elapsed:.3f}\n")

        print(BOLD("-" * 60))
        if found:
            print(GREEN("PASSWORD FOUND:"), BOLD(found_password))
            print(f"Attempts: {fmt(attempt)}   Time: {human_time(total_elapsed)}")
        else:
            print(YELLOW("Finished. Password not found in tested space or stopped."))
            print(f"Attempts: {fmt(attempt)}   Time: {human_time(total_elapsed)}")
        print(BOLD("=" * 60))


if __name__ == "__main__":
    main()
