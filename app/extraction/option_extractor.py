import re
from typing import List, Dict, Tuple, Optional


class OptionExtractor:
    """Extracts multiple-choice question options supporting diverse formatting styles."""

    # Line-by-line option patterns ordered by specificity
    LINE_OPTION_PATTERNS = [
        # Pattern 1: [A] Option / [B] Option
        r'^\[([A-Ea-e])\]\s+(.*)$',
        # Pattern 2: (A) Option / (a) Option
        r'^\(([A-Ea-e])\)\s+(.*)$',
        # Pattern 3: A. Option / A) Option
        r'^([A-Ea-e])[\.\)]\s+(.*)$',
        # Pattern 4: (i) Option / (ii) Option / (iii) Option / (iv) Option / (v) Option
        r'^\((i{1,3}|iv|v|I{1,3}|IV|V)\)\s+(.*)$',
        # Pattern 5: i. Option / ii. Option / iii. Option
        r'^(i{1,3}|iv|v|I{1,3}|IV|V)\.\s+(.*)$',
        # Pattern 6: 1) Option / 2) Option (Note: 1. is reserved for question headers, so 1) is option)
        r'^([1-5])\)\s+(.*)$',
    ]

    # Inline option matching pattern e.g. "A. Red  B. Blue  C. Green  D. Yellow" or "[A] Red [B] Blue"
    INLINE_PATTERNS = [
        r'([A-Ea-e])[\.\)]\s+([^\n\t]+?)(?=(?:\s+[A-Ea-e][\.\)]|\s*$))',
        r'\[([A-Ea-e])\]\s+([^\n\t]+?)(?=(?:\s+\[[A-Ea-e]\]|\s*$))',
        r'\(([A-Ea-e])\)\s+([^\n\t]+?)(?=(?:\s+\([A-Ea-e]\)|\s*$))',
    ]

    def extract_options(self, question_text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Extract options from question block text.
        Returns tuple: (cleaned_question_stem_text, list_of_options)
        """
        options: List[Dict[str, str]] = []
        clean_stem = question_text.strip()

        # 1. Try inline option regex matching first
        for inline_pat in self.INLINE_PATTERNS:
            matches = re.findall(inline_pat, question_text)
            if len(matches) >= 2:
                keys_seen = set()
                for key, val in matches:
                    k_upper = key.upper()
                    if k_upper not in keys_seen:
                        options.append({"key": k_upper, "text": val.strip()})
                        keys_seen.add(k_upper)

                # Strip options text from question stem
                first_opt_idx = len(question_text)
                for m in re.finditer(r'(?:^|\s|\n)(?:[A-Ea-e][\.\)]|\[[A-Ea-e]\]|\([A-Ea-e]\))', question_text):
                    first_opt_idx = min(first_opt_idx, m.start())
                if first_opt_idx < len(question_text):
                    clean_stem = question_text[:first_opt_idx].strip()

                return clean_stem, options

        # 2. Line-by-line option matching
        lines = question_text.split('\n')
        stem_lines = []
        in_options = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            matched_opt = False
            for pat in self.LINE_OPTION_PATTERNS:
                match = re.match(pat, stripped)
                if match:
                    key = match.group(1).upper()
                    text = match.group(2).strip()
                    options.append({"key": key, "text": text})
                    matched_opt = True
                    in_options = True
                    break

            if not matched_opt:
                if not in_options:
                    stem_lines.append(line)
                else:
                    # Append continuation text to previous option if already inside options section
                    if options:
                        options[-1]["text"] += " " + stripped
                    else:
                        stem_lines.append(line)

        cleaned_text = "\n".join(stem_lines).strip()
        if not cleaned_text and options:
            cleaned_text = question_text.strip()

        return cleaned_text, options


option_extractor = OptionExtractor()
