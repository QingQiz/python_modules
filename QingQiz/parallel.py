#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Parallel():
    def __init__(self, job=None, thead=True):
        import sys

        self.job = job

        if thead or sys.platform != 'linux':
            from multiprocessing.pool import ThreadPool as Pool
            self.pool = Pool(job) if job else Pool()
        else:
            from multiprocessing import Pool
            self.pool = Pool(job) if job else Pool()

    def mapN2N(self, funcs, params):
        def withRetry(func, arg, retryTimes=3):
            while retryTimes >= 0:
                try:
                    return func(*arg)
                except:
                    retryTimes -= 1

        def realExec(funcCallPair):
            return withRetry(*funcCallPair)

        execList = list(zip(funcs, params))

        if len(execList) <= 1 or self.job <= 1:
            return [realExec(i) for i in execList]

        return self.pool.map(realExec, execList)

    def map(self, func, params):
        return self.mapN2N([func] * len(params), params)


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