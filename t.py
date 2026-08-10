import os
import saythanks

is_test_run = 'TEST' in os.environ

if __name__ == '__main__' and not is_test_run:
    # When binding to 0.0.0.0, you accept incoming connections
    # from anywhere. During development, an application may have
    # security vulnerabilities making it susceptible to SQL injections
    # and other attacks. Therefore when the application is not ready
    # for production, accepting connections from anywhere can be
    # dangerous.
    # It is recommended to use 127.0.0.1 or local host during
    # development phase. This prevents others from targeting your
    # application and executing SQL injections against your project.

    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.bind(('127.0.0.1', 31137)) # Binding to local host
    # saythanks.app.run(host='127.0.0.1', port=5000)

    # This is the cleanest way to keep normal app logging 
    # while removing repeated GET / HTTP/1.1 entries.
    # Instead, went with the other approach of setting the werkzeug logger 
    # to INFO level in logging_config.py.
    # saythanks.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    saythanks.app.run(host='0.0.0.0', port=5000)
