"""Command line interface for HyFI"""
import logging
import os

import hydra

from .env import HyfiConfig, __hydra_version_base__
from .main import HyFI, getLogger

logger = getLogger(__name__)


def cmd(**args):
    """Run the command defined in the config file"""
    HyFI.run(args)


def about(**args):
    """Print the about information"""
    cfg = HyfiConfig(**args)
    name = cfg.about.name
    print()
    for k, v in cfg.about.dict().items():
        print(f"{k:11} : {v}")
    print(f"\nExecute `{name} --help` to see what you can do with {name}")


@hydra.main(
    config_path="conf", config_name="config", version_base=__hydra_version_base__
)
def hydra_main(cfg) -> None:
    hyfi = HyfiConfig(**cfg)
    verbose = hyfi.verbose
    app_name = hyfi.about.name
    print_config = hyfi.print_config
    print_resolved_config = hyfi.print_resolved_config

    if verbose:
        print("## Command Line Interface for %s ##" % app_name)
    HyFI.initialize(cfg)

    if print_config:
        if print_resolved_config:
            logger.info("## hydra configuration resolved ##")
            HyFI.pprint(cfg)
        else:
            logger.info("## hydra configuration ##")
            print(HyFI.to_yaml(cfg))

    if verbose:
        logger.info(f"Hydra working directory : {os.getcwd()}")
        logger.info(f"Orig working directory  : {hydra.utils.get_original_cwd()}")

    HyFI.instantiate(cfg)

    HyFI.terminate()


if __name__ == "__main__":
    # hydra.initialize_config_module
    hydra_main()
