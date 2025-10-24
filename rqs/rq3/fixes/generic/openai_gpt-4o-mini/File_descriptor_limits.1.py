if os.name == "posix" or os.name == "nt":
    import resource

    DEFAULT_NOFILE = 16384

    @deprecated("This function is deprecated and will be removed in ANTA v2.0.0. Use AntaRunner class instead.", category=DeprecationWarning)
    def adjust_rlimit_nofile() -> tuple[int, int]:
        nofile = int(os.environ.get("ANTA_NOFILE", DEFAULT_NOFILE))

        limits = resource.getrlimit(resource.RLIMIT_NOFILE)
        logger.debug("Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])
        nofile = min(limits[1], nofile)
        logger.debug("Setting soft limit for open file descriptors for the current ANTA process to %s", nofile)
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, limits[1]))
        except ValueError as exception:
            logger.warning("Failed to set soft limit for open file descriptors for the current ANTA process: %s", exc_to_str(exception))
        return resource.getrlimit(resource.RLIMIT_NOFILE)