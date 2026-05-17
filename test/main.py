import warnings

from agent_framework.bootstrap import build_cli


def main() -> None:
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    cli = build_cli()
    cli.run()


if __name__ == "__main__":
    main()

