#!/usr/bin/env python3
"""
pdf_crack_numeric_len.py

Same functionality as before, with all user-visible strings centralized in messages().
Call m(id) to get a message string and format it with .format(...) for dynamic parts.

Usage:
    python pdf_crack_numeric_len.py /path/to/encrypted.pdf
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


def messages():
    """
    Centralized user-visible messages.
    Sections are separated by comments.

    Usage:
        text = m('category.id')  # returns the raw string
        print(m('category.id').format(var=val))
    """

    msgs = {}

    # -----------------------
    # banners / headers
    # -----------------------
    msgs['banner.line'] = "=" * 60
    msgs['banner.title'] = "PDF NUMERIC BRUTE-FORCE (CLI)".center(60)
    msgs['banner.target'] = "Target: {pdf}"
    msgs['banner.backend'] = "Backend: {backend}"
    msgs['banner.sep'] = "-" * 60

    # -----------------------
    # prompts / inputs
    # -----------------------
    msgs['prompt.length'] = "Password length (positive integer): "
    msgs['prompt.confirm_length'] = "Proceed with this length? [Y/N]: "
    msgs['prompt.pattern'] = "Pattern (use '*' for unknowns). Enter to brute-force all {length} positions:\n"
    msgs['prompt.choose_pattern_action'] = "  [1] Re-enter pattern   [2] Change length   [3] Exit\nChoose 1/2/3: "
    msgs['prompt.proceed'] = "Proceed? [Y/N]: "
    msgs['prompt.single_confirm'] = "Type YES to proceed or anything else to re-enter: "

    # -----------------------
    # info / summary
    # -----------------------
    msgs['info.no_pattern'] = "No pattern provided. Brute-forcing all positions."
    msgs['info.attempt_single'] = "Attempting single password: {password}"
    msgs['info.summary_header'] = "Summary:"
    msgs['info.summary_length_pattern'] = "  Length: {length}    Pattern: {pattern}"
    msgs['info.summary_unknowns'] = "  Unknown positions: {unknowns}"
    msgs['info.summary_remaining'] = "  Remaining attempts: {remaining}"
    msgs['info.large_space_warn'] = "  Warning: remaining search space is very large — this may take a long time."

    # -----------------------
    # progress / status
    # -----------------------
    msgs['progress.line'] = "[{attempt}] {candidate} -> {result}  rate={rate}/s  ETA={eta}"
    msgs['progress.finished'] = "-" * 60
    msgs['progress.found'] = "\n  PASSWORD FOUND: {password}"
    msgs['progress.finished_no'] = "Finished. Password not found in tested space or stopped."
    msgs['progress.attempts_time'] = "  Attempts: {attempts}   Time: {time}"

    # -----------------------
    # warnings / errors
    # -----------------------
    msgs['error.length_positive'] = "Error: length must be > 0"
    msgs['error.length_integer'] = "Error: enter a positive integer"
    msgs['warn.full_space'] = "Warning: full search space = {space} attempts"
    msgs['error.pattern_mismatch'] = "Error: pattern length mismatch"
    msgs['error.pattern_chars'] = "Error: use digits (0-9) and '*' only"
    msgs['error.file_not_found'] = "Error: file not found"
    msgs['error.no_pdf_library'] = "No PDF library found. Install 'pikepdf' or 'pypdf'."

    # -----------------------
    # usage
    # -----------------------
    msgs['usage'] = "Usage: python pdf_crack_numeric_len.py /path/to/encrypted.pdf"

    return msgs


# helper to access messages
_def_messages = messages()
def m(msg_id: str) -> str:
    return _def_messages.get(msg_id, f"<missing message {msg_id}>")


# --- PDF open helpers (unchanged) ---
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
    # <-- runtime error message now comes from messages()
    raise RuntimeError(m('error.no_pdf_library'))


# --- small utilities (unchanged) ---
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


# --- UI printing that uses messages() ---
def print_banner(pdf_path: str):
    print(m('banner.line'))
    print(m('banner.title'))
    print(m('banner.line'))
    print(m('banner.target').format(pdf=pdf_path))
    print(m('banner.backend').format(backend=_BACKEND if _BACKEND else 'none'))
    print(m('banner.sep'))


def prompt_length() -> int:
    while True:
        s = input(m('prompt.length')).strip()
        try:
            length = int(s)
            if length <= 0:
                print(m('error.length_positive'))
                continue
        except ValueError:
            print(m('error.length_integer'))
            continue

        total = 10 ** length
        if total > 10_000_000:
            print(m('warn.full_space').format(space=fmt(total)))
            cinput = input(m('prompt.confirm_length')).strip().upper()
            if cinput != "Y":
                continue
        return length


def prompt_optional_pattern(length: int):
    prompt = m('prompt.pattern').format(length=length)
    while True:
        pat = input(prompt).strip()
        if pat == "":
            print(m('info.no_pattern'))
            return "*" * length
        if len(pat) != length:
            print(m('error.pattern_mismatch'))
            print(m('prompt.choose_pattern_action'), end='')
            choice = input().strip()
            if choice == "1":
                continue
            if choice == "2":
                return None
            sys.exit(0)
        if any(not (ch.isdigit() or ch == "*") for ch in pat):
            print(m('error.pattern_chars'))
            continue
        return pat


def highlight_pattern(pattern: str) -> str:
    # plain ASCII highlighting: keep as-is
    return pattern


def confirm_before_run(length: int, pattern: str, unknown_indices: list, remaining_space: int) -> bool:
    print(m('banner.sep'))
    print(m('info.summary_header'))
    print(m('info.summary_length_pattern').format(length=length, pattern=highlight_pattern(pattern)))
    print(m('info.summary_unknowns').format(unknowns=unknown_indices))
    print(m('info.summary_remaining').format(remaining=fmt(remaining_space)))
    if remaining_space > 10_000_000:
        print(m('info.large_space_warn'))
    ans = input(m('prompt.proceed')).strip().upper()
    return ans == "Y"


def build_candidate_from_pattern(pattern: str, replacement_digits: tuple, unknown_indices: list) -> str:
    s = list(pattern)
    for pos, digit in zip(unknown_indices, replacement_digits):
        s[pos] = digit
    return "".join(s)


def main():
    if len(sys.argv) != 2:
        print(m('usage'))
        sys.exit(1)

    pdf_path = sys.argv[1]
    pdf_file = Path(pdf_path)
    if not pdf_file.exists() or not pdf_file.is_file():
        print(m('error.file_not_found'))
        sys.exit(1)

    if _BACKEND is None:
        print(m('error.no_pdf_library'))
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
            print(m('info.attempt_single').format(password=pattern))
            if input(m('prompt.single_confirm')).strip() == 'YES':
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

    # run brute-force
    start_time = time.time()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Start: {time.ctime(start_time)}\nPDF: {pdf_path}\nLength: {length}\nPattern: {pattern}\n")
        f.write("Attempt,Password,Result,ElapsedSeconds\n")

    attempt = 0
    found = False
    found_password = None
    total_space = 10 ** len(unknown_indices) if len(unknown_indices) else 1

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

            if attempt % PROGRESS_INTERVAL == 0 or ok:
                rate = attempt / max(1e-6, elapsed)
                rem = max(0, total_space - attempt)
                eta = rem / rate if rate > 0 else float("inf")
                print(m('progress.line').format(
                    attempt=fmt(attempt),
                    candidate=candidate,
                    result=result_str,
                    rate=fmt(int(rate)),
                    eta=human_time(eta)
                ))

            if ok:
                found = True
                found_password = candidate
                break
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        total_elapsed = time.time() - start_time
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            if found:
                f.write(f"SUCCESS,{found_password},{attempt},{total_elapsed:.3f}\n")
            else:
                f.write(f"STOPPED,{attempt},{total_elapsed:.3f}\n")

        print(m('progress.finished'))
        if found:
            print(m('progress.found').format(password=found_password))
            print(m('progress.attempts_time').format(attempts=fmt(attempt), time=human_time(total_elapsed)))
        else:
            print(m('progress.finished_no'))
            print(m('progress.attempts_time').format(attempts=fmt(attempt), time=human_time(total_elapsed)))
        print(m('banner.line'))


if __name__ == "__main__":
    main()
