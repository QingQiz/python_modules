#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pam

from getpass import getpass


def auth(retry=3):
    username = os.environ['USER']

    while retry:
        try:
            password = getpass(prompt=f'{username}\'s password: ')
            assert pam.pam().authenticate(username, password)
            return password, True
        except (KeyboardInterrupt, EOFError):
            print('abort')
            exit(0)
        except AssertionError:
            retry -= 1
    return '', False