from multiprocessing import Process
import logging

_logger = logging.getLogger(__name__)

def async(timeout=10, timeout_message='Async process took long enough', logger=_logger):
    def decorator(func):
        def asa(args, kwargs):
            def func_wrap(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.fatal('async function throws an exception', exc_info=True, extra={
                        'function': func,
                        'args': args,
                        'kwargs': kwargs,
                        'exception': e,
                    })

            process = Process(target=func_wrap, args=args, kwargs=kwargs)
            process.start()
            process.join(timeout)
            if process.is_alive():
                process.terminate()
                logger.error(timeout_message, exc_info=True, extra={
                    'function': func,
                    'args': args,
                    'kwargs': kwargs
                })

        def runner(*args, **kwargs):
            Process(target=asa, args=(args, kwargs)).start()

        return runner

    return decorator