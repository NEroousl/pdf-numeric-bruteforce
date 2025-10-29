# pdf-numeric-bruteforce

Interactive numeric brute-force tool for encrypted PDFs (single-length numeric passwords).

> **Warning:** You **must** be the lawful owner of the PDF or have explicit written authorization to test it. Unauthorized access attempts may be illegal. educational purpose ONLY!!!

---

## Features

* Tries all zero-padded numeric passwords of a given length (e.g. `0000` → `9999` for length `4`).
* Auto-detects backend: `pikepdf` (recommended) or `pypdf`/`PyPDF2`.
* Logs every attempt to `output.txt` (CSV-style) and stops on first successful open.
* Simple, single-threaded, easy to read and modify.

---

## Quick start (copy-paste)

```bash
# 1) Clone or copy this repo so that pdf_crack_numeric_len.py is in the current folder
# 2) Create and activate a virtual environment (recommended)

# Unix / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (cmd)
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3) Upgrade pip and install dependencies
pip install --upgrade pip
# Recommended backend
pip install pikepdf
# or alternative backend
# pip install pypdf

# 4) Run the script
python pdf_crack_numeric_len.py /path/to/encrypted.pdf
```

---

## Usage (interactive)

1. Run the script with the PDF path as the only argument:

   ```bash
   python pdf_crack_numeric_len.py /path/to/encrypted.pdf
   ```

2. Follow prompts:

   * Enter numeric password character length (positive integer), e.g. `4`.
   * If the search space is larger than `10_000_000` attempts, you'll get a warning and must type `YES` to proceed.

3. Output:

   * `output.txt` is overwritten when the script starts and receives one line per attempt:

     ```
     Attempt,Password,Result,ElapsedSeconds
     1,0000,FAIL,0.002
     2,0001,FAIL,0.004
     ...
     1023,1023,PASS,12.345
     ```
   * On success the script prints the password and appends a `SUCCESS` block to `output.txt`.

---

## Example

```
$ python pdf_crack_numeric_len.py secret.pdf
Using backend: pikepdf
Enter numeric password character length (positive integer): 4
[1] Trying 0000 -> FAIL
[2] Trying 0001 -> FAIL
...
[1023] Trying 1023 -> PASS

=== PASSWORD FOUND ===
Password: 1023
Attempts: 1023. Total time: 12.345s
```

---

## Configuration & suggestions

* To reduce verbosity, you can modify the script to print progress every N attempts instead of every attempt.
* For very large search spaces, consider restricting the range (add `--start` / `--end` options) or implementing resume support to avoid repeating work.
* This script is intentionally single-threaded and educational — do not expect industrial cracking speed.

---

## Security & Responsible Use

* Use only on files you own or are explicitly permitted to test.
* Keep `output.txt` private — it can contain discovered passwords.
* If you find sensitive data during authorized testing, follow your organization's disclosure/handling policy.

---

## Troubleshooting

* `pikepdf` may require system packages (libqpdf, build tools). If `pip install pikepdf` fails, check the `pikepdf` documentation or install the binary packages appropriate to your OS.
* If neither `pikepdf` nor `pypdf` is installed the script will exit with instructions to install one of them.

---

## License (MIT)

This project is licensed under the MIT License — see the full text below.

```
MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

`2025` `@NeroOUSL` all rights recieved