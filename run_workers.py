import subprocess as sp
import select
import sys


def run_workers(number_of_workers):
    """
    Run a bunch of rq workers on the default queue and read their output.
    We use 'select' to get output as it occurs
    """

    procs = [sp.Popen(["rq", "worker"], stdout=sp.PIPE) for i in range(number_of_workers)]

    fds = [proc.stdout for proc in procs]
    fds.append(sys.stdin)

    fd_to_worker_number = { proc.stdout: idx for idx, proc in enumerate(procs)}
    proc_to_worker_number = { proc: idx for idx, proc in enumerate(procs)}

    try:
        quit = False
        while not quit:
            rds, _, _ = select.select(fds, [], [])
            for rd in rds:
                if rd == sys.stdin:
                    line = sys.stdin.readline()
                    if 'quit' in line:
                        quit = True
                else:
                    print(f"WORKER {fd_to_worker_number[rd]} :", rd.readline())
    finally:
        print("WAITING FOR WOKERS TO TERMINATE")
        for proc in procs:
            print(f"Terminating {proc_to_worker_number[proc]}")
            proc.terminate()
        for proc in procs:
            print(f"Waiting for {proc_to_worker_number[proc]}")
            proc.wait()



if __name__ == '__main__':
    run_workers(int(sys.argv[1]))
