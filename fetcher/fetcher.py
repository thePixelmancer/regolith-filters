import tempfile
import shutil
import fsspec
import requests
import json
from pathlib import Path
from urllib.parse import urlparse


def load_github_token():
    """
    Load the GitHub token from data/fetcher/config.json. Returns None if not found or invalid.
    """
    config_path = Path("data/fetcher/config.json")
    if not config_path.exists():
        print("Warning: GitHub token config not found at data/fetcher/config.json. API requests may be rate-limited.")
        return None
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        token = config.get("github_token")
        if not token:
            print("Warning: 'github_token' not found in config file. API requests may be rate-limited.")
        return token
    except Exception as e:
        print(f"Error reading GitHub token config: {e}")
        return None

github_token = load_github_token()
folders = ["data", "RP", "BP"]


def get_top_level_folder(path: str) -> str:
    """
    Get the top-level folder name from a path string.
    Args:
        path (str): The path string (e.g., 'foo/bar/baz').
    Returns:
        str: The top-level folder name, or None if not present.
    """
    return path.strip("/").split("/")[0] if path.strip("/") else None


def copy_from_cache_to_target(cache_dir: Path, target_dir: Path):
    """
    Copy all files and folders from the cache directory to the target directory, skipping the _downloaded marker.
    Args:
        cache_dir (Path): Path to the cache directory containing downloaded files.
        target_dir (Path): Directory to copy files/folders into.
    """
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in cache_dir.iterdir():
        if item.name == "_downloaded":
            continue
        dest = target_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    print(f"Copied all items to {target_dir}")


def get_latest_commit_hash(github_url: str, github_token: str) -> str:
    """
    Given a GitHub file or folder URL and a GitHub token, return the latest commit hash that touched that file or folder.
    Args:
        github_url (str): The GitHub file or folder URL.
        github_token (str): The GitHub personal access token.
    Returns:
        str: The latest commit hash for the specified file or folder.
    Raises:
        ValueError: If no commits are found for the specified path.
    """

    owner, repo, branch, path = parse_github_url(github_url)

    # Use the GitHub API to get the latest commit for the path
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "path": path, "per_page": 1}
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    resp = requests.get(api_url, params=params, headers=headers)
    if resp.status_code == 404:
        raise ValueError("Repository or path not found (404). Check the URL.")
    if resp.status_code == 403:
        # Forbidden: likely private repo or rate-limited
        if not github_token:
            raise PermissionError("Access denied (403). This repository may be private and requires a GitHub token.")
        else:
            raise PermissionError("Access denied (403). Your GitHub token may not have access to this repository.")
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError("No commits found for the specified path.")
    return data[0]["sha"]


def parse_github_url(source_url):
    """
    Parse a GitHub file or folder URL and extract the owner, repository name, branch, and path.

    Args:
        source_url (str): The GitHub URL to parse. Example:
            'https://github.com/owner/repo/tree/branch/path/to/folder'
            or
            'https://github.com/owner/repo/blob/branch/path/to/file'

    Returns:
        tuple: (owner, repo, branch, path)

    Raises:
        ValueError: If the URL does not match the expected GitHub format.
    """
    import re

    m = re.search(
        r"github.com/([^/]+)/([^/]+)/(?:blob|tree)/([^/]+)/(.*)",
        source_url,
    )
    if not m:
        raise ValueError(f"Invalid GitHub URL: {source_url}")
    return m.groups()  # owner, repo, branch, path


def download_from_github(owner, repo, branch, path, cache_dir, github_token):
    """
    Download a file or folder from a GitHub repository to a local cache directory using fsspec.
    Args:
        owner (str): GitHub repository owner.
        repo (str): Repository name.
        branch (str): Branch name.
        path (str): Path within the repository to download.
        cache_dir (str): Local directory to store the downloaded files.
        github_token (str): GitHub personal access token.
    """
    fs = fsspec.filesystem(
        "github",
        org=owner,
        repo=repo,
        username=owner,
        token=github_token,
        branch=branch,
    )
    github_path = path.rstrip("/")
    fs.get(github_path, str(cache_dir), recursive=True)


def copy_to_destination(src_dir, dst_dir):
    """
    Copy all files and folders from the source directory to the destination directory, skipping the _downloaded marker.
    Args:
        src_dir (str or Path): Path to the source directory containing files to copy.
        dst_dir (str or Path): Path to the destination directory.
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        if item.name == "_downloaded":
            continue
        dest = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    print(f"Copied all items to {dst_dir}")


def load_cache(cache_path):
    """
    Load the cache from a JSON file if it exists, otherwise return an empty dict.
    Args:
        cache_path (str): Path to the cache JSON file.
    Returns:
        dict: The loaded cache dictionary.
    """
    cache_path = Path(cache_path)
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache_path, cache):
    """
    Save the cache dictionary to a JSON file.
    Args:
        cache_path (str): Path to the cache JSON file.
        cache (dict): The cache dictionary to save.
    """
    cache_path = Path(cache_path)
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def main():
    cache_path = Path(tempfile.gettempdir()) / "regolith_fetcher_cache.json"
    file_cache_dir = Path(tempfile.gettempdir()) / "regolith_fetcher_files"
    file_cache_dir.mkdir(parents=True, exist_ok=True)
    cache = load_cache(cache_path)

    for folder in folders:
        for fetch_file in Path(folder).rglob("_fetch.json"):
            fetch_file = Path(fetch_file)
            with fetch_file.open("r", encoding="utf-8") as f:
                fetch_data = json.load(f)

            # Remove the _fetch.json file after reading
            try:
                fetch_file.unlink()
                print(f"Removed fetch file: {fetch_file}")
            except Exception as e:
                print(f"Error removing fetch file {fetch_file}: {e}")

            fetch_file_dir = fetch_file.parent
            for fetcher in fetch_data:
                source_url = fetcher.get("source")
                target = fetcher.get("target", "")
                if not source_url:
                    continue

                # Get latest commit hash (from cache or GitHub)
                latest_hash = cache.get(source_url)
                if not latest_hash:
                    try:
                        latest_hash = get_latest_commit_hash(source_url, github_token)
                        cache[source_url] = latest_hash
                        print(f"Fetched and cached: {latest_hash}")
                    except PermissionError as e:
                        print(f"Warning: {e}\nSkipping fetch for {source_url}.")
                        continue
                    except Exception as e:
                        print(f"Error fetching commit hash for {source_url}: {e}")
                        continue
                else:
                    print(f"Cache hit: {latest_hash}")

                # Prepare cache dir for this hash
                hash_cache_dir = file_cache_dir / latest_hash
                hash_cache_dir.mkdir(parents=True, exist_ok=True)

                # Parse repo, branch, and path from the URL (always needed)
                try:
                    owner, repo, branch, path = parse_github_url(source_url)
                except ValueError as e:
                    print(e)
                    continue

                # Determine if we need to (re)download
                cache_marker = hash_cache_dir / "_downloaded"
                need_download = not cache_marker.exists()

                if need_download:
                    try:
                        download_from_github(
                            owner, repo, branch, path, hash_cache_dir, github_token
                        )
                        with cache_marker.open("w") as f:
                            f.write("ok")
                        print(f"Downloaded {source_url} to cache {hash_cache_dir}")
                    except Exception as e:
                        print(f"Error downloading {source_url}: {e}")
                        continue
                else:
                    print(f"Using cached files for {source_url}")

                # Handle target logic for copying
                if not target or target.strip() == "":
                    # No target specified: create a top-level folder named after the top folder in the path
                    top_folder = get_top_level_folder(path)
                    if not top_folder:
                        print(f"No top-level folder found in path: {path}, skipping.")
                        continue
                    dst_folder = fetch_file_dir / top_folder
                    copy_to_destination(hash_cache_dir, dst_folder)
                else:
                    # Target specified: copy all files/folders into the target path (relative to fetch_file_dir)
                    target_path = (fetch_file_dir / target).resolve()
                    copy_to_destination(hash_cache_dir, target_path)
    save_cache(cache_path, cache)


if __name__ == "__main__":
    main()
