import logging
import os, json
from glob import glob
import importlib
from operator import itemgetter
from mqas import Queue
from pymongo import MongoClient


JOBS_CONNECTION = os.getenv('JOBS_CONNECTION', 'mongodb://localhost:27017')
JOBS_DBNAME = os.getenv('JOBS_DBNAME', 'jobs')
JOBS_COLNAME = os.getenv('JOBS_COLNAME', 'jobs')
DEFUALT_CHANNEL=os.getenv('DEFUALT_CHANNEL', 'default')
REGISTRY = os.getenv('REGISTRY', './registry')
SETTINGS = os.getenv('SETTINGS', os.path.join(os.getcwd(), "settings.json"))

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('service.log')
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

def load_config(names=[]):
    data = []
    for fn in glob(os.path.join(REGISTRY, "*" ,"settings.json")):
        with open(fn, 'r') as file:
            config = json.load(file)
            if isinstance(config, list):
                for c in config:
                    if ("jobName" in c) and ("worker" in c) and ("callback" in c):
                        jobname = c.get("jobName")
                        if not "sortPosition" in c:
                            c["sortPosition"] = 999
                        if names.count(jobname) > 0:
                            logger.error(f"Duplicate Job Name: {jobname}")
                            continue
                        if c.get("disabled", False):
                            continue
                        data.append(c)
                        names.append(jobname)

            if isinstance(config, dict):
                if ("jobName" in config) and ("worker" in config) and ("callback" in config):
                        jobname = config.get("jobName")
                        if not "sortPosition" in config:
                            config["sortPosition"] = 999

                        if names.count(jobname) > 0:
                            logger.error(f"Duplicate Job Name: {jobname}")
                            continue
                        if config.get("disabled", False):
                            continue
                        data.append(config)
                        names.append(jobname)

    return data

def load_system_config():
    data = {}
    with open(SETTINGS, 'r') as file:
        data = json.load(file)

    return data

def start_job(jobname, worker, kwargs, timeout='1h', channel=None, depends_on=None, client=None):
    kwargs["jobName"] = jobname

    if channel is None:
        channel = DEFUALT_CHANNEL

    try:
        if client is None:
            client = MongoClient(JOBS_CONNECTION)

        q = Queue(client, channel=channel, db_name=JOBS_DBNAME, col_name=JOBS_COLNAME)
        if depends_on is None:
            job = q.enqueue(worker, kwargs=kwargs, job_timeout=timeout, result_ttl=3600*24)
            return job
        else:
            job = q.enqueue(worker, kwargs=kwargs, job_timeout=timeout, depends_on=depends_on, result_ttl=3600*24)
            return job

    except Exception as ex:
        logger.error(f"Exception: {ex}")
        return None

def restructure_jobs(jobs):
    proc_jobs = []
    rem_jobs = jobs
    passed_jobs = []
    done = False

    while not done:
        jobs_avail = rem_jobs
        rem_jobs = []
        for j in jobs_avail:
            dps = j.get("dependsOn")
            if isinstance(dps, list):
                passed = True
                for dp in dps:
                    passed = passed and (proc_jobs.count(dp) > 0)

                if passed:
                    proc_jobs.append(j["jobName"])
                    passed_jobs.append(j)
                else:
                    rem_jobs.append(j)
            elif isinstance(dps, str):
                if proc_jobs.count(dps) > 0:
                    proc_jobs.append(j["jobName"])
                    passed_jobs.append(j)
                else:
                    rem_jobs.append(j)
            else:
                proc_jobs.append(j["jobName"])
                passed_jobs.append(j)

        if len(rem_jobs) == len(jobs_avail):
            done = True

    return passed_jobs

def process_final_jobs(jobs, headers, added_params, jobIds={}, dependsOn=[], client=None):
    if client is None:
        client = MongoClient(JOBS_CONNECTION)

    for job in jobs:
        depends_on = None
        kwargs = {"headers": headers, "added_params": added_params, "params": job.get("params")}

        j_depends = []
        if "dependsOn" in job:
            dps = job.get("dependsOn")
            if isinstance(dps, list):
                j_depends = dps
            elif isinstance(dps, str):
                j_depends.append(dps)

        j_depends = j_depends + dependsOn
        if (len(j_depends) > 0):
            depends_on = []
            for dp in j_depends:
                if dp in jobIds:
                    depends_on.append(jobIds[dp])

        try:
            j = start_job(jobname=job["jobName"], worker=job["worker"], kwargs=kwargs, timeout=job.get("timeout", "1h"), channel=job.get("channel"), depends_on=depends_on, client=client)
            jobIds[job["jobName"]] = j

        except Exception as ex:
            logger.error(f"Exception: {ex}")

    return jobIds

def check_jobs(jobs):
    data = []
    names = []
    for job in jobs:
        if ("jobName" in job) and ("worker" in job) and ("callback" in job):
            jobname = job.get("jobName")
            
            if not "sortPosition" in job:
                job["sortPosition"] = 1
            
            if names.count(jobname) > 0:
                logger.error(f"Duplicate Job Name: {jobname}")
                continue
            
            if job.get("disabled", False):
                continue

            data.append(job)
            names.append(jobname)
    return data, names

def check_callbacks(jobs, headers, params = {}):
    passed = []

    for config in jobs:
        if ("callback" in config) and ("worker" in config)  and ("jobName" in config):
            try:
                callback = config["callback"]
                mod_name, func_name = callback.rsplit(".", 1)
                mod = importlib.import_module(mod_name)
                func = getattr(mod, func_name)
                kwargs = {"jobName": config.get("jobName"), "headers": headers, "added_params": params, "params": config.get("params")}
                results = func(**kwargs)
                
                j_params = {}
                result = False

                if isinstance(results, list) or isinstance(results, tuple):
                    if len(results) > 0:
                        result = results[0]
                    if len(results) > 1:
                        if isinstance(results[1], dict):
                            j_params = results[1]
                else:
                    result = results


                if result:
                    params[config["jobName"]] = j_params
                    config["added_params"] = j_params
                    passed.append(config)

            except Exception as ex:
                logger.error(f"Exception: {config.get('jobName', '')}: {ex}")

        else:
            logger.error(f"Error in configuration: {json.dumps(config)}")
    return passed, params

def modify_tags(data, keys):

    def mod(tags):
        new_tags = {}
        for k in keys:
            if k in tags:
                new_tags[k] = tags[k]

        return new_tags
    
    if "tags" in data:
        data["tags"] = mod(data["tags"])
    
    if "studies" in data:
        for i in range(len(data["studies"])):
            if "tags" in data["studies"][i]:
                data["studies"][i]["tags"] = mod(data["studies"][i]["tags"])
            
            if "series" in data["studies"][i]:
                for j in range(len(data["studies"][i]["series"])):
                    if "tags" in data["studies"][i]["series"][j]:
                        data["studies"][i]["series"][j]["tags"] = mod(data["studies"][i]["series"][j]["tags"])

    return data

def process_main(data):
    settings = load_system_config()
    headers = modify_tags(data, settings.get("headerFields", []))

    preJobs, preJobNames = [[], []]
    postJobs, postJobNames = [[], []]

    if "preServices" in settings:
        preJobs, preJobNames = check_jobs(settings["preServices"])
        preJobs = sorted(preJobs, key=itemgetter("sortPosition"))

    if "postServices" in settings:
        postJobs, postJobNames = check_jobs(settings["postServices"])
        postJobs = sorted(postJobs, key=itemgetter("sortPosition"))

    configs = load_config(preJobNames + postJobNames)
    configs = sorted(configs, key=itemgetter("sortPosition"))


    preJobs, added_params = check_callbacks(preJobs, headers)
    configs, added_params = check_callbacks(configs, headers, added_params)
    postJobs, added_params = check_callbacks(postJobs, headers, added_params)
    
    preJobs = restructure_jobs(preJobs)
    jobs = restructure_jobs(configs)
    postJobs = restructure_jobs(postJobs)

    client = MongoClient(JOBS_CONNECTION)

    preJobIds = process_final_jobs(preJobs, headers, added_params, client=client)


    preJobNames = []

    for i in range(len(preJobs)):
        jobName = preJobs[i].get("jobName")
        if (not jobName is None) and (jobName in preJobIds):
            preJobNames.append(jobName)

    jobIds = process_final_jobs(jobs, headers, added_params, preJobIds, preJobNames, client=client)
    preJobIds.update(jobIds)
    
    for i in range(len(jobs)):
        jobName = jobs[i].get("jobName")
        if (not jobName is None) and (jobName in jobIds):
            preJobNames.append(jobName)

    process_final_jobs(postJobs, headers, added_params, preJobIds, preJobNames, client=client)