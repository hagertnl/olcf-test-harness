#! /usr/bin/env python3

import time
import datetime
import collections
import queue
from types import *

from libraries import apptest
from fundamental_types.rgt_state import RgtState
from libraries import application_test_dictionary

#
# Author: Arnold Tharrington (arnoldt@ornl.gov)
# National Center for Computational Sciences, Scientific Computing Group.
# Oak Ridge National Laboratory
#

class Harness:

    #These strings define the tasks that the tests can do.
    checkout = "check_out_tests"
    starttest = "start_tests"
    stoptest = "stop_tests"
    displaystatus = "display_status"
    summarize_results = "summarize_results"
    status_file = "applications_status.txt"

    # Defines the harness log file name.
    LOG_FILE_NAME = "harness_log_file.txt"
    
    def __init__(self,
                 rgt_input_file,
                 concurrency):
        self.__tests = rgt_input_file.get_tests()
        self.__tasks = rgt_input_file.get_harness_tasks()
        self.__local_path_to_tests = rgt_input_file.get_local_path_to_tests()
        self.__appsubtest = []
        self.__concurrency = concurrency
        mycomputer_with_events_record = None

    def run_me_serial(self):
        apptest_queue = queue.Queue()
        # Mark status as tasks not completed.
        self.__returnState = RgtState.ALL_TASKS_NOT_COMPLETED

        my_tests = self.__formListOfTests()

        ip = -1
        for application_test in my_tests:
            message = "Starting tasks for application {}.\n".format(application_test.ApplicationName)
            for test in application_test.Tests:
                my_application_name = test[0]
                my_subtest_name = test[1]
                self.__appsubtest  = self.__appsubtest + \
                                     [apptest.subtest(name_of_application=my_application_name,
                                                      name_of_subtest=my_subtest_name,
                                                      local_path_to_tests=self.__local_path_to_tests) ]
                apptest_queue.put(apptest.subtest(name_of_application=my_application_name,
                                                      name_of_subtest=my_subtest_name,
                                                      local_path_to_tests=self.__local_path_to_tests))
                
                ip += 1
                with open(Harness.LOG_FILE_NAME,"a") as out:
                    #app_test = self.__appsubtest[ip]
                    app_test = apptest_queue.get()
                    message = "Starting tasks for application {} test {} .\n".format(app_test.getNameOfApplication(),
                                                                                     app_test.getNameOfSubtest()) 
                    out.write(message)
                    app_test.doTasks(tasks=self.__tasks)

        # If we get to this point mark all task as completed.
        self.__returnState = RgtState.ALL_TASKS_COMPLETED
        return

    def run_me_concurrent(self):
        # Form a queue of the apps.
        
    
        return

    def getState(self):
        return self.__returnState

    # Private member functions
    def __formListOfTests(self):
        """ Returns a list with each element being of type 
            application_test_dictionary.ApplicationSubtestDictionary.
        """
        # Form a set of application names.
        my_set_of_application_names = set([])
        for test in self.__tests:
            name_of_application=test[0]
            if name_of_application not in my_set_of_application_names:
                my_set_of_application_names.add(name_of_application) 

        # Form a list of tests without the subtests, and keep
        # the sequence of the the application in a dictionary.
        ip = -1
        my_tests = []
        application_sequence_index = {}
        for application_name in my_set_of_application_names:
            ip += 1
            application_sequence_index[application_name] = ip
            my_tests.append(application_test_dictionary.ApplicationSubtestDictionary(application_name))

        # We now add the subtests for each appication.
        for test in self.__tests:
            name_of_application=test[0]
            name_of_subtest=test[1]
            index = application_sequence_index[name_of_application] 
            my_tests[index].addAppSubtest(name_of_application,
                                          name_of_subtest)
        return my_tests
    
    def __check_out_test(self,apptest1):
        # Check out the files.
        apptest1.check_out_test()

    def __start_test(self,apptest1):
        #Start the test.
        apptest1.start_test()

    def __stop_test(self,apptest1):
        #Stop the test.
        apptest1.stop_test()

    def __display_status(self,apptest1,taskwords,mycomputer_with_events_record):
        #Display the test status.
        print("In display_status")
        if mycomputer_with_events_record == None:
            apptest1.display_status()
        else:
            apptest1.display_status2(taskwords,mycomputer_with_events_record)

    def __summarize_results(self,taskwords,mycomputer_with_events_record):
        failed_list = []
        inconclusive_list = []
        results = {"Test_has_at_least_1_pass" : 0,
                   "Number_attemps" : 0,
                   "Number_passed" : 0,
                   "Number_failed" : 0,
                   "Number_inconclusive" : 0,
                   "Failed_jobs" : [] ,
                   "Inconclusive_jobs" : []}

        #-----------------------------------------------------
        #                                                    -
        #                                                    -
        #-----------------------------------------------------
        tests_with_no_passes = []

        #-----------------------------------------------------
        # Generate a time stamp of the current time.         -
        #                                                    -
        #-----------------------------------------------------
        currenttime = time.localtime()
        timestamp = time.strftime("%Y%b%d_%H:%M:%S",currenttime)

        #-----------------------------------------------------
        # Generate the name of the logfile.                  -
        #                                                    -
        #-----------------------------------------------------
        logfile = Harness.status_file + "__" + str(timestamp)
        for appsubtest1 in self.__appsubtest:
            app_status = appsubtest1.generateReport(logfile,taskwords,mycomputer_with_events_record)

            if app_status["Number_passed"] == 0:
                tests_with_no_passes = tests_with_no_passes + [appsubtest1.name()]

            if app_status["Number_failed"] > 0:
                for tmpjob in app_status["Failed_jobs"]:
                    log_message = "Failed job: " + tmpjob
                    print(log_message)

            if app_status["Number_inconclusive"] > 0:
                for tmpjob in app_status["Inconclusive_jobs"]:
                    log_message = "Inconclusive job: " + tmpjob
                    print(log_message)


            for key in app_status.keys():
                results[key] = results[key] + app_status[key]

        dfile_obj = open(logfile,"a")
        dfile_obj.write("\n\n\nTest with 0 passes\n")
        dfile_obj.write("==================\n")
        for [application,subtest] in tests_with_no_passes:
            appname = "{app:20s} {test:20s}\n".format(app=application,test=subtest)
            dfile_obj.write(appname)

        dfile_obj.write("\n\n\nSummary\n")
        dfile_obj.write("==================\n")
        tmp_string = "Number of attempts = {attemps:10s}\n".format(attemps=str(results["Number_attemps"]))
        dfile_obj.write(tmp_string)
        tmp_string = "Number of passes = {passes:10s}\n".format(passes=str(results["Number_passed"]))
        dfile_obj.write(tmp_string)
        tmp_string = "Number of fails = {fails:10s}\n".format(fails=str(results["Number_failed"]))
        dfile_obj.write(tmp_string)
        tmp_string = "Number inconclusive = {inconclusive:10s}\n".format(inconclusive=str(results["Number_inconclusive"]))
        dfile_obj.write(tmp_string)

        dfile_obj.close()
