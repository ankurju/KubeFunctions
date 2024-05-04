This is a simple Faas wrapper on Kubernetes where users can give a file containing function to be executed. 
So it includes function registration, trigger registration and trigger dispatch.
Functions submitted by the users are executed on kubernetes pods.
Django is used as backend to handle user requests.
Redis is used to enqeue the tasks and celery worker is used for processing the tasks
