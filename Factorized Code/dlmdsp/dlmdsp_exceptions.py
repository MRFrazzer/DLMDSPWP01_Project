# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_exceptions.py                                                           # module: custom exceptions
# ──────────────────────────────────────────────────────────────────────────────
"""Custom errors for DLMDSP.

I group errors here so calling code can catch one base type or something specific.
"""

class DLMDSPError(Exception):                                                     # base exception for package
    """Base error for DLMDSP.

    Catch this if you want one handler for everything the package raises.
    """  # class docstring


class DataShapeMismatchError(DLMDSPError):                                        # raised when data schema is wrong
    """CSV columns don’t match what the pipeline expects.

    Common cases:
    - Missing the X column.
    - Training is not exactly Y1..Y4.
    - Ideal is not exactly Y1..Y50.
    - Test is missing Y.
    """  # class docstring


class AssignmentRuleError(DLMDSPError):                                           # raised when assignment fails tolerance
    """No ideal could accept a test point under its tolerance.

    I include deviations and tolerances in the message to help with debugging.
    """  # class docstring
