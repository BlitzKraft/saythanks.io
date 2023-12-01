import os
import saythanks

is_test_run = 'TEST' in os.environ

if __name__ == '__main__' and not is_test_run:
    saythanks.app.run(host='0.0.0.0', port=5000)
