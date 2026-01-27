"""
Main entry point for E.V3 Background Service
"""

from service.core import EV3Service

if __name__ == "__main__":
    service = EV3Service()
    service.initialize()
    service.start()
