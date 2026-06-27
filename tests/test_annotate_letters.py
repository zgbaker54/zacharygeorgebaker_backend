"""Unit tests for ``annotateLetters`` in ``src/utils/utils.py``.

``annotateLetters`` evaluates a single guess against the answer and
sets each letter's ``evaluation`` field to one of ``'exact'``, ``'misplaced'`` or
``'wrong'``. It also upper-cases every guess letter in place.

Evaluation rules, as implemented:
  * ``exact``     - the letter matches the answer at the same index.
  * ``misplaced`` - the letter is not exact but still has an unconsumed
                    occurrence remaining in the answer (after exact matches and
                    earlier misplaced matches have been consumed).
  * ``wrong``     - no unconsumed occurrence of the letter remains in the answer.

Duplicate handling: both exact and misplaced matches CONSUME an occurrence of
the letter from the answer, so a guess can never be marked ``exact``/``misplaced``
for a given letter more times than that letter actually appears in the answer.
Surplus copies fall through to ``wrong`` (see ``TestDuplicateLetterBehavior``).
"""

import pytest

from src.utils.utils import annotateLetters


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_letters(word, evaluation=None):
    """Build the list-of-dicts structure ``annotateLetters`` expects."""
    return [{"letter": ch, "evaluation": evaluation} for ch in word]


def evaluations(letters):
    """Extract just the evaluation strings, in order."""
    return [letter["evaluation"] for letter in letters]


def letters_str(letters):
    """Extract the (joined) letter characters, in order."""
    return "".join(letter["letter"] for letter in letters)


# ---------------------------------------------------------------------------
# Core evaluation behavior
# ---------------------------------------------------------------------------

class TestExactMatches:
    def test_full_exact_match(self):
        result = annotateLetters(make_letters("EXAMPLE"), "EXAMPLE")
        assert evaluations(result) == ["exact"] * 7

    def test_single_letter_exact(self):
        result = annotateLetters(make_letters("A"), "A")
        assert evaluations(result) == ["exact"]


class TestWrongLetters:
    def test_all_wrong(self):
        # No letter of the guess appears anywhere in the answer.
        result = annotateLetters(make_letters("BCDF"), "WXYZ")
        assert evaluations(result) == ["wrong"] * 4

    def test_single_letter_wrong(self):
        result = annotateLetters(make_letters("Q"), "A")
        assert evaluations(result) == ["wrong"]


class TestMisplacedLetters:
    def test_all_misplaced_reversed(self):
        # Same multiset of letters, every position shifted -> all misplaced.
        result = annotateLetters(make_letters("ABC"), "CAB")
        assert evaluations(result) == ["misplaced", "misplaced", "misplaced"]

    def test_single_misplaced(self):
        # 'C' is present in the answer but not at index 0.
        result = annotateLetters(make_letters("CXY"), "ZZC")
        assert evaluations(result) == ["misplaced", "wrong", "wrong"]


class TestMixedEvaluations:
    def test_exact_misplaced_and_wrong_together(self):
        # answer = SHADOW
        #   S exact (idx0)
        #   O misplaced (in answer at idx4, not idx1)
        #   Q wrong
        #   D exact (idx3)
        #   Z wrong
        #   H misplaced (in answer at idx1, not idx5)
        result = annotateLetters(make_letters("SOQDZH"), "SHADOW")
        assert evaluations(result) == [
            "exact",
            "misplaced",
            "wrong",
            "exact",
            "wrong",
            "misplaced",
        ]

    def test_realistic_seven_letter_guess(self):
        # The game is built around 7-letter words; exercise that length.
        # answer = PICTURE
        #   P exact, R wrong-position?, ... build deterministically:
        #   guess = PENCILS vs PICTURE
        #     P(0)=P exact
        #     E(1) vs I -> E is in PICTURE (idx6) -> misplaced
        #     N(2) vs C -> wrong
        #     C(3) vs T -> C in answer (idx3? answer idx3 is T) C is at idx2 -> misplaced
        #     I(4) vs U -> I in answer (idx1) -> misplaced
        #     L(5) vs R -> wrong
        #     S(6) vs E -> wrong
        result = annotateLetters(make_letters("PENCILS"), "PICTURE")
        assert evaluations(result) == [
            "exact",
            "misplaced",
            "wrong",
            "misplaced",
            "misplaced",
            "wrong",
            "wrong",
        ]


# ---------------------------------------------------------------------------
# Case handling
# ---------------------------------------------------------------------------

class TestCaseHandling:
    def test_lowercase_guess_is_uppercased_in_place(self):
        letters = make_letters("example")
        result = annotateLetters(letters, "EXAMPLE")
        assert letters_str(result) == "EXAMPLE"
        assert evaluations(result) == ["exact"] * 7

    def test_mixed_case_guess_is_uppercased(self):
        result = annotateLetters(make_letters("ExAmPlE"), "EXAMPLE")
        assert letters_str(result) == "EXAMPLE"
        assert evaluations(result) == ["exact"] * 7

    def test_lowercase_guess_evaluates_against_uppercase_answer(self):
        # 'a' should be recognized as matching 'A' after the upper-casing pass.
        result = annotateLetters(make_letters("cab"), "CAB")
        assert evaluations(result) == ["exact", "exact", "exact"]

    def test_answer_must_be_uppercase_to_match(self):
        # The function upper-cases the guess but NOT the answer; a lowercase
        # answer therefore never matches. This documents the contract that
        # callers (AnnotateGuessSequence) pass an already-uppercased answer.
        result = annotateLetters(make_letters("CAB"), "cab")
        assert evaluations(result) == ["wrong", "wrong", "wrong"]


# ---------------------------------------------------------------------------
# Duplicate-letter behavior (documents current logic)
# ---------------------------------------------------------------------------

class TestDuplicateLetterBehavior:
    def test_exact_consumes_answer_position(self):
        # answer LEVEL has E at idx1 and idx3.
        # guess  EEXYZ:
        #   E(1) vs E -> exact (consumes answer idx1)
        #   E(0) -> the remaining E (idx3) is still present -> misplaced
        #   X,Y,Z wrong
        result = annotateLetters(make_letters("EEXYZ"), "LEVEL")
        assert evaluations(result) == [
            "misplaced",
            "exact",
            "wrong",
            "wrong",
            "wrong",
        ]

    def test_exact_consumes_only_one_occurrence(self):
        # answer MANGO has a single A (idx1).
        # guess  AAXYZ:
        #   A(1) vs A -> exact, consumes the only A.
        #   A(0) -> no A left in answer -> wrong.
        result = annotateLetters(make_letters("AAXYZ"), "MANGO")
        assert evaluations(result) == [
            "wrong",
            "exact",
            "wrong",
            "wrong",
            "wrong",
        ]

    def test_misplaced_consumes_so_surplus_duplicate_is_wrong(self):
        # answer MANGO has a single A (idx1), and no guess letter is exact.
        # guess  ABRAS has two A's (idx0, idx3), neither exact.
        # The first A consumes the only A in the answer -> misplaced; the second
        # A has nothing left to match -> wrong.
        result = annotateLetters(make_letters("ABRAS"), "MANGO")
        assert evaluations(result) == [
            "misplaced",
            "wrong",
            "wrong",
            "wrong",
            "wrong",
        ]

    def test_two_misplaced_one_exact_only_one_misplaced_kept(self):
        # The scenario from the feature request: the answer holds the letter
        # exactly once (in a position the guess gets right), and the guess
        # repeats that letter elsewhere. The repeats must NOT be misplaced.
        #
        # answer CIGAR has a single A (idx3).
        # guess  AAGAR:
        #   A(3) vs A -> exact, consumes the only A.
        #   G(2) vs G -> exact.
        #   R(4) vs R -> exact.
        #   A(0), A(1) -> no A left -> both wrong.
        result = annotateLetters(make_letters("AAGAR"), "CIGAR")
        assert evaluations(result) == [
            "wrong",
            "wrong",
            "exact",
            "exact",
            "exact",
        ]

    def test_two_misplaced_no_exact_only_first_counts(self):
        # answer CIGAR has a single A (idx3); guess repeats A in two non-matching
        # positions with no exact A match -> exactly one misplaced, one wrong.
        result = annotateLetters(make_letters("AAXYZ"), "CIGAR")
        assert evaluations(result) == [
            "misplaced",
            "wrong",
            "wrong",
            "wrong",
            "wrong",
        ]

    def test_two_misplaced_when_answer_has_two_occurrences(self):
        # answer ALOHA has two A's (idx0, idx4); guess repeats A twice in
        # non-matching positions -> BOTH may be misplaced.
        # guess XAXAX:
        #   no position matches A's at idx0/idx4
        #   A(1) -> misplaced (consumes one A)
        #   A(3) -> misplaced (consumes the other A)
        result = annotateLetters(make_letters("XAXAX"), "ALOHA")
        assert evaluations(result) == [
            "wrong",
            "misplaced",
            "wrong",
            "misplaced",
            "wrong",
        ]

    def test_exact_takes_priority_over_misplaced_for_consumption(self):
        # answer SASSY has S at idx0, idx2, idx3 (three S's).
        # guess  SSSXX:
        #   S(0) vs S -> exact (consumes idx0)
        #   S(2) vs S -> exact (consumes idx2)
        #   S(1) -> misplaced (one S left at idx3) -> consumes it
        #   X(3), X(4) -> wrong
        result = annotateLetters(make_letters("SSSXX"), "SASSY")
        assert evaluations(result) == [
            "exact",
            "misplaced",
            "exact",
            "wrong",
            "wrong",
        ]


# ---------------------------------------------------------------------------
# Mutation contract & data preservation
# ---------------------------------------------------------------------------

class TestMutationAndPreservation:
    def test_returns_same_list_object(self):
        letters = make_letters("ABC")
        result = annotateLetters(letters, "ABC")
        assert result is letters

    def test_mutates_input_in_place(self):
        letters = make_letters("abc")
        annotateLetters(letters, "ABC")
        # The original reference reflects both upper-casing and evaluation.
        assert letters_str(letters) == "ABC"
        assert evaluations(letters) == ["exact", "exact", "exact"]

    def test_overwrites_preexisting_evaluation(self):
        letters = make_letters("ABC", evaluation="exact")
        result = annotateLetters(letters, "XYZ")
        assert evaluations(result) == ["wrong", "wrong", "wrong"]

    def test_preserves_unrelated_keys(self):
        letters = [
            {"letter": "A", "evaluation": None, "id": 1, "extra": "keep"},
            {"letter": "B", "evaluation": None, "id": 2, "extra": "me"},
        ]
        result = annotateLetters(letters, "AB")
        assert result[0]["id"] == 1 and result[0]["extra"] == "keep"
        assert result[1]["id"] == 2 and result[1]["extra"] == "me"
        assert evaluations(result) == ["exact", "exact"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_guess_and_answer(self):
        result = annotateLetters([], "")
        assert result == []

    def test_guess_longer_than_answer_raises_index_error(self):
        # The exact-match pass indexes the answer by guess position, so a guess
        # longer than the answer reads past the end of the answer list.
        with pytest.raises(IndexError):
            annotateLetters(make_letters("ABC"), "AB")

    def test_guess_shorter_than_answer_evaluates_only_guess_length(self):
        # answer ABCDE, guess AB -> both exact; trailing answer letters ignored.
        result = annotateLetters(make_letters("AB"), "ABCDE")
        assert evaluations(result) == ["exact", "exact"]

    def test_guess_shorter_misplaced_against_longer_answer(self):
        # answer ABCDE, guess EA -> E present (misplaced), A present (misplaced).
        result = annotateLetters(make_letters("EA"), "ABCDE")
        assert evaluations(result) == ["misplaced", "misplaced"]

    def test_does_not_mutate_answer_string(self):
        answer = "ABCDE"
        annotateLetters(make_letters("AXCYE"), answer)
        assert answer == "ABCDE"

    @pytest.mark.parametrize(
        "guess,answer,expected",
        [
            ("WORLD", "WORLD", ["exact"] * 5),
            # DLROW shares the R at idx2 with WORLD (exact); the rest are present
            # but displaced.
            ("WORLD", "DLROW", ["misplaced", "misplaced", "exact", "misplaced", "misplaced"]),
            ("ABCDE", "FGHIJ", ["wrong"] * 5),
            # STARE / RATES are anagrams with no shared position -> all misplaced.
            ("STARE", "RATES", ["misplaced"] * 5),
        ],
    )
    def test_parametrized_words(self, guess, answer, expected):
        result = annotateLetters(make_letters(guess), answer)
        assert evaluations(result) == expected
