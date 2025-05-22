import logging
import sys
import inotify.adapters
import inotify.constants
import os # For checking path existence

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

_LOGGER = logging.getLogger(__name__)
STATSFILE = b'/proc/diskstats' # Define as a constant for clarity

def _configure_logging():
    _LOGGER.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)
    _LOGGER.addHandler(ch)

def _main():
    i = None  # Initialize i to None for the finally block
    try:
        _LOGGER.debug("Initializing Inotify adapter.")
        i = inotify.adapters.Inotify()
        _LOGGER.info("Inotify adapter initialized successfully.")
    except Exception as e:
        # Inotify adapter initialization is critical for the script's core functionality.
        # Recovery: Log a critical error and exit if the adapter cannot be initialized,
        # as no file monitoring can occur.
        _LOGGER.critical("Failed to initialize Inotify adapter: %s", e, exc_info=True)
        sys.exit(1)

    # Check if STATSFILE exists and is accessible before adding watch.
    # This provides a more specific error message than relying solely on add_watch failure.
    if not os.path.exists(STATSFILE) or not os.access(STATSFILE, os.R_OK):
        _LOGGER.critical(
            "STATSFILE path '%s' does not exist or is not readable. Cannot establish watch.",
            STATSFILE.decode('utf-8')
        )
        # Recovery: Exit if the target path is invalid, as the script cannot monitor it.
        # No specific cleanup of 'i' is needed here if add_watch hasn't been called.
        sys.exit(1)

    try:
        _LOGGER.debug("Adding watch for path: %s", STATSFILE.decode('utf-8'))
        # Using a specific mask for modifications or close-after-write events,
        # relevant for /proc/diskstats which is updated by the kernel.
        mask = inotify.constants.IN_MODIFY | inotify.constants.IN_CLOSE_WRITE
        i.add_watch(STATSFILE, mask=mask)
        _LOGGER.info("Successfully added watch for %s with mask %s.", STATSFILE.decode('utf-8'), mask)
    except (inotify.calls.InotifyError, OSError, IOError) as e:
        # Adding a watch to STATSFILE is essential for monitoring.
        # Recovery: Log a critical error and exit if the watch cannot be added,
        # as the script's primary purpose is unachievable.
        _LOGGER.critical(
            "Failed to add watch for path '%s': %s",
            STATSFILE.decode('utf-8'), e, exc_info=True
        )
        # The Inotify object 'i' might hold resources (e.g., a file descriptor).
        # While Python's GC typically handles this, explicit cleanup is ideal if available.
        # However, inotify.adapters.Inotify doesn't offer a direct close() method.
        sys.exit(1)

    try:
        _LOGGER.info("Starting to listen for events on %s...", STATSFILE.decode('utf-8'))
        # Loop to generate and process inotify events.
        for event in i.event_gen(yield_nones=False):
            (header, type_names, watch_path, filename) = event
            _LOGGER.info("EVENT: WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                         "WATCH-PATH=[%s] FILENAME=[%s]",
                         header.wd, header.mask, header.cookie, header.len, type_names,
                         watch_path.decode('utf-8'), filename.decode('utf-8'))
            # Further event processing could be added here.

    except Exception as e: # Catching a broad exception for the event loop
        # Errors during event generation or processing might be transient or due to specific event data.
        # Recovery: Log the error and continue. This allows the script to attempt to process
        # subsequent events, maintaining uptime for monitoring if the issue is isolated.
        # However, if the inotify instance itself becomes invalid, this loop might continuously fail.
        _LOGGER.error("An error occurred during event generation or processing: %s", e, exc_info=True)
    finally:
        _LOGGER.info("Cleaning up watches.")
        if i is not None: # Ensure 'i' (Inotify adapter) was initialized.
            try:
                _LOGGER.debug("Attempting to remove watch for %s", STATSFILE.decode('utf-8'))
                i.remove_watch(STATSFILE)
                _LOGGER.info("Successfully removed watch for %s", STATSFILE.decode('utf-8'))
            except (inotify.calls.InotifyError, OSError, IOError) as e:
                # Failure to remove a watch is logged but not treated as a critical error
                # preventing script termination. The OS will likely clean up on process exit.
                _LOGGER.error(
                    "Error removing watch for path '%s': %s",
                    STATSFILE.decode('utf-8'), e, exc_info=True
                )
            except Exception as e: # Catch any other unexpected error during remove_watch
                 _LOGGER.error(
                    "Unexpected error removing watch for path '%s': %s",
                    STATSFILE.decode('utf-8'), e, exc_info=True
                )

            # Handling the problematic /tmp watch removal.
            # This watch was present in the original code's finally block without a corresponding add_watch.
            # It will likely fail if /tmp was never added, but we handle the error gracefully.
            tmp_path_bytes = b'/tmp'
            try:
                _LOGGER.debug("Attempting to remove watch for %s (if it was added).", tmp_path_bytes.decode('utf-8'))
                i.remove_watch(tmp_path_bytes)
                _LOGGER.info("Successfully removed watch for %s (if it was present).", tmp_path_bytes.decode('utf-8'))
            except (inotify.calls.InotifyError, OSError, IOError) as e:
                # This error is expected if /tmp was not explicitly watched.
                # Recovery: Log as a warning, as it's not a failure of the script's main objective.
                # Not using exc_info=True as this is often an expected outcome.
                _LOGGER.warning(
                    "Could not remove watch for path '%s' (may not have been watched): %s",
                    tmp_path_bytes.decode('utf-8'), e
                )
            except Exception as e:
                # For any other unexpected error during /tmp watch removal.
                 _LOGGER.error(
                    "Unexpected error removing watch for path '%s': %s",
                    tmp_path_bytes.decode('utf-8'), e, exc_info=True
                )
        else:
            _LOGGER.info("Inotify adapter 'i' was not initialized, no watches to remove.")


if __name__ == '__main__':
    _configure_logging()
    _main()