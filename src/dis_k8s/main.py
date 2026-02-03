"""
Main entry point for DIS agent
"""

import os
import sys
import logging
import signal
import yaml
from pathlib import Path

from dis_k8s.orchestrator import DISOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = '/app/config/dis-config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return None
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None


def main():
    """Main entry point"""
    logger.info("Starting Digital Immune System (DIS) agent...")
    
    # Get node name from environment
    node_name = os.environ.get('NODE_NAME', 'default-node')
    logger.info(f"Node name: {node_name}")
    
    # Load configuration
    config = load_config()
    
    # Initialize orchestrator
    orchestrator = DISOrchestrator(node_name=node_name, config=config)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        orchestrator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for pre-trained models
    model_path = '/app/models'
    if Path(f"{model_path}/isolation_forest.pkl").exists():
        logger.info("Loading pre-trained models...")
        orchestrator.load_models(model_path)
    else:
        logger.info("No pre-trained models found, starting training phase...")
        training_duration = int(os.environ.get('TRAINING_DURATION', '300'))
        orchestrator.train_models(training_duration_seconds=training_duration)
        
        # Save trained models
        orchestrator.save_models(model_path)
    
    # Start the DIS system
    orchestrator.start()
    
    logger.info("DIS agent is running. Press Ctrl+C to stop.")
    
    # Keep running
    try:
        while True:
            signal.pause()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        orchestrator.stop()


if __name__ == '__main__':
    main()
