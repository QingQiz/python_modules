#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Parallel():
    def __init__(self, job=None, thead=True):
        import sys, functools

        if thead or sys.platform != 'linux':
            from multiprocessing.pool import ThreadPool as Pool
        else:
            from multiprocessing import Pool
        self.pool = functools.partial(Pool, job)

    def map(self, func, params):
        global worker

        def initializer(func):
            global _worker
            _worker = func

        def worker(arg):
            n = 3
            while n >= 0:
                try:
                    return _worker(*arg)
                except:
                    n -= 1

        with self.pool(initializer=initializer, initargs=(func,)) as p:
            return p.map(worker, params)


def init(job=None):
    '''Just for compatibility with past codes
    init :: Int -> (ParamList -> a) -> [ParamList] -> Bool -> [a]

    usage: for example:
        a = init(job=8)(lambda x: x + 1, [[i] for i in range(10)])
        print(a) # a will be [1,2,3,4,5,6,7,8,9,10]
    '''
    def run(target, params, thread=True):
        '''
        run :: (ParamList -> a) -> [ParamList] -> Bool -> [a]
        '''
        return Parallel(job, thread).map(target, params)
    return run


def parallel(params, job=None, thread=True):
    '''
    parallel :: Int -> [ParamList] -> Bool -> (ParamList -> a) -> [a]

    usage: for example:
        @parallel(params=[[i] for i in range(10)], job=8, thread=False)
        def f(x):
            return x + 1
        print(f) # f will be [1,2,3,4,5,6,7,8,9,10]
    '''
    return __import__('functools').partial(init(1), params=params, thread=thread)