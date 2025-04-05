import os
import re


def bump_version(version: str) -> str:
    """Bump the version number."""
    major, minor, patch = map(int, version.split("."))
    patch += 1
    return f"{major}.{minor}.{patch}"


def main():
    """Main function for incrementing the version."""
    path = "pyproject.toml"

    with open(path) as f:
        content = f.read()

    # Match version = "x.y.z"
    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        print("Version not found in pyproject.toml")
        return

    current_version = (
        match.group(1) + "." + match.group(2) + "." + match.group(3)
    )
    new_version = bump_version(current_version)

    print(f"::notice:: Bumping version from {current_version} to {new_version}")

    new_content = re.sub(
        r'version\s*=\s*"\d+\.\d+\.\d+"', f'version = "{new_version}"', content
    )

    with open(path, "w") as f:
        f.write(new_content)

    # Output to GitHub Actions
    with open(os.environ["GITHUB_OUTPUT"], "a") as gh_out:
        gh_out.write(f"new_version={new_version}\n")


if __name__ == "__main__":
    main()
