"""AWS Lambda handler for StartPage application.

This handler is invoked by AWS Lambda and runs the StartPage main function.
Environment variables are automatically loaded from Lambda configuration.
"""

import asyncio
import logging

from startpage.startpage import main

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """AWS Lambda handler function.

    Args:
        event: Lambda event object (unused in this scheduled function)
        context: Lambda context object providing runtime information

    Returns:
        dict: Response with statusCode and body

    Raises:
        Exception: If the StartPage main function fails
    """
    try:
        logger.info(f"Lambda function invoked. Request ID: {context.aws_request_id}")

        asyncio.run(main())

        logger.info("StartPage execution completed successfully")
        return {
            "statusCode": 200,
            "body": "StartPage updated successfully",
        }
    except Exception as e:
        logger.error(f"Error executing StartPage: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}",
        }
