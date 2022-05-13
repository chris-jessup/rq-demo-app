from time import sleep
from datetime import datetime, timedelta

#
# Some silly functions to demonstrate how rq works
#

def fail():
    """Function that Always raises and Exception and records the time"""
    raise ValueError(f"That is outrageous! {datetime.now()=}")

def succeed():
    """Function that Always succeeds and returns the time"""
    return f"Hurray! {datetime.now()=}"

def sleep_then_fail(sleep_time):
    """Function that sleeps for a given time, then raises an error"""
    print(f"I'm going to sleep for {sleep_time=}, then raise an exception")
    sleep(sleep_time)
    raise ValueError(f"That is outrageous! I slept for {sleep_time=}")

def sleep_then_succeed(sleep_time):
    """Function that sleeps for a given time, then succeeds"""
    print(f"I'm going to sleep for {sleep_time=}, then succeed")
    sleep(sleep_time)
    return f"Hurray! I slept for {sleep_time=}"

def succeed_after_specified_time(specified_time):
    """
    Function that only succeeds if the current time is later than the specified time
    Allows to demonstrate re-running a job that failed
    """
    print(f"I'm only going to succeed after {specified_time}")

    if datetime.now() < specified_time:
        raise ValueError(f"NOOOOO! I'll only succeed after {specified_time}")
    return "Hurray!"

def large_args_and_large_output(*args):
    """
    A function that always succeeds, but produces
    output proportional to the number of args
    """
    return "\n".join([str(arg) for arg in args])

