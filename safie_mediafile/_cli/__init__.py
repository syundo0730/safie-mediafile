try:
    from ._cli_app import main
except ImportError:
    # When CLI dependencies are not installed
    import sys

    def main() -> None:  # type: ignore
        print(
            "The safie-mediafile command line client could not run because the required "
            "dependencies were not installed.\nMake sure you've installed "
            "everything with: pip install 'safie-mediafile[cli]'"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
