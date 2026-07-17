import re
import wave
from pathlib import Path

import fitz
from piper import PiperVoice, SynthesisConfig


PDF_PATH = Path("self-adjusting-computation.pdf")
VOICE_PATH = Path("en_US-kristin-medium.onnx")
OUTPUT_DIR = Path("./self_adjusting_computation_pdf_tts")

# PDF pages 9 through 14 contain the table of contents.
TOC_PDF_PAGES = range(9, 15)

# Printed thesis page 1 is PDF page 19.
PRINTED_PAGE_TO_PDF_PAGE_OFFSET = 18


def extract_pages(pdf_path: Path) -> dict[int, str]:
    """Return {one_based_pdf_page_number: page_text}."""
    with fitz.open(pdf_path) as pdf:
        return {
            page_number: page.get_text("text", sort=True)
            for page_number, page in enumerate(pdf, start=1)
        }


def parse_toc(page_text: dict[int, str]) -> list[tuple[str, str, int]]:
    """
    Return:
        [
            ("1", "Introduction", 1),
            ("1.1", "Overview and Contributions of this Thesis", 4),
            ...
        ]
    """
    toc_text = "\n".join(
        page_text[page_number]
        for page_number in TOC_PDF_PAGES
    )

    sections = []

    for line in toc_text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        # Match:
        # 4.2 Virtual Clock and the Order Maintenance Data Structure . . . 30
        match = re.match(
            r"^(\d+(?:\.\d+)*|A(?:\.\d+)*)\s+"
            r"(.+?)"
            r"(?:\s+\.\s*)+"
            r"(\d+)$",
            line,
        )

        # Chapter entries often have no dot leaders:
        # 1 Introduction 1
        if match is None:
            match = re.match(
                r"^(\d+|A)\s+(.+?)\s+(\d+)$",
                line,
            )

        if match is None:
            continue

        section_number = match.group(1)
        title = match.group(2).strip(" .")
        printed_page = int(match.group(3))

        sections.append(
            (section_number, title, printed_page)
        )

    return sections


def clean_text(text: str) -> str:
    # Join hyphenated words split across lines.
    text = re.sub(
        r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])",
        "",
        text,
    )

    # Replace normal line wrapping with spaces.
    text = re.sub(r"\s*\n\s*", " ", text)

    # Collapse excessive whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def safe_filename(text: str) -> str:
    text = text.replace(".", "-")
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text)
    return text.strip("_")[:100]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting PDF text...")
    page_text = extract_pages(PDF_PATH)

    print("Parsing table of contents...")
    sections = parse_toc(page_text)

    if not sections:
        raise RuntimeError("Could not parse the table of contents.")

    print(f"Found {len(sections)} sections.")

    voice = PiperVoice.load(str(VOICE_PATH))

    for index, (number, title, printed_page) in enumerate(
        sections,
        start=1,
    ):
        start_pdf_page = (
            printed_page
            + PRINTED_PAGE_TO_PDF_PAGE_OFFSET
        )

        if index < len(sections):
            next_printed_page = sections[index][2]
            end_pdf_page = (
                next_printed_page
                + PRINTED_PAGE_TO_PDF_PAGE_OFFSET
            )
        else:
            end_pdf_page = max(page_text) + 1

        # This is intentionally crude. Sections beginning on the same page
        # may contain overlapping text.
        text = " ".join(
            page_text.get(page_number, "")
            for page_number in range(
                start_pdf_page,
                end_pdf_page,
            )
        )

        text = clean_text(text)

        if not text:
            print(f"Skipping empty section {number}: {title}")
            continue

        filename = (
            f"{index:03d}_"
            f"{safe_filename(number)}_"
            f"{safe_filename(title)}.wav"
        )

        output_path = OUTPUT_DIR / filename

        if output_path.exists():
            print(f"Skipping existing {filename}")
            continue

        spoken_text = f"Section {number}. {title}. {text}"

        print(f"[{index}/{len(sections)}] {filename}")

        syn_config = SynthesisConfig(length_scale=0.8) #25% faster

        with wave.open(str(output_path), "wb") as wav_file:
            voice.synthesize_wav(
                spoken_text,
                wav_file,
                syn_config=syn_config,
            )


if __name__ == "__main__":
    main()