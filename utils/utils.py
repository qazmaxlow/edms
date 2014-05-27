import logging

class Utils:

	LOGGER_NAME = 'django.entrak_error'

	@staticmethod
	def log_exception(error):
		logger = logging.getLogger(Utils.LOGGER_NAME)
		logger.exception(error)

	@staticmethod
	def log_error(msg):
		logger = logging.getLogger(Utils.LOGGER_NAME)
		logger.error(msg)
