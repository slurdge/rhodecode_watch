# Rhodecode watcher

This python script allows you to watch a rhodecode installation for commits.

By default, it will pull all the commits and changes from last day and package it as a report. Optionnaly, you can have the script to send you an email.

The easiest way to use it is to have a localhost sendmail or equivalent smtp server, and create a cronjob that calls the script.

