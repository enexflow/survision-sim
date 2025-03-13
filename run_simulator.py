#!/usr/bin/env python3
"""
Entry point script for the Survision Device Simulator.
"""

import logging.config

from survision_simulator.main import main

if __name__ == "__main__":
    logging.config.fileConfig('logging.conf')
    main() 