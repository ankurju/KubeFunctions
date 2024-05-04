from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os,subprocess
from celery.result import AsyncResult
from .models import Function
from .tasks import execute_function
import uuid
import time
import re
import matplotlib.pyplot as plt


def home(request):
    return render(request,'apis/register.html')

def register_function(request):
    if request.method == 'POST':
        function_name = request.POST.get('function_name')
        trigger_name = request.POST.get('trigger_name')
        function_file = request.FILES.get('file')

        if not function_name or not function_file or not trigger_name:
            error_message = 'Function name,Trigger name and file are required'
            return render(request, 'apis/home.html', {'error_message': error_message})

        # Check if a function with the same name already exists
        if Function.objects.filter(function_name=function_name).exists():
            error_message = 'Function with the same name already exists'
            return render(request, 'apis/home.html', {'error_message': error_message})
        
        # Check if a trigger with the same name already exists
        if Function.objects.filter(trigger_name=trigger_name).exists():
            error_message = 'Trigger with the same name already exists'
            return render(request, 'apis/home.html', {'error_message': error_message})

         # Create a folder for the function
        function_folder_path = os.path.join(settings.MEDIA_ROOT, function_name)
        os.makedirs(function_folder_path, exist_ok=True)

        # Save function file to the function folder
        fs = FileSystemStorage(location=function_folder_path)
        filename = fs.save(function_file.name, function_file)

        # Write Dockerfile
        dockerfile_content = f"""
            FROM python:3.9-slim
            COPY {filename} /{filename}
            CMD ["python", "./{filename}"]
        """
        dockerfile_path = os.path.join(function_folder_path, 'Dockerfile')
        with open(dockerfile_path, 'w') as dockerfile:
            dockerfile.write(dockerfile_content)


        # Build Docker image
        image_tag = f'karjank7/{function_name}:latest'
        subprocess.run(['docker', 'build', '-t', image_tag, '-f', dockerfile_path, function_folder_path])

        # Push Docker image to Docker Hub
        subprocess.run(['docker', 'push', image_tag])

        # Save function to the database
        Function.objects.create(function_name=function_name,trigger_name=trigger_name)

        success_message = f'Function {function_name} with trigger {trigger_name} registered successfully'
        return render(request, 'apis/register.html', {'success_message': success_message})

    return render(request, 'apis/register.html')


def trigger_dispatch(request):
    if request.method == 'POST':
        trigger_name = request.POST.get('trigger_name')

        if not trigger_name:
            error_message = 'Trigger name is required'
            return render(request, 'apis/home.html', {'error_message': error_message})

        # get function name corresponding to the trigger
        function_name = Function.objects.get(trigger_name=trigger_name).function_name
        unique_id = uuid.uuid4()
        job_name = f"{function_name}-{unique_id}"
        
        result = execute_function.delay(function_name,job_name)

        print("delay" , result)
        all_functions = Function.objects.all()
        return render(request, 'apis/dispatch.html', {'success_message': 'Trigger Dispatched','result':result,'all_functions':all_functions})
    else:
        all_functions = Function.objects.all()
        return render(request, 'apis/dispatch.html',{'all_functions':all_functions})

def load_test(request):
    if request.method == 'POST':
        plot_data={}
        function_name = 'f2'
        num_requests = 2
        while num_requests != 72:
            for i in range(1,num_requests+1):
                unique_id = uuid.uuid4()
                job_name = f"{function_name}-{unique_id}"
                execute_function.delay(function_name, job_name)

            succeeded_count = 0
            while succeeded_count != num_requests:
                with open('celery_logs.log', 'r') as file:
                    log_contents = file.read()                
                succeeded_count = log_contents.count("succeeded")

                # Sleep for a short interval before checking again
                time.sleep(1)
            
            if succeeded_count==num_requests:
                with open('celery_logs.log', 'r') as file:
                    log_lines = file.readlines()
                    data=0.0
                    for log_line in log_lines:
                        # Check if the line contains "succeeded"
                        if "succeeded" in log_line:
                            # Use regular expression to extract the time from the log line
                            match = re.search(r'succeeded in \d+\.\d+s: \'(?:\d+-)?(\d+\.\d+)\'', log_line)
                            if match:
                                # Extract the time from the matched group
                                execution_time = match.group(1)
                                data += float(execution_time)
                    data /= num_requests
                    plot_data[num_requests]=data
                    print('plot data ',plot_data)

            with open('celery_logs.log', 'w') as file:
                file.write('')
            num_requests += 2
        plot_response_time(plot_data)
        return render(request,'apis/loadtest.html')
    else:
        return render(request,'apis/loadtest.html')

def plot_response_time(plot_data):
    # Extract keys (number of requests) and values (average response time)
    requests = list(plot_data.keys())
    response_times = list(plot_data.values())

    # Create the plot
    plt.plot(requests, response_times, marker='o')

    # Add labels and title
    plt.xlabel('Number of Requests')
    plt.ylabel('Average Response Time')
    plt.title('Response Time vs. Number of Requests')

    # Show the plot
    plt.grid(True)
    plt.show()


def check_result(request,task_id):
    result = AsyncResult(task_id)
    return render(request,'apis/result.html',{'result':result})

# def load_test(request):

    