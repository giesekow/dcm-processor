# DCM PROCESSOR
A dicom processing library setup with docker containers.

## DEPENDENCIES
1. Docker & Docker Compose

## Getting up and running
1. open the `.env` file with any text editor and set the `BASEDIR` variable to a folder which will be used as a base for mounting docker volumes.
2. build and pull docker images with `bash build.sh` [Run with `sudo` if needed].
3. run docker containers with `bash run.sh` [Run with `sudo` if needed].
4. initialize base services with `bash init.sh` [Run with `sudo` if needed].
Note: Its good to run the containers without `sudo`. This can be achieved by creating  the `docker` group is not already created and adding your user account to this group. `sudo groupadd docker && sudo usermod -aG docker $USER`

## Containers in this library
1. `orthanc`    : The orthanc server which servers as an intermedairy between dicom providers and our services.
2. `scheduler`  : The flask based service for scheduling jobs in our service registry.
3. `worker`     : A worker container which executes the scheduled tasks.
4. `dashboard`  : A dashboard for RQ workers. Which shows the state of scheduled jobs.


## Scaling up workers
You can scale the number of workers by passing the argument `--scale worker=N` to `run.sh` script, where `N` is the number of instances you want.


## Preparing your own service
A service consist of two parts.
1. An entry in the services `registry`.
2. An entry in the service `modules`.
Once you have prepare your entries you can use the `service.sh` script to install your service.

### Service entry in the `registry`
A service entry in the `registry` is basically a folder which contains a `settings.json` file and a python file.
The json file defines the job associated with the service and the python file provides a callback function whose return value determines when a job is to be run.
- The `settings.json` file can either be an object or an array of objects with the following fields:
    * `jobName` :  [string,required] the name of the job, this should be unique from other service jobs.
    * `worker` : [string,required] name of the function to be run as the worker, this should be a full function name. (see section below for details.).
    * `callback` : [string,required] name of the function which determines if a job should be scheduled for the current dicom processing or not. (see section below for details).
    * `dependsOn` : [string/list,optional] name(s) of jobs which the current service job depends on. this will make sure that those jobs run successfully before this job runs.
    * `priority` : [string,optional] the priority level assigned to this job. if not specified a default priority is assigned.
    * `timeout` : [string/number,optional] the RQ queuing timeout default is 1 hour.
    * `params`: [object,optional] this is an object with additional parameters that will be sent to the worker function.
    * `sortPosition` : [number,optional] this is a sorting variable which is used to sort the order in which jobs are scheduled (Note: independent jobs are however scheduled before dependent jobs).
    * `description` : [string,optional] this is a description for this current job. Its not used in any operation but only for third parties to have an idea what your service does.

- The python file should contain the `callback` function(s) you stated in the `settings.json` file
- For an example check the `temp` service folder in the `services` folder.

### Service entry in the `modules`
- A service entry in the `modules` is basically a folder which contains at least a python file with the `worker` function definition and other python files and any other file needed to run the worker function.
- This should usually be prepared as a python module.
- Module dependencies should be added using a `requirements.txt` in the same folder.
- A special shell script `script.sh` can also be added to the same folder which will be run by the worker container.

For an example of the service entry in the `modules` directory see the `temp` service in the `services` folder.


### The callback function
A `callback` function takes the following arguments
   - `jobName`   : The name of the job.
   - `headers`   : The selected fields in the dicom header.
   - `params`    : The params object from the `settings.json`.
   - `added_params`: This is a dictionary of `injected` params from other jobs.
   - `**kwargs`  : We recommend you add this to the list of arguments to capture all other params that may be passed.

Note:
1. Arguments are passed by name which means `exact names` should be used and position is NOT important.
2. The callback function should return `True` if the job should be processed for the current dicom or `False` otherwise.
3. It can also return a dictionary in addition to the `True/False` which will be sent to other `callbacks` and `worker` functions as `added_params`.
4. The callback function should NOT be used to perform time intensive tasks. The actual job should be handled in the `worker` function.


### The worker function
A `worker` function takes the following arguments
   - `jobName`   : The name of the job.
   - `headers`   : The selected fields in the dicom header.
   - `params`    : The params object from the `settings.json`.
   - `added_params`: This is a dictionary of `injected` params from other jobs. Provide the name of the service whos parameters you want to access as a key to the dictionary for e.g. `added_params[servicename][keyname]`.
   - `**kwargs`  : We recommend you add this to the list of arguments to capture all other params that may be passed.

Note:
1. Arguments are passed by name which means `exact names` should be used and position is NOT important.
2. The worker function is where all the processing takes place and thats the function that will be scheduled to be handled by the RQ workers.
3. The worker function should not return any value. [it can but will not be used for anything].


## The `service.sh` script.
This script can be used to `install`, `remove`, and `backup` services.
- An installable service should be a parent folder with two sub-folders:
    * `registry` : This contains the files which will go into the services registry
    * `module`  : This contains the module files which goes into the services modules
- To install a service run `bash service.sh install <servicename> -p <parentFolderPath>`
- To remove a service run `bash service.sh remove <servicename> -b <backupPath>` backup path is optional
- To backup a service run `bash service.sh backup <servicename> -b <backupPath>`

## Install the new service automatically.
To add the new service permanently to the workflow, append the service intallation command to the `init.sh` file.

## TO DOs
1. Support direct service installation from `git` source.
2. Support virtualenv based workers.
3. Create a CLI which can be installed with apt or npm or pip
