import os
import re
import sys


def bump_version(version: str, bump_type: str) -> str:
    """Bump the version number based on bump type."""
    major, minor, patch = map(int, version.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def main():
    """Main function for incrementing the version."""
    bump_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    path = "pyproject.toml"

    with open(path) as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        print("Version not found in pyproject.toml")
        return

    current_version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
    new_version = bump_version(current_version, bump_type)

    print(f"::notice:: Bumping version from {current_version} to {new_version}")

    new_content = re.sub(
        r'version\s*=\s*"\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        content,
    )

    with open(path, "w") as f:
        f.write(new_content)

    with open(os.environ["GITHUB_OUTPUT"], "a") as gh_out:
        gh_out.write(f"new_version={new_version}\n")


if __name__ == "__main__":
    main()
