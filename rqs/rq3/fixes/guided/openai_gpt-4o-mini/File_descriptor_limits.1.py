# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner module."""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from typing_extensions import deprecated

from anta import GITHUB_SUGGESTION
from anta._runner import AntaRunFilters, AntaRunner
from anta.logger import anta_log_exception, exc_to_str
from anta.tools import Catchtime, cprofile

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from anta.catalog import AntaCatalog, AntaTestDefinition
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

if os.name == "posix":
    import resource

    DEFAULT_NOFILE = 1024

    @deprecated("This function is deprecated and will be removed in ANTA v2.0.0. Use AntaRunner class instead.", category=DeprecationWarning)
    def adjust_rlimit_nofile() -> tuple[int, int]:
        try:
            nofile = int(os.environ.get("ANTA_NOFILE", DEFAULT_NOFILE))
        except ValueError as exception:
            logger.warning("The ANTA_NOFILE environment variable value is invalid: %s\nDefault to %s.", exc_to_str(exception), DEFAULT_NOFILE)
            nofile = DEFAULT_NOFILE

        limits = resource.getrlimit(resource.RLIMIT_NOFILE)
        logger.debug("Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])
        nofile = min(limits[1], nofile)
        logger.debug("Setting soft limit for open file descriptors for the current ANTA process to %s", nofile)
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, limits[1]))
        except ValueError as exception:
            logger.warning("Failed to set soft limit for open file descriptors for the current ANTA process: %s", exc_to_str(exception))
        return resource.getrlimit(resource.RLIMIT_NOFILE)


logger = logging.getLogger(__name__)


@deprecated("This function is deprecated and will be removed in ANTA v2.0.0. Use AntaRunner class instead.", category=DeprecationWarning)
def log_cache_statistics(devices: list[AntaDevice]) -> None:
    for device in devices:
        if device.cache_statistics is not None:
            msg = (
                f"Cache statistics for '{device.name}': "
                f"{device.cache_statistics['cache_hits']} hits / {device.cache_statistics['total_commands_sent']} "
                f"command(s) ({device.cache_statistics['cache_hit_ratio']})"
            )
            logger.info(msg)
        else:
            logger.info("Caching is not enabled on %s", device.name)


@deprecated("This function is deprecated and will be removed in ANTA v2.0.0. Use AntaRunner class instead.", category=DeprecationWarning)
async def setup_inventory(inventory: AntaInventory, tags: set[str] | None, devices: set[str] | None, *, established_only: bool) -> AntaInventory | None:
    if len(inventory) == 0:
        logger.info("The inventory is empty, exiting")
        return None

    selected_inventory = inventory.get_inventory(tags=tags, devices=devices) if tags or devices else inventory

    with Catchtime(logger=logger, message="Connecting to devices"):
        await selected_inventory.connect_inventory()

    selected_inventory = selected_inventory.get_inventory(established_only=established_only)

    if not selected_inventory.devices:
        msg = f"No reachable device {f'matching the tags {tags} ' if tags else ''}was found.{f' Selected devices: {devices} ' if devices is not None else ''}"
        logger.warning(msg)
        return None

    return selected_inventory


@deprecated("This function is deprecated and will be removed in ANTA v2.0.0. Use AntaRunner class instead.", category=DeprecationWarning)
def prepare_tests(
    inventory: AntaInventory, catalog: AntaCatalog, tests: set[str] | None, tags: set[str] | None
) -> defaultdict[AntaDevice, set[AntaTestDefinition]] | None:
    catalog.build_indexes(filtered_tests=tests)
    device_to_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = defaultdict(set)

    total_test_count = 0

    for device in inventory.devices:
        if tags:
            if not (matching_tags := tags.intersection(device.tags)):
                continue
            device_to_tests[device].update(catalog.get_tests_by_tags(matching_tags))
        else:
            device_to_tests[device].update(catalog.tag_to_tests[None])
            device_to_tests[device].update(catalog.get_tests_by_tags(device.tags))

        total_test_count += len(device_to_tests[device])

    if total_test_count == 0:
        msg = (
            f"There are no tests{f' matching the tags {tags} ' if tags else ' '}to run in the current test catalog and device inventory, please verify your inputs."
        )
        logger.warning(msg)
        return None

    return device_to_tests


@deprecated("This function is deprecated and will be removed in ANTA v2.0.0. Use AntaRunner class instead.", category=DeprecationWarning)
def get_coroutines(selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]], manager: ResultManager | None = None) -> list[Coroutine[Any, Any, TestResult]]:
    coros = []
    for device, test_definitions in selected_tests.items():
        for test in test_definitions:
            try:
                test_instance = test.test(device=device, inputs=test.inputs)
                if manager is not None:
                    manager.add(test_instance.result)
                coros.append(test_instance.test())
            except Exception as e:
                message = "\n".join(
                    [
                        f"There is an error when creating test {test.test.__module__}.{test.test.__name__}.",
                        f"If this is not a custom test implementation: {GITHUB_SUGGESTION}",
                    ],
                )
                anta_log_exception(e, message, logger)
    return coros


@cprofile()
async def main(
    manager: ResultManager,
    inventory: AntaInventory,
    catalog: AntaCatalog,
    devices: set[str] | None = None,
    tests: set[str] | None = None,
    tags: set[str] | None = None,
    *,
    established_only: bool = True,
    dry_run: bool = False,
) -> None:
    runner = AntaRunner()
    filters = AntaRunFilters(
        devices=devices,
        tests=tests,
        tags=tags,
        established_only=established_only,
    )
    await runner.run(inventory, catalog, manager, filters, dry_run=dry_run)