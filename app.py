import rq
from rq.job import Job
import redis
import random
import pendulum
import zlib



from simple_functions import *

r = redis.Redis()   # Just use defaults:

q = rq.Queue(connection=r)


# jobs = [q.enqueue(succeed) for _ in range(1000)]

def get_job_ids():
    return [id.split(b":")[2].decode('utf-8') for id in r.keys("rq:job:*")]

def get_jobs():
    job_ids = get_job_ids()
    return [Job.fetch(job_id, connection=r) for job_id in job_ids]

def get_job_info(job_id):
    job = Job.fetch(job_id, connection=r)
    print(dir(job))

#
# Metrics
#
def is_redis_running():
    try:
        r.ping()            # Check we're connected
        return True
    except:
        return False
def number_of_jobs(): return len(r.keys("rq:job:*"))
def number_of_workers(): return len(r.keys("rq:worker:*"))

def get_zset_length(name):
    return r.zcount(name,'-inf','+inf')
def failed_queue_length():
    return get_zset_length("rq:failed:default")
def work_queue_length():
    return r.llen("rq:queue:default")
def work_in_progress_length():
    return get_zset_length("rq:wip:default")
def redis_memory_usage():
    return r.memory_stats()['total.allocated']

#
# Summary data of each job
#

def safe_parse(value):
    try:
        return pendulum.parse(value)
    except:
        return None 

def get_job_data():
    jobs = get_jobs()

    def get_traceback(id):
        x = r.hget('rq:job:' + id, 'exc_info')
        if x:
            return zlib.decompress(x).decode('utf-8').strip()
        return x

    return [
            {
            "id": job.id,
            "status":job.get_status(),
            "result_ttl": job.get_result_ttl(),
            "ttl": r.ttl('rq:job:' + job.id),
            "started_at": safe_parse(r.hget("rq:job:" + job.id, 'started_at').decode('utf-8')),
            "ended_at": safe_parse(r.hget("rq:job:" + job.id, 'ended_at').decode('utf-8')),
            "created_at": safe_parse(r.hget("rq:job:" + job.id, 'created_at').decode('utf-8')),
            "args": str(job.args),
            "result": job.return_value,
            "call": job.get_call_string().split("(")[0].split(".")[-1],
            "memory_usage": r.memory_usage("rq:job:" + job.id),
            "traceback": get_traceback(job.id)
            }
        for job in jobs
    ]

def run_api():
    from flask import Flask, send_from_directory, jsonify, request
    import rq_dashboard
    app = Flask(__name__)
    app.config.from_object(rq_dashboard.default_settings)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

    #
    # Set up API
    #
    @app.route("/")
    @app.route("/index.html")
    def index(): return send_from_directory('static', 'index.html')
    @app.route("/jobs.html")
    def jobs(): return send_from_directory('static', 'jobs.html')


    #
    # Map metrics to api
    #
    @app.route("/metrics/is_redis_running")
    def _is_redis_running(): return jsonify(is_redis_running())
    @app.route("/metrics/number_of_jobs")
    def _number_of_jobs(): return jsonify(number_of_jobs())
    @app.route("/metrics/number_of_workers")
    def _number_of_workers(): return jsonify(number_of_workers())


    @app.route("/metrics/work_queue_length")
    def _work_queue_length(): return jsonify(work_queue_length())
    @app.route("/metrics/failed_queue_length")
    def _failed_queue_length(): return jsonify(failed_queue_length())
    @app.route("/metrics/redis_memory_usage")
    def _redis_memory_usage(): return jsonify(redis_memory_usage())


    @app.route("/jobs")
    def _get_job_data(): return jsonify(get_job_data())

    @app.route("/functions")
    def functions():
        return jsonify([
            "succeed",
            "fail",
            "sleep_then_fail",
            "sleep_then_succeed",
            "succeed_after_specified_time",
            "large_args_and_large_output",
            ])

    @app.route("/start_function", methods=["POST"])
    def start_function():
        payload = request.get_json() 
        count = payload["count"]
        function_name = payload["function_name"]

        if function_name == "fail":
            fn = fail
            getargs = lambda: ()
        elif function_name == "succeed":
            fn = succeed
            getargs = lambda: ()
        elif function_name == 'sleep_then_fail':
            fn = sleep_then_fail
            getargs = lambda: (random.randint(1,10), )
        elif function_name == 'sleep_then_succeed':
            fn = sleep_then_succeed
            getargs = lambda: (random.randint(1,10), )
        elif function_name == 'succeed_after_specified_time':
            fn = succeed_after_specified_time 
            getargs = lambda: ( datetime.now() + timedelta(seconds=random.randint(1,10)),)
        elif function_name == 'large_args_and_large_output':
            fn = large_args_and_large_output
            getargs = lambda: [random.randint(0,10000) for i in range(random.randint(20,100))]
        else:
            return "bad request", 400

        for i in range(int(count)):
            q.enqueue(fn, *getargs())

        return jsonify({})
  

    app.run(port=5001, debug=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'app':
        run_api()

