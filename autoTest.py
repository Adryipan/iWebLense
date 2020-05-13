import subprocess
import paramiko
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

threadNumber = [1,2, 4, 8, 16, 30]

def sshConnect(replicas):
    hostname = "115.146.87.78"
    username = "ubuntu"
    sshkey = paramiko.RSAKey.from_private_key_file("./sshPK")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    exitCode = 0
    try:
        # Connect to the server
        print("-------Connecting to the server via ssh------------")
        ssh.connect(hostname = hostname, username=username, pkey=sshkey)
        print("Connection successful")
        checkStatus = "kubectl get pods -o wide"
        stdin, stdout, stderr = ssh.exec_command(checkStatus)
        result = stdout.read().decode()
        result = result.split(" ")
        # Check the number of running pods
        runningPodNumber = 0
        for this in result:
            if this == "Running":
                runningPodNumber += 1
        if runningPodNumber != replicas:
            # Set corresponding replica
            print("Setting replicas to: " + str(replicas))
            scaleCommand = "kubectl scale deployment object-detection --replicas=" + str(replicas)
            stdin, stdout, stderr = ssh.exec_command(scaleCommand)
            err = stderr.read().decode()
            print("Command executed, waiting for changes to apply")
            # Pause for 10 sec to make sure changes is effective
            # Confirming the change is reflected on the server
            creating = 1
            while creating != 0:
                stdin, stdout, stderr = ssh.exec_command(checkStatus)
                result = stdout.read().decode().split(" ")
                creating = result.count("ContainerCreating")
                if creating != 0:
                    print("ContainerCreating status found. 2 sec waiting time will apply before checking again")
                    time.sleep(2)
            stdin, stdout, stderr = ssh.exec_command(checkStatus)
            result = stdout.read().decode()
            print("Current pods status:")
            print(result)
            # Check the number of running pods
            runningPodNumber = result.split(" ").count("Running")
            if err:
                print(err)
                exitCode = 2
            else:
                print("------Connection will now close.--------")
        else:
            # Check the number of running pods
            stdin, stdout, stderr = ssh.exec_command(checkStatus)
            err = stderr.read().decode()
            result = stdout.read().decode()
            print("Current pods status:")
            print(result)
            result = result.split(" ")
            runningPodNumber = result.count("Running")
            if err:
                print(err)
                exitCode = 2
            else:
                print("------Connection will now close.--------")
    except:
        print("[!] Cannot connect to the SSH Server")
        exitCode = -2
    finally:
        ssh.close()
        return runningPodNumber


def autoTest():
    results = []
    # Change the threadNumber each time
    for thisThread in threadNumber:
        print("Starting test on thread number of " + str(thisThread))
        tempResult = []
        # Change the replicas
        for i in range(3):
            # set up the number of replicas on the server
            print("Thread number of " + str(thisThread))
            print("Setting up replicas of " + str(i+1))
            podNumber = sshConnect(i+1)
            print("Checking number of replicas now: " + str(podNumber))
            print("Expected number of replicas now: " + str(i+1))
            restart = 0
            while podNumber != i+1:
                print("One or more replcias not setting up properly... Retrying in 5 second.....")
                restart += 1
                time.sleep(5)
                podNumber = sshConnect(i + 1)
                print("Checking number of replicas now: " + str(podNumber))
                print("Expected number of replicas now: " + str(i + 1))
            if restart > 10:
                print("Error setting up replicas detected more than 10 times. Server could be overloaded.")
                print("Experiment will continue. However, the result should be analysed cautiously.")
            print("------- Environment Ready ------")
            print("Thread number of " + str(thisThread))
            # run the command
            print("Getting result....")
            command = "python client/iWebLens_client.py client/inputfolder/ http://115.146.87.78/api/detect " + str(thisThread)
            p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
            output = p.stdout.read().decode().split("\n")
            resultTime = output[-2].split(" ")[-1]
            tempResult.append(resultTime)
            print("Result obtained")
            print("The average time for the current trial is: " + resultTime)
            print("--------------------\n")
        # Add the result for all three replica to the result list for all thread
        results.append(tempResult)
    return results

def plot(data):
    x = [1,2,3]
    markers = ['s', '^', 'P', 'D', '*', 'x']
    # convert the data into dataframe
    for i in range(len(data)):
        thisThreadSamele = list(np.array(map(float,data[i])).tolist())
        label = "Thread number of " + str(threadNumber[i])
        plt.plot(x,thisThreadSamele, label=label, marker=markers[i], markersize=6)

    plt.xticks(x)
    plt.legend()
    plt.title("Response time of iWebLens service in response to \nchange in the number of pods and threads")
    plt.xlabel("Number of replicas")
    plt.ylabel("Average response time (second)")
    plt.savefig('resultPlot1.png', bbox_inches='tight')


def logging(round, data):
    # Save result to a text file
    with open("ResultHistory", "a+") as f:
        f.write("Round " + round)
        for i in range(len(threadNumber)):
            f.write("Thread Number: " + str(threadNumber[i]) + ": " + ", ".join(map(str, data[i])) + "\n")

def main():
    with open("ResultHistory", "a+") as f:
        currentDT = datetime.now().strftime("%d/%m/%Y %H:%M")
        f.write("Date: " + currentDT + "\n")
    # Generate the result
    average = []
    for i in range(3):
        print("---------------Running trial " + str(i+1) + "--------------------")
        print("==================================================")
        if i == 0:
            average = autoTest()
            print("This is the first trial")
            print(average)
            print("Logging current round data")
            logging(str(i + 1), average)
            print("Logged")
        else:
            # Take average witht the new results
            result = autoTest()
            print(str(i+1) + " repeat")
            print(result)
            print("Logging current round data")
            print("logged")
            logging(str(i+1), result)
            temp = (np.asarray(average, dtype=float) + np.asarray(result, dtype=float)) / 2
            average = np.array(temp).tolist()
            print(average)
        print("===================================\n")
    plot(average)


if __name__ == "__main__":
    main()

