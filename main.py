#!/usr/bin/python3

import os
import requests
import json
import random
import datetime
import smtplib
import configparser 
import email

file_path = os.path.dirname(__file__)
if file_path != "":
    os.chdir(file_path)

maincfg_filename='main.cfg'
config = configparser.ConfigParser()
if not os.path.exists(maincfg_filename):
	print('Main configuration file not found: {name}.\nPlease copy {name}.dist and edit'.format(name=maincfg_filename))
	sys.exit(1)
config.read(maincfg_filename)

auth_token=config['rhodecode']['auth_token']
url=config['rhodecode']['url']
base_url=url.split("_admin")[0]
numhistory=config.getint('rhodecode','number_of_commits', fallback=20)

do_email=config.getboolean('main', 'email', fallback=False)
if do_email:
	mail_from=config['email']['from']
	mail_to=config['email']['to']
	mail_host=config['email']['host']
	mail_subject=config['email']['subject']
	dateformat=config['email']['dateformat']

do_repotrack=config.getboolean('main','repotrack',fallback=False)
if do_repotrack and os.path.exists('repositories.txt'):
	oldrepositories=open('repositories.txt', 'r').readlines()
	oldrepositories=[x for x in oldrepositories if x.strip() != ""]
else:
	oldrepositories=[]

header_template="""Hello, here are the commits for {date}
{body}
"""
commit_format="""\n#{short_id} {author} : {message}\n{long_url}"""

id_ = random.randint(0,2**32)

def make_request(method, **args):
	global id_
	payload = {'id': id_, 'auth_token': auth_token, 'args': '{}'}
	payload['method'] = method
	payload['args'] = args
	req = requests.post(url, json=payload)
	result = req.json()
	if result["id"] != id_:
		raise Exception("Id mismatch (got {}, expected {})".format(result["id"], id_))
	id_ += 1
	return result["result"]

def get_rh_date(date):
	return datetime.datetime.strptime(date.split(".")[0], "%Y-%m-%dT%H:%M:%S")

initialdate = datetime.datetime.utcnow() + datetime.timedelta(days=-1)
print("Getting repositories...")
repositories = make_request("get_repos")
print("Got {} repositories".format(len(repositories)))
commitbody = ["Fetched {} repositories".format(len(repositories))]
if do_repotrack:
	reponames=[repository['repo_name'] for repository in repositories]
	newrepositories = [repository for repository in reponames if repository not in oldrepositories]
	if len(newrepositories) != 0:
		commitbody.append("New repositories:")
		commitbody.append("\n".join(newrepositories))
	open('repositories.txt', 'w').write('\n'.join(reponames))
for repository in repositories:
	name, type_, repid, rev = repository["repo_name"], repository["repo_type"], repository["repo_id"], repository["last_changeset"]["revision"]
	if rev >= 0:
		latest = get_rh_date(repository["last_changeset"]["date"])
		if latest >= initialdate:
			repoline = "\n\nLatest commits for {name} (type: {type}, id: {id})".format(name=name, type=type_, id=repid)
			print('Getting commits for {} (type: {}, id {})'.format(name, type_, repid))
			commitbody.append(repoline)
			start_rev = max(0, rev-numhistory+1)
			changes = make_request("get_repo_changesets", repoid=repid, details="basic", start_rev=str(start_rev), limit=numhistory)
			for change in changes:
				change_date =  get_rh_date(change["date"])
				if change_date > initialdate:
					change['long_url'] = '{base_url}{name}/changeset/{id}'.format(base_url=base_url, name=name, id=change['raw_id'])
					commitbody.append(commit_format.format(**change))

datenow = datetime.datetime.now().strftime(dateformat)
fulltxt = header_template.format(date=datenow, body='\n'.join(commitbody))

if do_email:
	server=smtplib.SMTP('localhost')
	message=email.message.EmailMessage()
	message['Subject'] = mail_subject.format(date=datenow)
	essage['From'] = mail_from
	message['To'] = mail_to
	message.set_content(fulltxt)
	server.send_message(message, mail_from, mail_to)
else:
	print(fulltxt)

print("All done.")

sys.exit(0)