import subprocess
from financial_data_query.errors import FetchError

try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None

# Standard Chrome options shared across all browser-based fetchers
_STANDARD_CHROME_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]

# Per-source install hints for undetected-chromedriver
_UC_INSTALL_HINTS = {
    "stooq": "pip install financial-data-query[stooq]",
    "tw_eco": "pip install financial-data-query[tw_ndc]",
    "tw_pmi": "pip install financial-data-query[tw_ndc]",
    "macroMicro": "pip install financial-data-query[macroMicro]",
    "moea": "pip install webdriver-manager selenium",
}


def _get_chrome_version_main() -> int | None:
    """Auto-detect Chrome browser major version from system."""
    candidates = [
        "google-chrome", "google-chrome-stable",
        "google-chrome-beta", "chromium", "chromium-browser",
    ]
    for cmd in candidates:
        try:
            out = subprocess.check_output(
                [cmd, "--version"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for part in out.split():
                if part[0].isdigit():
                    return int(part.split(".")[0])
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError, IndexError):
            continue
    return None


def _make_chrome_options(args: list[str] | None = None) -> "uc.ChromeOptions":
    """Create ChromeOptions with standard flags for undetected-chromedriver.

    Args:
        args: Additional arguments to add beyond the standard ones.

    Returns:
        Configured ChromeOptions instance.
    """
    if uc is None:
        raise FetchError("undetected-chromedriver is not installed")
    options = uc.ChromeOptions()
    for arg in _STANDARD_CHROME_ARGS:
        options.add_argument(arg)
    if args:
        for arg in args:
            options.add_argument(arg)
    return options


def _create_uc_driver(
    options: "uc.ChromeOptions | None" = None,
    extra_args: list[str] | None = None,
) -> "uc.Chrome":
    """Create a uc.Chrome driver with auto-detected version.

    Args:
        options: Pre-configured ChromeOptions. If None, creates with standard args.
        extra_args: Additional arguments if creating default options.

    Returns:
        Configured uc.Chrome driver.
    """
    if options is None:
        options = _make_chrome_options(extra_args)
    version_main = _get_chrome_version_main()
    if version_main:
        return uc.Chrome(options=options, version_main=version_main)
    return uc.Chrome(options=options)


def _check_uc_installed(source: str) -> None:
    """Check if undetected-chromedriver is installed, raise FetchError with source-specific hint.

    Args:
        source: Source name for install hint lookup.
    """
    if uc is None:
        hint = _UC_INSTALL_HINTS.get(source, "pip install undetected-chromedriver")
        raise FetchError(
            f"undetected-chromedriver 未安裝。\n請執行: {hint}"
        )
