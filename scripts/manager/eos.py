from typing import Optional
import os
import subprocess
import base64
import io
import tarfile
import requests

# Python 3.11+ compatible import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import tomli_w

from config import get_server_binary
from custom_logging import Logger

logger = Logger.get_logger(__name__)


def dump_credentials_from_binary(config: dict) -> Optional[dict]:
    """
    Extract EOS API credentials (DedicatedServerClientId, DedicatedServerClientSecret, DeploymentId)
    from the Ark server binary files using pdb-sym2addr-rs.

    Args:
        config (dict): The configuration settings.

    Returns:
        Optional[dict]: A dictionary containing EOS API credentials if successful, else None.
    """
    # Ask user input, return by default
    choice = input(
        "To display the full status, the EOS API credentials will have to be extracted from the server binary files using pdb-sym2addr-rs (azixus/pdb-sym2addr-rs). Do you want to proceed [y/n]?: "
    ).lower()
    if choice not in ["y", "yes"]:
        return None

    dl = config["ark"]["advanced"]["pdb-sym2addr_dl"]
    pdb_sym2addr_path = config["ark"]["advanced"]["pdb-sym2addr_path"]

    # Download tar.gz file
    try:
        res = requests.get(dl, stream=True, timeout=20)
    except (requests.exceptions.Timeout, requests.exceptions.TooManyRedirects) as e:
        logger.error("[red]Failed to download file. Err: %s[/]", e)
        return None

    if res.status_code != 200:
        logger.error("[red]Failed to download file. Code: %s[/]", res.status_code)
        return None

    # Extract file and set permissions
    with tarfile.open(fileobj=io.BytesIO(res.raw.read()), mode="r:gz") as t:
        raw = t.extractfile(os.path.basename(pdb_sym2addr_path)).read()
        with open(pdb_sym2addr_path, "wb") as f:
            f.write(raw)
        os.chmod(pdb_sym2addr_path, 0o755)

    # Run and dump credentials
    server_binary = get_server_binary(config)
    if server_binary is None:
        logger.error("[red]Server binary not found at %s[/]", server_binary)
        return None

    server_pdb = server_binary.replace(".exe", ".pdb")
    if not os.path.exists(server_pdb):
        logger.error("[red]Server pdb not found at %s.[/]", server_pdb)
        return None

    cmd = [
        pdb_sym2addr_path,
        server_binary,
        server_pdb,
        "DedicatedServerClientSecret",
        "DedicatedServerClientId",
        "DeploymentId",
    ]
    res = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    if res.returncode != 0:
        logger.error("[red]Failed to dump symbols. Err: %s[/]", res.returncode)
        return None

    syms = {}
    for l in res.stdout.decode().splitlines()[1:]:
        sym = l.split(",")
        syms[f"{sym[1]}"] = sym[2]

    try:
        token = base64.b64encode(
            f"{syms['DedicatedServerClientId']}:{syms['DedicatedServerClientSecret']}".encode()
        ).decode()
        deployment_id = syms["DeploymentId"]
    except KeyError:
        logger.error("[red]Failed to dump credentials.[/]")
        return None

    eos_config = {}
    eos_config["DedicatedServerClientToken"] = token
    eos_config["DeploymentId"] = deployment_id

    eos_conf_file = config["ark"]["advanced"]["eos_file"]
    with open(eos_conf_file, "wb") as f:
        tomli_w.dump(eos_config, f)

    return eos_config


def try_load_eos_conf(config: dict) -> Optional[dict]:
    """
    Load EOS API credentials from a file.

    Args:
        config (dict): The configuration settings.

    Returns:
        Optional[dict]: A dictionary containing EOS API credentials if the file is valid, else None.
    """
    eos_creds_file = config["ark"]["advanced"]["eos_file"]
    try:
        with open(eos_creds_file, "rb") as f:
            # Load and check file is valid
            eos = tomllib.load(f)
            if "DedicatedServerClientToken" in eos and "DeploymentId" in eos:
                return eos
            else:
                return None
    except FileNotFoundError:
        return None


def get_eos_credentials(config: dict) -> Optional[dict]:
    """
    Try to load EOS API credentials from a file, otherwise request the user to download them
    using pdb-sym2addr-rs.

    Args:
        config (dict): The configuration settings.

    Returns:
        Optional[dict]: A dictionary containing EOS API credentials if successful, else None.
    """
    # Try to get, otherwise request user to download them
    creds = try_load_eos_conf(config)
    if creds:
        return creds
    else:
        return dump_credentials_from_binary(config)
